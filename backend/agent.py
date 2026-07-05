import json
import re
import time
import os
# pyrefly: ignore [missing-import]
import google.generativeai as genai
from dotenv import load_dotenv
from tools import TOOLS, TOOL_DESCRIPTIONS
from memory import (
    scratchpad_write, scratchpad_read, scratchpad_clear,
    remember_task, recall_similar_tasks
)

def classify_failure(tool_name: str, error: str) -> str:
    """Classify a tool failure to decide how to handle retry."""
    error_lower = error.lower()

    # Transient — worth an automatic retry
    transient_signals = ["timeout", "timed out", "connection", "temporarily", "rate limit"]
    if any(sig in error_lower for sig in transient_signals):
        return "transient"

    # Bad params — LEO should adjust its approach, not retry blindly
    param_signals = ["bad parameters", "missing", "required positional", "unexpected keyword"]
    if any(sig in error_lower for sig in param_signals):
        return "bad_params"

    # Missing capability — no tool can do this, stop wasting steps
    if tool_name == "not_found" or "not found" in error_lower and "file" not in error_lower:
        return "missing_capability"

    # Default — let LEO see it and decide (most code errors fall here)
    return "general"

# Ensure API key is configured even when imported standalone
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# System prompt — tells LEO how to think and act
SYSTEM_PROMPT = """You are LEO, an autonomous AI coding agent. 🐐

You have access to the following tools:
{tool_descriptions}

To use a tool, you MUST respond with EXACTLY this format (no extra text after PARAMS):
TOOL: tool_name
PARAMS: {{"param1": "value1", "param2": "value2"}}

Rules:
1. Think step by step before acting
2. Use one tool at a time — include only ONE TOOL: block per response
3. After seeing a tool result, decide your next action
4. When the task is fully complete, you MUST respond with DONE: followed by your final answer
5. If you are just answering a question, greeting, or chatting, respond with DONE: followed by your reply
6. If you cannot complete the task, respond with ERROR: followed by the reason
7. Always write clean, working code
8. Never make up tool results — always actually use the tools
9. For tasks that mention git, commits, branches, or pull requests: always create a branch FIRST (git_create_branch), then commit changes (git_commit_changes), then push (git_push_branch), then open the PR (git_open_pull_request) — in that exact order.
10. When writing Python code with newlines, use actual newlines in the JSON string, escaped as \\n
11. After running code, always report the output in your DONE: response
12. Do not explain what you "will do" in plain text without taking an action. Either call a tool or finish with DONE/ERROR.

Example multi-step task:
User: Write a Python script that prints numbers 1 to 5 and run it

LEO: I'll write the script first.
TOOL: write_file
PARAMS: {{"filename": "count.py", "content": "for i in range(1, 6):\\n    print(i)"}}

(after seeing tool result)

LEO: File written. Now I'll run it.
TOOL: run_shell
PARAMS: {{"command": "python3 /workspace/count.py"}}

(after seeing tool result)

LEO: DONE: I wrote count.py and ran it. The output was:
1
2
3
4
5

Example simple greeting:
User: hey

LEO: DONE: Hey there! 👋 I'm LEO, your AI coding agent. Give me a coding task and I'll handle it end-to-end — writing code, running it, and showing you the results! 🐐
"""

def format_tool_descriptions() -> str:
    lines = []
    for tool in TOOL_DESCRIPTIONS:
        params = ", ".join(
            f"{k}: {v}" for k, v in tool["parameters"].items()
        )
        lines.append(f"- {tool['name']}: {tool['description']} | params: {params or 'none'}")
    return "\n".join(lines)


LOG_FILE = "/tmp/leo_agent.log"

def log(message: str):
    with open(LOG_FILE, "a") as f:
        f.write(message + "\n")
    print(message)

def extract_json_object(text: str, start_pos: int) -> str | None:
    """Extract a JSON object from text starting at start_pos using brace counting."""
    if start_pos >= len(text) or text[start_pos] != '{':
        return None

    depth = 0
    in_string = False
    escape_next = False

    for i in range(start_pos, len(text)):
        char = text[i]

        if escape_next:
            escape_next = False
            continue

        if char == '\\' and in_string:
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                return text[start_pos:i + 1]

    return None


def parse_tool_call(text: str):
    """Extract tool name and params from LLM response."""
    try:
        tool_match = re.search(r"TOOL:\s*(\w+)", text)

        if not tool_match:
            return None, None

        tool_name = tool_match.group(1).strip()
        params = {}

        # Find PARAMS: and extract JSON using brace counting
        params_prefix = re.search(r"PARAMS:\s*", text)
        if params_prefix:
            json_start = params_prefix.end()
            # Find the opening brace
            while json_start < len(text) and text[json_start] != '{':
                json_start += 1
            if json_start < len(text):
                json_str = extract_json_object(text, json_start)
                if json_str:
                    json_str = json_str.replace("```json", "").replace("```", "").strip()
                    params = json.loads(json_str)

        return tool_name, params
    except Exception as e:
        log(f"PARSE ERROR: {e}")
        return None, None


