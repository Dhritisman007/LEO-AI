import json
import asyncio
import google.generativeai as genai
from tools import TOOLS, TOOL_DESCRIPTIONS
from memory import (
    scratchpad_write, scratchpad_clear,
    remember_task, recall_similar_tasks
)
from agent import (
    SYSTEM_PROMPT, generate_plan, parse_tool_call,
    format_tool_descriptions, classify_failure, log
)


async def run_agent_streaming(task: str, max_steps: int = 10, user_id: str = "anonymous"):
    """
    Same as run_agent but yields SSE events for each step
    so the frontend can render them in real time.
    """

    async def emit(event_type: str, data: dict):
        yield f"data: {json.dumps({'type': event_type, **data})}\n\n"
        await asyncio.sleep(0)  # yield control so FastAPI can flush

    scratchpad_clear(user_id)

    # Emit plan first
    plan = generate_plan(task)
    async for chunk in emit("plan", {"plan": plan}):
        yield chunk

    past_memories = recall_similar_tasks(task, user_id=user_id, n=2)
    if past_memories:
        async for chunk in emit("memories", {"memories": past_memories}):
            yield chunk

    system = SYSTEM_PROMPT.format(tool_descriptions=format_tool_descriptions())
    plan_text = "\n".join(f"{p['id']}. {p['description']}" for p in plan)
    history = [
        f"SYSTEM: {system}",
        f"USER TASK: {task}",
    ]
    if past_memories:
        memory_lines = [f"- Past task: \"{m.get('task')}\"" for m in past_memories]
        history.append("RELEVANT PAST EXPERIENCE:\n" + "\n".join(memory_lines))
    history.append(f"YOUR PLAN:\n{plan_text}\n(Execute one step at a time.)")

    model = genai.GenerativeModel("gemini-1.5-flash", generation_config={"temperature": 0.3})
    last_tool_signature = None
    repeat_count = 0
    current_plan_idx = 0
    step_failure_counts = {}
    final_answer = None

    if plan:
        plan[0]["status"] = "in_progress"
        async for chunk in emit("plan_update", {"plan": plan}):
            yield chunk

    for step in range(max_steps):
        prompt = "\n\n".join(history) + "\n\nLEO:"

        # Emit thinking indicator
        async for chunk in emit("thinking", {"step": step + 1}):
            yield chunk

        try:
            response = model.generate_content(prompt)
            leo_response = response.text.strip()
        except Exception as e:
            async for chunk in emit("error", {"content": f"API error: {str(e)}"}):
                yield chunk
            final_answer = f"ERROR: {str(e)}"
            break

        history.append(f"LEO: {leo_response}")

        if leo_response.startswith("DONE:"):
            final_answer = leo_response.replace("DONE:", "").strip()
            for p in plan:
                if p["status"] != "failed":
                    p["status"] = "done"
            async for chunk in emit("done", {"content": final_answer, "plan": plan}):
                yield chunk
            break

        if leo_response.startswith("ERROR:"):
            final_answer = leo_response
            if plan and current_plan_idx < len(plan):
                plan[current_plan_idx]["status"] = "failed"
            async for chunk in emit("agent_error", {"content": leo_response, "plan": plan}):
                yield chunk
            break

        tool_name, params = parse_tool_call(leo_response)

        if tool_name:
            signature = f"{tool_name}:{json.dumps(params, sort_keys=True)}"
            if signature == last_tool_signature:
                repeat_count += 1
            else:
                repeat_count = 0
            last_tool_signature = signature

            if repeat_count >= 2:
                final_answer = "ERROR: LEO got stuck in a loop."
                async for chunk in emit("agent_error", {"content": final_answer, "plan": plan}):
                    yield chunk
                break

            # Emit tool call start
            async for chunk in emit("tool_start", {
                "step": step + 1,
                "tool": tool_name,
                "params": params,
                "plan_idx": current_plan_idx
            }):
                yield chunk

            if tool_name in TOOLS:
                try:
                    if tool_name in ["read_file", "write_file", "list_files"]:
                        params["user_id"] = user_id
                    tool_result = TOOLS[tool_name](**params)
                except TypeError as e:
                    tool_result = {"success": False, "error": f"Bad parameters: {str(e)}"}
                except Exception as e:
                    tool_result = {"success": False, "error": str(e)}
            else:
                tool_result = {"success": False, "error": f"Tool '{tool_name}' not found"}

            # Emit tool result
            async for chunk in emit("tool_result", {
                "step": step + 1,
                "tool": tool_name,
                "result": tool_result
            }):
                yield chunk

            if not tool_result.get("success"):
                failure_type = classify_failure(tool_name, tool_result.get("error", ""))
                step_failure_counts[current_plan_idx] = step_failure_counts.get(current_plan_idx, 0) + 1
                scratchpad_write(f"Tool '{tool_name}' failed: {tool_result.get('error')}", user_id)

                if failure_type == "missing_capability" or step_failure_counts[current_plan_idx] >= 3:
                    final_answer = f"ERROR: Could not complete — {tool_result.get('error')}"
                    if plan and current_plan_idx < len(plan):
                        plan[current_plan_idx]["status"] = "failed"
                    async for chunk in emit("agent_error", {"content": final_answer, "plan": plan}):
                        yield chunk
                    history.append(f"TOOL RESULT: {json.dumps(tool_result)}")
                    break

                hint = {"transient": "Retry.", "bad_params": "Fix the parameters.", "general": "Adjust your approach."}.get(failure_type, "")
                history.append(f"TOOL RESULT: {json.dumps(tool_result)}\nHINT: {hint}")
            else:
                history.append(f"TOOL RESULT: {json.dumps(tool_result)}")

            if plan and current_plan_idx < len(plan):
                if tool_result.get("success"):
                    plan[current_plan_idx]["status"] = "done"
                    if current_plan_idx + 1 < len(plan):
                        current_plan_idx += 1
                        plan[current_plan_idx]["status"] = "in_progress"
                else:
                    plan[current_plan_idx]["status"] = "failed"

                async for chunk in emit("plan_update", {"plan": plan}):
                    yield chunk
        else:
            async for chunk in emit("thought", {"step": step + 1, "content": leo_response}):
                yield chunk
            history.append("SYSTEM REMINDER: Use TOOL:/PARAMS: format or finish with DONE:/ERROR:")

    if not final_answer:
        final_answer = "Task incomplete — max steps reached."
        async for chunk in emit("agent_error", {"content": final_answer, "plan": plan}):
            yield chunk

    was_successful = final_answer is not None and not final_answer.startswith("ERROR")
    remember_task(task, final_answer, was_successful, user_id)
