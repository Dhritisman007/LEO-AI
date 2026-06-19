import json
import re
import time
import os
# pyrefly: ignore [missing-import]
import google.generativeai as genai
from dotenv import load_dotenv
from tools import TOOLS, TOOL_DESCRIPTIONS

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
9. When writing Python code with newlines, use actual newlines in the JSON string, escaped as \\n
10. After running code, always report the output in your DONE: response
11. Do not explain what you "will do" in plain text without taking an action. Either call a tool or finish with DONE/ERROR.

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


def run_agent(task: str, max_steps: int = 10) -> dict:
    log(f"\n{'='*50}\nNEW TASK: {task}\n{'='*50}")

    system = SYSTEM_PROMPT.format(
        tool_descriptions=format_tool_descriptions()
    )

    # Conversation history
    history = [
        f"SYSTEM: {system}",
        f"USER TASK: {task}"
    ]

    steps = []
    final_answer = None

    model = genai.GenerativeModel(
        "gemini-flash-lite-latest",
        generation_config={"temperature": 0.3}
    )

    # Track repeated tool calls to detect loops
    last_tool_signature = None
    repeat_count = 0

    for step in range(max_steps):
        # Small delay between steps to be polite to the API
        if step > 0:
            time.sleep(2)

        # Build prompt from history
        prompt = "\n\n".join(history) + "\n\nLEO:"

        # Ask Gemini what to do next (with retry on 429)
        for attempt in range(3):
            try:
                response = model.generate_content(prompt)
                leo_response = response.text.strip()
                break
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    wait = 15 * (attempt + 1)
                    log(f"Rate limited, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    log(f"GEMINI API ERROR: {e}")
                    # Return error instead of crashing
                    return {
                        "task": task,
                        "steps": steps,
                        "final_answer": f"ERROR: API call failed — {str(e)}",
                        "total_steps": len(steps)
                    }

        log(f"\n--- Step {step + 1} ---\nLEO: {leo_response[:200]}...")

        # Add LEO's response to history
        history.append(f"LEO: {leo_response}")

        # Check if task is done or errored (search anywhere in response)
        completion_type, completion_content = check_completion(leo_response)

        if completion_type == "done":
            final_answer = completion_content
            steps.append({
                "step": step + 1,
                "type": "done",
                "content": completion_content
            })
            break

        if completion_type == "error":
            final_answer = completion_content
            steps.append({
                "step": step + 1,
                "type": "error",
                "content": completion_content
            })
            break

        # Check if LEO wants to use a tool
        tool_name, params = parse_tool_call(leo_response)

        if tool_name:
            # Loop detection — same tool + same params called twice in a row
            try:
                signature = f"{tool_name}:{json.dumps(params, sort_keys=True)}"
            except Exception:
                signature = f"{tool_name}:error_serializing_params"
                
            if signature == last_tool_signature:
                repeat_count += 1
            else:
                repeat_count = 0
            last_tool_signature = signature

            if repeat_count >= 2:
                log("LOOP DETECTED — same tool call repeated 3x, stopping")
                final_answer = "ERROR: LEO got stuck repeating the same action. Task stopped to prevent infinite loop."
                steps.append({"step": step + 1, "type": "error", "content": final_answer})
                break

            steps.append({
                "step": step + 1,
                "type": "tool_call",
                "tool": tool_name,
                "params": params,
                "thought": leo_response
            })

            # Execute the tool
            if tool_name in TOOLS:
                log(f"Running tool: {tool_name} with {params}")
                try:
                    tool_result = TOOLS[tool_name](**params)
                except TypeError as e:
                    tool_result = {"success": False, "error": f"Bad parameters: {str(e)}"}
                except Exception as e:
                    tool_result = {"success": False, "error": f"Tool execution failed: {str(e)}"}
            else:
                tool_result = {"success": False, "error": f"Tool '{tool_name}' not found. Available tools: {list(TOOLS.keys())}"}

            log(f"Tool result: {str(tool_result)[:200]}...")

            # Add tool result to history so LEO can see it
            history.append(f"TOOL RESULT: {json.dumps(tool_result)}")

            steps[-1]["result"] = tool_result
        else:
            # No tool call found — nudge LEO instead of silently continuing
            steps.append({
                "step": step + 1,
                "type": "thought",
                "content": leo_response
            })
            history.append(
                "SYSTEM REMINDER: You must either call a tool using the TOOL:/PARAMS: format, "
                "or finish with DONE: or ERROR:. Please continue."
            )

    # If max steps reached with no answer
    if not final_answer:
        final_answer = "Task incomplete — max steps reached."
        steps.append({"step": max_steps + 1, "type": "error", "content": final_answer})

    log(f"\nFINAL ANSWER: {final_answer}")

    return {
        "task": task,
        "steps": steps,
        "final_answer": final_answer,
        "total_steps": len(steps)
    }
