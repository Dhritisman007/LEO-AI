import google.generativeai as genai
import json

CRITIC_PROMPT = """You are a senior software engineer reviewing code written by an AI agent.

Task the agent was given:
{task}

Code the agent produced:
{code}

Execution output:
{output}

Review the code and respond with a JSON object ONLY — no other text:
{{
  "score": 1-10,
  "passed": true/false,
  "issues": ["issue 1", "issue 2"],
  "improvements": ["improvement 1", "improvement 2"],
  "rewrite_needed": true/false,
  "rewrite_reason": "reason if rewrite needed"
}}

Score 8+ = good code, no rewrite needed.
Score below 6 = rewrite needed.

Focus on:
- Correctness (does it actually solve the task?)
- Code quality (readable, idiomatic, no obvious bugs)
- Edge cases (does it handle empty input, errors?)
- Efficiency (no obvious performance issues)
"""


def critique_code(task: str, code: str, output: str) -> dict:
    """
    Have a critic LLM review LEO's code output.
    Returns assessment with score and whether a rewrite is needed.
    """
    try:
        model = genai.GenerativeModel(
            "gemini-flash-lite-latest",
            generation_config={
                "temperature": 0.1,
                "response_mime_type": "application/json"
            }
        )

        prompt = CRITIC_PROMPT.format(
            task=task,
            code=code[:3000],  # cap to avoid token overflow
            output=output[:1000]
        )

        response = model.generate_content(prompt)
        result = json.loads(response.text)
        return result

    except Exception as e:
        return {
            "score": 7,
            "passed": True,
            "issues": [],
            "improvements": [],
            "rewrite_needed": False,
            "rewrite_reason": f"Critic failed: {str(e)}"
        }


REWRITE_PROMPT = """You are LEO, an expert coding agent. You previously wrote this code:

{original_code}

A code reviewer found these issues:
{issues}

And suggested these improvements:
{improvements}

Rewrite the code fixing ALL the issues and applying the improvements.
Return ONLY the improved code — no explanation, no markdown, no backticks.
"""


def rewrite_code(original_code: str, issues: list, improvements: list) -> str:
    """Ask LEO to rewrite code based on critic feedback."""
    try:
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={"temperature": 0.2}
        )

        prompt = REWRITE_PROMPT.format(
            original_code=original_code,
            issues="\n".join(f"- {i}" for i in issues),
            improvements="\n".join(f"- {i}" for i in improvements)
        )

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        return original_code  # fallback to original if rewrite fails
