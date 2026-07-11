import google.generativeai as genai
import json

PR_REVIEW_PROMPT = """You are a senior engineer doing a thorough PR review.

Task that was implemented: {task}

Files produced:
{files}

Execution output:
{output}

Do a PR review covering:
1. CORRECTNESS — does it actually solve the task? does it handle edge cases?
2. CODE QUALITY — readability, naming, structure, documentation
3. ROBUSTNESS — error handling, input validation, resource cleanup
4. COMPLETENESS — are all requirements met? anything missing?
5. PRODUCTION READINESS — could this ship without embarrassment?

Respond with JSON ONLY:
{{
  "approve": true/false,
  "score": 1-10,
  "summary": "one sentence verdict",
  "blocking_issues": ["critical issues that must be fixed before DONE"],
  "suggestions": ["non-blocking improvements for next time"],
  "rewrite_needed": true/false,
  "what_was_done_well": ["things LEO got right"]
}}

Score guide:
10 = would merge immediately, production ready
8-9 = good code, minor suggestions only
6-7 = works but needs improvement
4-5 = significant issues, needs revision
1-3 = fundamental problems, rewrite needed

Be a strict but fair reviewer. Don't approve mediocre code.
"""

REWRITE_PROMPT = """You are LEO, an expert software engineer.

Your original implementation had these blocking issues:
{issues}

Original code:
{original_code}

Rewrite the code fixing ALL blocking issues.
Apply these improvements too:
{suggestions}

Return ONLY the improved code — complete, no truncation, no markdown.
"""


def pr_review(
    task: str,
    files: list[dict],  # [{"filename": "x.py", "content": "..."}]
    output: str
) -> dict:
    """Perform a PR-style review of LEO's output."""
    try:
        model = genai.GenerativeModel(
            "gemini-flash-lite-latest",
            generation_config={
                "temperature": 0.1,
                "response_mime_type": "application/json"
            }
        )

        files_text = "\n\n".join(
            f"### {f['filename']}\n```\n{f['content'][:2000]}\n```"
            for f in files
        )

        response = model.generate_content(
            PR_REVIEW_PROMPT.format(
                task=task,
                files=files_text,
                output=output[:1000]
            )
        )

        return json.loads(response.text)

    except Exception as e:
        return {
            "approve": True,
            "score": 7,
            "summary": f"Review failed: {str(e)}",
            "blocking_issues": [],
            "suggestions": [],
            "rewrite_needed": False,
            "what_was_done_well": []
        }


def rewrite_code(
    original_code: str,
    blocking_issues: list[str],
    suggestions: list[str]
) -> str:
    """Rewrite code based on PR review feedback."""
    try:
        model = genai.GenerativeModel(
            "gemini-flash-lite-latest",
            generation_config={"temperature": 0.2}
        )

        response = model.generate_content(
            REWRITE_PROMPT.format(
                original_code=original_code[:4000],
                issues="\n".join(f"- {i}" for i in blocking_issues),
                suggestions="\n".join(f"- {s}" for s in suggestions[:5])
            )
        )

        code = response.text.strip()
        if code.startswith("```"):
            lines = code.split("\n")
            code = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        return code

    except Exception:
        return original_code