def check_completion(text: str):
    """Check if LEO's response indicates completion or error.
    Returns (type, content) or (None, None) if not a completion.
    """
    # Check for DONE: anywhere in the response
    done_match = re.search(r"DONE:\s*(.*)", text, re.DOTALL)
    if done_match:
        return "done", done_match.group(1).strip()

    # Check for ERROR: anywhere in the response
    error_match = re.search(r"ERROR:\s*(.*)", text, re.DOTALL)
    if error_match:
        return "error", error_match.group(1).strip()

    return None, None


def generate_plan(task: str) -> list:
    """Ask Gemini to break the task into a numbered plan before acting."""
    planning_prompt = f"""You are LEO, an AI coding agent. Before doing anything, break this task into a short numbered plan.

Task: {task}

Respond ONLY with a numbered list of 2-6 concrete steps. No explanation, no extra text.
Example format:
1. Write the script
2. Run the script
3. Verify output

Now write the plan for the task above:"""

    model = genai.GenerativeModel(
        "gemini-flash-lite-latest",
        generation_config={"temperature": 0.3}
    )
    response = model.generate_content(planning_prompt)
    raw = response.text.strip()

    # Extract numbered lines like "1. Write the script"
    lines = re.findall(r"^\s*\d+[\.\)]\s*(.+)$", raw, re.MULTILINE)

    if not lines:
        # fallback — just split by newline if numbering parsing failed
        lines = [l.strip("- ").strip() for l in raw.split("\n") if l.strip()]

    plan = [
        {"id": i + 1, "description": desc.strip(), "status": "pending"}
        for i, desc in enumerate(lines)
    ]
    return plan

