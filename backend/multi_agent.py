import asyncio
import json
# pyrefly: ignore [missing-import]
import google.generativeai as genai
from tools import TOOLS
from agent import parse_tool_call, format_tool_descriptions, SYSTEM_PROMPT, log


ORCHESTRATOR_PROMPT = """You are LEO's orchestrator. Your job is to break a complex task into parallel subtasks that specialized agents can work on simultaneously.

Task: {task}

Current workspace context:
{context}

Break this into 2-4 independent subtasks that can run in parallel.
Respond with JSON ONLY:
{{
  "subtasks": [
    {{
      "id": "agent_1",
      "role": "what this agent specializes in",
      "task": "specific task for this agent",
      "depends_on": []
    }},
    {{
      "id": "agent_2",
      "role": "what this agent specializes in",
      "task": "specific task for this agent",
      "depends_on": ["agent_1"]
    }}
  ],
  "reasoning": "why you split it this way"
}}

Only split if the task genuinely benefits from parallelism.
If the task is simple and sequential, return a single subtask.
"""


async def run_sub_agent(
    agent_id: str,
    role: str,
    task: str,
    user_id: str,
    max_steps: int = 8
) -> dict:
    """Run a single sub-agent asynchronously."""
    log(f"SUB-AGENT [{agent_id}] starting: {role}")

    model = genai.GenerativeModel(
        "gemini-flash-lite-latest",
        generation_config={"temperature": 0.3}
    )

    system = SYSTEM_PROMPT.format(tool_descriptions=format_tool_descriptions())
    history = [
        f"SYSTEM: {system}",
        f"You are a specialized sub-agent. Your role: {role}",
        f"Your specific task: {task}"
    ]

    steps = []
    final_answer = None

    for step in range(max_steps):
        prompt = "\n\n".join(history) + "\n\nSUB-AGENT:"

        try:
            response = model.generate_content(prompt)
            leo_response = response.text.strip()
        except Exception as e:
            return {"agent_id": agent_id, "success": False, "error": str(e), "steps": steps}

        history.append(f"SUB-AGENT: {leo_response}")

        if leo_response.startswith("DONE:"):
            final_answer = leo_response.replace("DONE:", "").strip()
            steps.append({"step": step + 1, "type": "done", "content": leo_response})
            break

        if leo_response.startswith("ERROR:"):
            return {
                "agent_id": agent_id,
                "success": False,
                "error": leo_response,
                "steps": steps
            }

        tool_name, params = parse_tool_call(leo_response)

        if tool_name and tool_name in TOOLS:
            try:
                if tool_name in ["read_file", "write_file", "list_files", "get_file_tree", "get_file_content"]:
                    params["user_id"] = user_id
                tool_result = TOOLS[tool_name](**params)
            except Exception as e:
                tool_result = {"success": False, "error": str(e)}

            steps.append({
                "step": step + 1,
                "type": "tool_call",
                "tool": tool_name,
                "params": params,
                "result": tool_result,
            })
            history.append(f"TOOL RESULT: {json.dumps(tool_result)}")
        else:
            steps.append({"step": step + 1, "type": "thought", "content": leo_response})
            history.append("SYSTEM: Use TOOL:/PARAMS: format or finish with DONE:/ERROR:")

    log(f"SUB-AGENT [{agent_id}] finished: {final_answer or 'incomplete'}")
    return {
        "agent_id": agent_id,
        "role": role,
        "task": task,
        "success": final_answer is not None,
        "final_answer": final_answer or "Incomplete",
        "steps": steps,
    }


async def run_multi_agent(task: str, user_id: str, context: str = "") -> dict:
    """
    Orchestrate multiple sub-agents to complete a complex task in parallel.
    """
    log(f"ORCHESTRATOR: Planning subtasks for: {task}")

    # Step 1 — Ask orchestrator to plan subtasks
    model = genai.GenerativeModel(
        "gemini-flash-lite-latest",
        generation_config={
            "temperature": 0.2,
            "response_mime_type": "application/json"
        }
    )

    orchestrator_response = model.generate_content(
        ORCHESTRATOR_PROMPT.format(task=task, context=context[:2000])
    )

    try:
        plan = json.loads(orchestrator_response.text)
        subtasks = plan.get("subtasks", [])
        reasoning = plan.get("reasoning", "")
        log(f"ORCHESTRATOR: Split into {len(subtasks)} subtasks. Reasoning: {reasoning}")
    except Exception as e:
        log(f"ORCHESTRATOR: Failed to parse plan — {e}. Running as single agent.")
        subtasks = [{"id": "agent_1", "role": "general", "task": task, "depends_on": []}]

    # Step 2 — Run subtasks, respecting dependencies
    completed = {}
    all_steps = []

    # Group by dependency level
    remaining = subtasks.copy()
    iteration = 0

    while remaining and iteration < 5:
        iteration += 1
        # Find tasks whose dependencies are all complete
        ready = [
            t for t in remaining
            if all(dep in completed for dep in t.get("depends_on", []))
        ]

        if not ready:
            break

        # Run ready tasks in parallel
        log(f"ORCHESTRATOR: Running {len(ready)} tasks in parallel: {[t['id'] for t in ready]}")
        results = await asyncio.gather(*[
            run_sub_agent(t["id"], t["role"], t["task"], user_id)
            for t in ready
        ])

        for result in results:
            completed[result["agent_id"]] = result
            all_steps.extend(result.get("steps", []))
            remaining = [t for t in remaining if t["id"] != result["agent_id"]]

    # Step 3 — Synthesize results
    successful = [r for r in completed.values() if r.get("success")]
    failed = [r for r in completed.values() if not r.get("success")]

    synthesis_prompt = f"""You are LEO. Multiple sub-agents worked on parts of this task:

Original task: {task}

Sub-agent results:
{json.dumps([{"role": r["role"], "result": r.get("final_answer", "failed")} for r in completed.values()], indent=2)}

Write a brief synthesis explaining what was accomplished overall. Start with DONE:"""

    synthesis_response = model.generate_content(synthesis_prompt)
    final_answer = synthesis_response.text.strip().replace("DONE:", "").strip()

    return {
        "task": task,
        "subtasks": subtasks,
        "reasoning": reasoning,
        "agent_results": list(completed.values()),
        "steps": all_steps,
        "final_answer": final_answer,
        "agents_used": len(completed),
        "success_rate": f"{len(successful)}/{len(completed)}",
    }
