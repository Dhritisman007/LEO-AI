import json
import asyncio
# pyrefly: ignore [missing-import]
import google.generativeai as genai
from tools import TOOLS, TOOL_DESCRIPTIONS
from memory import (
    scratchpad_write, scratchpad_read, scratchpad_clear,
    remember_task, recall_similar_tasks
)
from agent import (
    SYSTEM_PROMPT, generate_plan, parse_tool_call,
    format_tool_descriptions, classify_failure, log
)
from context_engine import format_context_for_prompt
from checkpoints import save_checkpoint
from critic import critique_code, rewrite_code
from style_guides import detect_language_from_task, get_style_guide


async def run_agent_streaming(task: str, max_steps: int = 10, user_id: str = "anonymous"):
    """
    Same as run_agent but yields SSE events for each step
    so the frontend can render them in real time.
    """

    async def emit(event_type: str, data: dict):
        # EventSourceResponse automatically formats dictionaries to `data: ...\n\n`
        yield {"data": json.dumps({"type": event_type, **data})}
        await asyncio.sleep(0)  # yield control so FastAPI can flush

    scratchpad_clear(user_id)

    # Build workspace context — LEO reads the codebase before acting
    workspace_context = format_context_for_prompt(user_id)
    log(f"WORKSPACE CONTEXT BUILT (streaming): {len(workspace_context)} chars")

    # Emit plan first
    plan = generate_plan(task)
    async for chunk in emit("plan", {"plan": plan}):
        yield chunk

    past_memories = recall_similar_tasks(task, user_id=user_id, n=2)
    if past_memories:
        async for chunk in emit("memories", {"memories": past_memories}):
            yield chunk

    system = SYSTEM_PROMPT.format(tool_descriptions=format_tool_descriptions())
    lang = detect_language_from_task(task)
    if lang:
        guide = get_style_guide(lang)
        if guide:
            system += f"\n\n{guide}\n"

    plan_text = "\n".join(f"{p['id']}. {p['description']}" for p in plan)
    history = [
        f"SYSTEM: {system}",
        f"USER TASK: {task}",
        f"{workspace_context}",  # LEO sees the whole workspace
    ]
    if past_memories:
        memory_lines = [f"- Past task: \"{m.get('task')}\"" for m in past_memories]
        history.append("RELEVANT PAST EXPERIENCE:\n" + "\n".join(memory_lines))
    history.append(f"YOUR PLAN:\n{plan_text}\n(Execute one step at a time.)")

    model = genai.GenerativeModel("gemini-flash-lite-latest", generation_config={"temperature": 0.3})
    last_tool_signature = None
    repeat_count = 0
    current_plan_idx = 0
    step_failure_counts = {}
    step_history = []  # lightweight tracker for pre-tool reasoning
    steps = []  # full steps tracker for checkpointing
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

            # NEW — self-improvement critic pass
            last_code = None
            last_filename = None
            last_output = ""

            for s in reversed(steps):
                if s.get("type") == "tool_call":
                    if s.get("tool") == "run_code" and not last_output:
                        result = s.get("result", {})
                        last_output = result.get("stdout", "") + result.get("stderr", "")
                    if s.get("tool") in ("write_file", "run_code") and not last_code:
                        params = s.get("params", {})
                        if "code" in params:
                            last_code = params["code"]
                            last_filename = params.get("filename", "code")
                        elif "content" in params:
                            last_code = params["content"]
                            last_filename = params.get("filename", "code")
                    if last_code and last_output:
                        break

            critique = None
            if last_code:
                log("CRITIC: Reviewing LEO's output...")
                critique = critique_code(task, last_code, last_output)
                log(f"CRITIC RESULT: score={critique.get('score')} rewrite={critique.get('rewrite_needed')}")

                if critique.get("rewrite_needed") and critique.get("score", 10) < 6:
                    log("CRITIC: Rewriting code due to low score...")
                    improved_code = rewrite_code(
                        last_code,
                        critique.get("issues", []),
                        critique.get("improvements", [])
                    )
                    if last_filename and improved_code != last_code:
                        from tools.file_tools import write_file
                        write_file(last_filename, improved_code, user_id)
                        final_answer += f"\n\n(LEO self-improved this code — {len(critique.get('issues', []))} issue(s) fixed)"
                        log("CRITIC: Rewrite saved successfully")

            async for chunk in emit("done", {"content": final_answer, "plan": plan, "critique": critique}):
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
            # NEW — quick sanity check on tool selection
            if tool_name == "read_file" and any(
                s.get("tool") == "write_file" and s.get("params", {}).get("filename") == params.get("filename")
                for s in step_history[-3:]
            ):
                log(f"TOOL SKIP: Skipping read_file for {params.get('filename')} — just wrote it")
                history.append(
                    f"SYSTEM NOTE: You just wrote {params.get('filename')} — no need to read it back. Continue with the next step."
                )
                async for chunk in emit("thought", {"step": step + 1, "content": f"Skipped unnecessary read_file for {params.get('filename')}"}):
                    yield chunk
                continue

            if tool_name == "web_search" and any(
                s.get("tool") == "web_search" and s.get("params", {}).get("query") == params.get("query")
                for s in step_history
            ):
                log(f"TOOL SKIP: Duplicate web_search for '{params.get('query')}'")
                history.append("SYSTEM NOTE: You already searched for this. Use the previous result.")
                continue

            signature = f"{tool_name}:{json.dumps(params, sort_keys=True)}"
            if signature == last_tool_signature:
                repeat_count += 1
            else:
                repeat_count = 0
            last_tool_signature = signature

            if repeat_count >= 2 or (repeat_count >= 1 and tool_name in ["run_code", "run_python", "run_shell"]):
                final_answer = "ERROR: LEO got stuck in a loop."
                steps.append({"step": step + 1, "type": "error", "content": final_answer})
                async for chunk in emit("agent_error", {"content": final_answer, "plan": plan}):
                    yield chunk
                break

            # Track this tool call for future sanity checks
            step_history.append({"tool": tool_name, "params": params})
            steps.append({
                "step": step + 1,
                "type": "tool_call",
                "tool": tool_name,
                "params": params,
                "thought": leo_response,
                "plan_idx": current_plan_idx
            })

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
                    USER_SCOPED_TOOLS = [
                        "read_file",
                        "write_file",
                        "list_files",
                        "get_file_tree",
                        "get_file_content",
                    ]
                    if tool_name in USER_SCOPED_TOOLS:
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
                    steps[-1]["result"] = tool_result
                    if plan and current_plan_idx < len(plan):
                        plan[current_plan_idx]["status"] = "failed"
                    async for chunk in emit("agent_error", {"content": final_answer, "plan": plan}):
                        yield chunk
                    history.append(f"TOOL RESULT: {json.dumps(tool_result)}")
                    break

                steps[-1]["result"] = tool_result
                hint = {"transient": "Retry.", "bad_params": "Fix the parameters.", "general": "Adjust your approach."}.get(failure_type, "")
                history.append(f"TOOL RESULT: {json.dumps(tool_result)}\nHINT: {hint}")
            else:
                steps[-1]["result"] = tool_result
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
            steps.append({"step": step + 1, "type": "thought", "content": leo_response})
            async for chunk in emit("thought", {"step": step + 1, "content": leo_response}):
                yield chunk
            history.append("SYSTEM REMINDER: Use TOOL:/PARAMS: format or finish with DONE:/ERROR:")

    if not final_answer:
        checkpoint_id = save_checkpoint(user_id, task, history, steps, plan, current_plan_idx)
        final_answer = f"PAUSED: Max steps ({max_steps}) reached. Task can be resumed — checkpoint saved: {checkpoint_id}"
        async for chunk in emit("agent_error", {"content": final_answer, "plan": plan}):
            yield chunk

    was_successful = final_answer is not None and not final_answer.startswith("ERROR")
    remember_task(task, final_answer, was_successful, user_id)