def run_agent(task: str, max_steps: int = 10, user_id: str = "anonymous") -> dict:
    log(f"\n{'='*50}\nNEW TASK [{user_id}]: {task}\n{'='*50}")

    scratchpad_clear(user_id)  # NEW — fresh scratchpad per task

    plan = generate_plan(task)
    log(f"PLAN: {json.dumps(plan, indent=2)}")

    # NEW — recall similar past tasks
    past_memories = recall_similar_tasks(task, user_id=user_id, n=2)
    memory_context = ""
    if past_memories:
        memory_lines = []
        for m in past_memories:
            outcome = "succeeded" if m.get("success") else "failed/incomplete"
            memory_lines.append(f"- Similar past task ({outcome}): \"{m.get('task')}\" → {m.get('final_answer', '')[:150]}")
        memory_context = "RELEVANT PAST EXPERIENCE:\n" + "\n".join(memory_lines)
        log(f"RECALLED MEMORIES:\n{memory_context}")

    system = SYSTEM_PROMPT.format(tool_descriptions=format_tool_descriptions())
    plan_text = "\n".join(f"{p['id']}. {p['description']}" for p in plan)

    history = [
        f"SYSTEM: {system}",
        f"USER TASK: {task}",
    ]
    if memory_context:
        history.append(memory_context)  # NEW — inject relevant past experience
    history.append(
        f"YOUR PLAN:\n{plan_text}\n(Follow this plan, but adapt if needed. Execute it one step at a time using tools.)"
    )

    steps = []
    final_answer = None
    model = genai.GenerativeModel("gemini-flash-lite-latest", generation_config={"temperature": 0.3})

    last_tool_signature = None
    repeat_count = 0
    current_plan_idx = 0  # which plan step we think we're on
    step_failure_counts = {}

    # Mark first plan step as in_progress
    if plan:
        plan[0]["status"] = "in_progress"

    for step in range(max_steps):
        prompt = "\n\n".join(history) + "\n\nLEO:"

        try:
            response = model.generate_content(prompt)
            leo_response = response.text.strip()
        except Exception as e:
            log(f"GEMINI API ERROR: {e}")
            steps.append({"step": step + 1, "type": "error", "content": f"API error: {str(e)}"})
            final_answer = f"ERROR: Gemini API call failed — {str(e)}"
            break

        log(f"\n--- Step {step + 1} ---\nLEO: {leo_response}")
        history.append(f"LEO: {leo_response}")

        if leo_response.startswith("DONE:"):
            final_answer = leo_response.replace("DONE:", "").strip()
            steps.append({"step": step + 1, "type": "done", "content": leo_response})
            # mark all remaining plan steps done
            for p in plan:
                if p["status"] != "failed":
                    p["status"] = "done"
            break

        if leo_response.startswith("ERROR:"):
            final_answer = leo_response
            steps.append({"step": step + 1, "type": "error", "content": leo_response})
            if plan and current_plan_idx < len(plan):
                plan[current_plan_idx]["status"] = "failed"
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
                log("LOOP DETECTED — stopping")
                final_answer = "ERROR: LEO got stuck repeating the same action. Task stopped."
                steps.append({"step": step + 1, "type": "error", "content": final_answer})
                if plan and current_plan_idx < len(plan):
                    plan[current_plan_idx]["status"] = "failed"
                break

            steps.append({
                "step": step + 1,
                "type": "tool_call",
                "tool": tool_name,
                "params": params,
                "thought": leo_response,
                "plan_idx": current_plan_idx
            })

            if tool_name in TOOLS:
                try:
                    # Inject user_id into file/workspace tools automatically
                    if tool_name in ["read_file", "write_file", "list_files", "run_python", "run_shell"]:
                        params["user_id"] = user_id
                        
                    log(f"Running tool: {tool_name} with {params}")
                    tool_result = TOOLS[tool_name](**params)
                except TypeError as e:
                    tool_result = {"success": False, "error": f"Bad parameters: {str(e)}"}
                except Exception as e:
                    tool_result = {"success": False, "error": str(e)}
            else:
                tool_result = {"success": False, "error": f"Tool '{tool_name}' not found"}

            log(f"Tool result: {tool_result}")

            # NEW — classify and track failures
            if not tool_result.get("success"):
                failure_type = classify_failure(tool_name, tool_result.get("error", ""))
                step_failure_counts[current_plan_idx] = step_failure_counts.get(current_plan_idx, 0) + 1
                scratchpad_write(f"Tool '{tool_name}' failed ({failure_type}) with params {params}: {tool_result.get('error')}", user_id=user_id)

                log(f"FAILURE CLASSIFIED AS: {failure_type} (attempt #{step_failure_counts[current_plan_idx]} on this plan step)")

                # Missing capability — stop wasting steps immediately
                if failure_type == "missing_capability":
                    final_answer = f"ERROR: LEO doesn't have a tool capable of this — {tool_result.get('error')}"
                    steps[-1]["result"] = tool_result
                    if plan and current_plan_idx < len(plan):
                        plan[current_plan_idx]["status"] = "failed"
                    history.append(f"TOOL RESULT: {json.dumps(tool_result)}")
                    break

                # Too many failures on the same plan step — escalate instead of looping forever
                if step_failure_counts[current_plan_idx] >= 3:
                    final_answer = (
                        f"ERROR: LEO tried {step_failure_counts[current_plan_idx]} times on "
                        f"'{plan[current_plan_idx]['description'] if plan else 'this step'}' and couldn't succeed. "
                        f"Last error: {tool_result.get('error')}"
                    )
                    steps[-1]["result"] = tool_result
                    if plan and current_plan_idx < len(plan):
                        plan[current_plan_idx]["status"] = "failed"
                    history.append(f"TOOL RESULT: {json.dumps(tool_result)}")
                    break

                # Give LEO a hint based on failure type, then let it try again
                hint = {
                    "transient": "This looked like a temporary issue. Try the same action again.",
                    "bad_params": "Check the parameter names and types match what the tool expects, then retry with corrected params.",
                    "general": "Read the error carefully and adjust your approach before retrying."
                }.get(failure_type, "")
                history.append(f"TOOL RESULT: {json.dumps(tool_result)}\nHINT: {hint}")
            else:
                history.append(f"TOOL RESULT: {json.dumps(tool_result)}")

            steps[-1]["result"] = tool_result

            if plan and current_plan_idx < len(plan):
                if tool_result.get("success"):
                    plan[current_plan_idx]["status"] = "done"
                    if current_plan_idx + 1 < len(plan):
                        current_plan_idx += 1
                        plan[current_plan_idx]["status"] = "in_progress"
                else:
                    plan[current_plan_idx]["status"] = "failed"
        else:
            steps.append({"step": step + 1, "type": "thought", "content": leo_response})
            history.append(
                "SYSTEM REMINDER: You must either call a tool using the TOOL:/PARAMS: format, "
                "or finish with DONE: or ERROR:. Please continue."
            )

    if not final_answer:
        final_answer = "Task incomplete — max steps reached without finishing."
        steps.append({"step": max_steps + 1, "type": "error", "content": final_answer})

    log(f"\nFINAL ANSWER: {final_answer}")
    log(f"FINAL PLAN STATE: {json.dumps(plan, indent=2)}")

    # NEW — store this task in long-term memory for future recall
    was_successful = final_answer is not None and not final_answer.startswith("ERROR")
    remember_task(task, final_answer, was_successful, user_id=user_id)

    return {
        "task": task,
        "plan": plan,
        "steps": steps,
        "final_answer": final_answer,
        "total_steps": len(steps),
        "scratchpad": scratchpad_read(user_id),       # NEW
        "recalled_memories": past_memories      # NEW
    }
