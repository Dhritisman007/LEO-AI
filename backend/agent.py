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
from context_engine import format_context_for_prompt
from checkpoints import save_checkpoint
from style_guides import get_style_guide, detect_language_from_task
from test_generator import generate_tests, get_test_filename
from static_analysis import run_analysis
from critic import pr_review, rewrite_code

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
SYSTEM_PROMPT = """You are LEO, an elite AI software engineer. 🐐
You write code at the level of a senior engineer with 10+ years of experience.

You have access to the following tools:
{tool_descriptions}

═══════════════════════════════════════
CODE QUALITY CONSTITUTION
═══════════════════════════════════════

Every piece of code you write MUST follow these non-negotiable standards:

── CORRECTNESS ─────────────────────────
- Solve the EXACT problem stated — re-read the task before writing
- Handle ALL edge cases: empty input, None/null, zero, negative numbers,
  empty lists, very large inputs, unicode strings
- Never assume input is valid — validate and raise clear errors
- Test mentally: "what happens if someone passes None here?"

── READABILITY ─────────────────────────
- Meaningful names: `calculate_compound_interest` not `calc` or `f`
- Functions do ONE thing — if you need "and" to describe it, split it
- Max 20 lines per function — longer means it needs decomposing
- No magic numbers: use named constants (`MAX_RETRIES = 3` not `3`)
- Blank lines between logical sections
- Consistent style throughout the file

── DOCUMENTATION ───────────────────────
- Every function gets a docstring explaining: what it does, args, returns, raises
- Complex logic gets inline comments explaining WHY not WHAT
- Module-level docstring explaining the file's purpose
- Include usage examples in docstrings for public functions

── ERROR HANDLING ──────────────────────
- Never silently swallow exceptions with bare `except: pass`
- Raise specific exceptions with descriptive messages
- Use try/except only where failure is expected and recoverable
- Always clean up resources (use context managers / with statements)
- Log errors with enough context to debug them

── STRUCTURE & REUSABILITY ─────────────
- Classes for things with state, functions for stateless operations
- Dependency injection over hardcoded values
- Configuration at the top of the file or in a config object
- Public interface clearly separated from implementation details
- No global mutable state

── PERFORMANCE ─────────────────────────
- Use appropriate data structures (dict for lookups, set for membership)
- Avoid O(n²) algorithms when O(n) or O(n log n) is possible
- Don't load entire files into memory when streaming works
- Cache expensive computations that are called repeatedly

── LANGUAGE-SPECIFIC RULES ─────────────
Python:  Type hints on all functions | f-strings not .format() |
         dataclasses/pydantic for data | pathlib not os.path |
         list comprehensions over map/filter | __all__ for modules

JavaScript/TS: const over let, never var | async/await not callbacks |
               destructuring | optional chaining (?.) | TypeScript types always

Java:    Follow Oracle naming conventions | interfaces over concrete types |
         Optional<T> instead of null returns | try-with-resources |
         Stream API for collections

C++:     RAII everywhere | smart pointers not raw | const correctness |
         std::string not char* | range-based for loops | nullptr not NULL

Go:      Errors as values, always check them | short variable names ok |
         defer for cleanup | interfaces for abstraction | table-driven tests

Rust:    Result<T,E> for fallible ops | no unwrap() in production |
         ownership semantics | derive common traits | descriptive error types

═══════════════════════════════════════
TOOL SELECTION RULES
═══════════════════════════════════════

- write_file: saving code/content to disk ONLY
- run_code: executing code — always specify language
- run_shell: shell commands that aren't running a code file
- read_file: verify contents ONLY when genuinely needed
- list_files: ONLY when you don't know what exists
- web_search: external info not in training data
- git_*: version control ops explicitly requested

NEVER inject user_id into run_shell, run_code, web_search, or git_* calls.
Only inject user_id into: read_file, write_file, list_files.

COMMON MISTAKES TO AVOID:
- Don't read_file immediately after write_file — you just wrote it
- Don't web_search for basic syntax you already know
- Don't repeat a failing tool call with identical params
- Don't call run_code on code you haven't written yet

═══════════════════════════════════════
TWO MODES
═══════════════════════════════════════

MODE 1 — DIRECT ANSWER
Simple factual questions → answer directly, start with DONE:

MODE 2 — AGENT (use tools)
Tasks needing code/files/execution → use tools one at a time

Format for tool use:
TOOL: tool_name
PARAMS: {{"param1": "value1"}}

Rules:
1. Simple questions → DONE: with direct answer
2. Before writing code — plan the structure in a thought step first
3. Write the COMPLETE implementation — never truncate with "# ... rest of code"
4. Use ONE tool at a time
5. When fully complete → DONE: with summary
6. If genuinely stuck → ERROR: with clear explanation
7. For Java: filename MUST match the public class name exactly
8. For git tasks: branch → commit → push → PR in that order
9. Run code after writing to verify it actually works
10. If code fails — READ the error, understand it, fix it properly
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
    """
    For simple questions, skip planning entirely.
    For real tasks, generate a step-by-step plan.
    """
    # Quick classifier — if it looks like a question, skip planning
    task_lower = task.strip().lower()
    question_signals = [
        "what is", "what are", "who is", "who are",
        "where is", "when is", "why is", "how does",
        "explain", "define", "tell me", "can you explain",
        "what does", "difference between", "meaning of"
    ]
    is_simple_question = any(task_lower.startswith(sig) for sig in question_signals) or (
        task_lower.endswith("?") and len(task.split()) < 12
    )

    if is_simple_question:
        return []  # No plan needed — LEO will answer directly

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
        generation_config={"temperature": 0.4}
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

def run_agent(
    task: str,
    max_steps: int = 10,
    user_id: str = "anonymous",
    checkpoint: dict = None  # NEW
) -> dict:
    log(f"\n{'='*50}\nNEW TASK [{user_id}]: {task}\n{'='*50}")

    # Resume from checkpoint if provided
    if checkpoint:
        log(f"RESUMING from checkpoint — {len(checkpoint['steps'])} steps already done")
        history = checkpoint["history"]
        steps = checkpoint["steps"]
        plan = checkpoint["plan"]
        current_plan_idx = checkpoint["current_plan_idx"]
        scratchpad_clear(user_id)
        
        # Build workspace context for the prompt
        workspace_context = format_context_for_prompt(user_id)
        
        # Recall similar past tasks (optional for resume, but good to have)
        past_memories = recall_similar_tasks(task, user_id=user_id, n=2)
        memory_context = ""
    else:
        # Normal fresh start
        scratchpad_clear(user_id)  # NEW — fresh scratchpad per task
    
        # Build workspace context — LEO reads the codebase before acting
        workspace_context = format_context_for_prompt(user_id)
        log(f"WORKSPACE CONTEXT BUILT: {len(workspace_context)} chars")
    
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
        
        # Detect language and inject style guide
        detected_language = detect_language_from_task(task)
        style_guide = get_style_guide(detected_language) if detected_language else ""
        if style_guide:
            log(f"STYLE GUIDE: Injecting {detected_language} quality standards")
    
        history = [
            f"SYSTEM: {system}",
            f"USER TASK: {task}",
            f"{workspace_context}",
        ]
        if style_guide:
            history.append(f"LANGUAGE QUALITY STANDARDS:\n{style_guide}")  # NEW
        if memory_context:
            history.append(memory_context)
        history.append(
            f"YOUR PLAN:\n{plan_text}\n(Execute one step at a time.)"
        )
    
        steps = []
        current_plan_idx = 0  # which plan step we think we're on

    final_answer = None
    model = genai.GenerativeModel("gemini-flash-lite-latest", generation_config={"temperature": 0.3})

    last_tool_signature = None
    repeat_count = 0
    step_failure_counts = {}

    # Mark first plan step as in_progress if starting fresh
    if not checkpoint:
        if plan:
            plan[0]["status"] = "in_progress"
        else:
            log("Simple question detected — skipping plan, answering directly")


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
            # NEW — quick sanity check on tool selection
            if tool_name == "read_file" and any(
                s.get("tool") == "write_file" and s.get("params", {}).get("filename") == params.get("filename")
                for s in steps[-3:]
            ):
                # LEO is trying to read a file it just wrote — skip it
                log(f"TOOL SKIP: Skipping read_file for {params.get('filename')} — just wrote it")
                history.append(
                    f"SYSTEM NOTE: You just wrote {params.get('filename')} — no need to read it back. Continue with the next step."
                )
                steps.append({
                    "step": step + 1,
                    "type": "thought",
                    "content": f"Skipped unnecessary read_file for {params.get('filename')}"
                })
                continue

            if tool_name == "web_search" and any(
                s.get("tool") == "web_search" and s.get("params", {}).get("query") == params.get("query")
                for s in steps
            ):
                # Same search called twice — skip it
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
                    USER_SCOPED_TOOLS = [
                        "read_file",
                        "write_file",
                        "list_files",
                        "get_file_tree",
                        "get_file_content",
                    ]
                    if tool_name in USER_SCOPED_TOOLS:
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
        # Save checkpoint so task can be resumed
        checkpoint_id = save_checkpoint(user_id, task, history, steps, plan, current_plan_idx)
        final_answer = f"PAUSED: Max steps ({max_steps}) reached. Task can be resumed — checkpoint saved: {checkpoint_id}"
        steps.append({
            "step": max_steps + 1,
            "type": "error",
            "content": final_answer,
            "checkpoint_id": checkpoint_id  # NEW
        })

    log(f"\nFINAL ANSWER: {final_answer}")
    log(f"FINAL PLAN STATE: {json.dumps(plan, indent=2)}")

    # NEW — store this task in long-term memory for future recall
    was_successful = final_answer is not None and not final_answer.startswith("ERROR")
    remember_task(task, final_answer, was_successful, user_id=user_id)

    # NEW — self-improvement critic pass
    # Find the last write_file + run_code pair
    last_code = None
    last_filename = None
    last_output = ""

    # Collect all files LEO wrote during this task
    files_written = []
    last_output = ""
    last_language = detected_language or "python"

    for s in steps:
        if s.get("type") == "tool_call":
            if s.get("tool") == "write_file":
                params = s.get("params", {})
                filename = params.get("filename", "")
                content = params.get("content", "")
                if filename and content:
                    files_written.append({"filename": filename, "content": content})
            if s.get("tool") == "run_code":
                result = s.get("result", {})
                last_output = result.get("stdout", "") + result.get("stderr", "")
                last_language = s.get("params", {}).get("language", last_language)

    # PR Review
    review = None
    if files_written and was_successful:
        log("PR REVIEW: Reviewing all produced files...")
        review = pr_review(task, files_written, last_output)
        log(f"PR REVIEW: score={review.get('score')} approve={review.get('approve')} rewrite={review.get('rewrite_needed')}")

        # Auto-rewrite if blocking issues found
        if review.get("rewrite_needed") and review.get("blocking_issues"):
            log(f"PR REVIEW: Rewriting due to {len(review['blocking_issues'])} blocking issues")
            for file_info in files_written:
                improved = rewrite_code(
                    file_info["content"],
                    review["blocking_issues"],
                    review.get("suggestions", [])
                )
                if improved != file_info["content"]:
                    from tools.file_tools import write_file
                    write_file(file_info["filename"], improved, user_id)
                    file_info["content"] = improved
                    log(f"PR REVIEW: Rewrote {file_info['filename']}")

        # Auto-generate tests if none exist
        has_tests = any(
            "test" in f["filename"].lower() or f["filename"].endswith("_test.py")
            for f in files_written
        )
        if not has_tests and files_written and review.get("score", 0) >= 6:
            log("TEST GEN: Generating tests automatically...")
            main_file = files_written[0]
            test_code = generate_tests(
                main_file["content"],
                last_language,
                main_file["filename"]
            )
            test_filename = get_test_filename(main_file["filename"], last_language)
            from tools.file_tools import write_file
            write_file(test_filename, test_code, user_id)
            log(f"TEST GEN: Tests written to {test_filename}")
            final_answer += f"\n\n(Auto-generated tests saved to {test_filename})"

    # Static analysis
    analysis = None
    if files_written and detected_language:
        main_file = files_written[0]
        log(f"STATIC ANALYSIS: Running on {main_file['filename']}...")
        analysis = run_analysis(main_file["content"], detected_language)
        if not analysis["clean"]:
            log(f"STATIC ANALYSIS: {len(analysis['issues'])} issues found")
            # Use formatted version if available
            if analysis.get("formatted_code") != main_file["content"]:
                from tools.file_tools import write_file
                write_file(main_file["filename"], analysis["formatted_code"], user_id)
                log("STATIC ANALYSIS: Applied auto-formatting")

    return {
        "task": task,
        "plan": plan,
        "steps": steps,
        "final_answer": final_answer,
        "total_steps": len(steps),
        "scratchpad": scratchpad_read(user_id),
        "recalled_memories": past_memories,
        "review": review,        # NEW
        "analysis": analysis,    # NEW
    }
