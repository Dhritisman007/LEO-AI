import json
import re
import time
# pyrefly: ignore [missing-import]
import google.generativeai as genai
from tools import TOOLS, TOOL_DESCRIPTIONS

# System prompt — tells LEO how to think and act
SYSTEM_PROMPT = """You are LEO, an autonomous AI coding agent. 🐐

You have access to the following tools:
{tool_descriptions}

To use a tool, respond with this exact format:
TOOL: tool_name
PARAMS: {{"param1": "value1", "param2": "value2"}}

Rules:
1. Think step by step before acting
2. Use one tool at a time
3. After seeing a tool result, decide your next action
4. When the task is fully complete, start your response with DONE:
5. If you cannot complete the task, start with ERROR: and explain why
6. Always write clean, working code
7. Never make up tool results — always actually use the tools

Example:
User: Write a Python script that prints numbers 1 to 10 and run it
You: I'll write the script first.
TOOL: write_file
PARAMS: {{"filename": "count.py", "content": "for i in range(1, 11):\\n    print(i)"}}
"""

def format_tool_descriptions() -> str:
    lines = []
    for tool in TOOL_DESCRIPTIONS:
        params = ", ".join(
            f"{k}: {v}" for k, v in tool["parameters"].items()
        )
        lines.append(f"- {tool['name']}: {tool['description']} | params: {params or 'none'}")
    return "\n".join(lines)


def parse_tool_call(text: str):
    """Extract tool name and params from LLM response."""
    try:
        tool_match = re.search(r"TOOL:\s*(\w+)", text)
        params_match = re.search(r"PARAMS:\s*(\{.*?\})", text, re.DOTALL)

        if not tool_match:
            return None, None

        tool_name = tool_match.group(1).strip()
        params = {}

        if params_match:
            params_str = params_match.group(1).strip()
            params = json.loads(params_str)

        return tool_name, params
    except Exception:
        return None, None


def run_agent(task: str, max_steps: int = 10) -> dict:
    """
    Main agent loop.
    Runs until task is done or max_steps reached.
    """
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

    for step in range(max_steps):
        # Rate limit: wait between API calls to stay under 5 req/min
        if step > 0:
            print("Waiting 15s for rate limit...")
            time.sleep(15)

        # Build prompt from history
        prompt = "\n\n".join(history) + "\n\nLEO:"

        # Ask Gemini what to do next (with retry on 429)
        model = genai.GenerativeModel("gemini-2.5-flash")
        for attempt in range(3):
            try:
                response = model.generate_content(prompt)
                leo_response = response.text.strip()
                break
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    wait = 30 * (attempt + 1)
                    print(f"Rate limited, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise

        print(f"\n--- Step {step + 1} ---")
        print(f"LEO: {leo_response}")

        # Add LEO's response to history
        history.append(f"LEO: {leo_response}")

        # Check if task is done
        if leo_response.startswith("DONE:"):
            final_answer = leo_response.replace("DONE:", "").strip()
            steps.append({
                "step": step + 1,
                "type": "done",
                "content": leo_response
            })
            break

        # Check if error
        if leo_response.startswith("ERROR:"):
            final_answer = leo_response
            steps.append({
                "step": step + 1,
                "type": "error",
                "content": leo_response
            })
            break

        # Check if LEO wants to use a tool
        tool_name, params = parse_tool_call(leo_response)

        if tool_name:
            steps.append({
                "step": step + 1,
                "type": "tool_call",
                "tool": tool_name,
                "params": params,
                "thought": leo_response
            })

            # Execute the tool
            if tool_name in TOOLS:
                print(f"Running tool: {tool_name} with {params}")
                tool_result = TOOLS[tool_name](**params)
            else:
                tool_result = {"success": False, "error": f"Tool '{tool_name}' not found"}

            print(f"Tool result: {tool_result}")

            # Add tool result to history so LEO can see it
            history.append(f"TOOL RESULT: {json.dumps(tool_result)}")

            steps[-1]["result"] = tool_result
        else:
            # LEO responded with text but no tool call — treat as thinking step
            steps.append({
                "step": step + 1,
                "type": "thought",
                "content": leo_response
            })

    # If max steps reached with no answer
    if not final_answer:
        final_answer = "Task incomplete — max steps reached."

    return {
        "task": task,
        "steps": steps,
        "final_answer": final_answer,
        "total_steps": len(steps)
    }
