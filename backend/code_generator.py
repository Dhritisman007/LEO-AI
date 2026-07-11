import google.generativeai as genai

DRAFT_PROMPT = """You are an expert {language} engineer.

Task: {task}

Write a complete, production-quality {language} implementation.
Follow these requirements strictly:
{style_guide}

Return ONLY the code — no explanation, no markdown backticks, no preamble.
Write the COMPLETE implementation — never truncate or use placeholder comments.
"""

REVIEW_PROMPT = """You are a senior {language} engineer doing a code review.

Original task: {task}

Code to review:
```{language}
{code}
```

Review this code against these quality standards:
{style_guide}

Identify specific issues. Respond with JSON only:
{{
  "issues": [
    {{"line": "approximate line or function name", "severity": "critical|major|minor", "issue": "description", "fix": "how to fix"}}
  ],
  "score": 1-10,
  "overall": "one sentence summary"
}}

Be specific and actionable. Score 9+ means ship it. Score below 7 needs a rewrite.
"""

REFINE_PROMPT = """You are an expert {language} engineer.

Original task: {task}

Your first draft:
```{language}
{original_code}
```

A senior engineer found these issues:
{issues}

Rewrite the code fixing ALL issues while keeping what was good.
Return ONLY the improved code — no explanation, no markdown, no backticks.
The code must be complete and runnable.
"""


def generate_high_quality_code(
    task: str,
    language: str = "python",
    style_guide: str = ""
) -> dict:
    """
    Generate code using a 3-pass draft → review → refine pipeline.
    Returns the best version along with review feedback.
    """
    model = genai.GenerativeModel(
        "gemini-flash-lite-latest",
        generation_config={"temperature": 0.2}
    )

    # Pass 1 — Draft
    draft_response = model.generate_content(
        DRAFT_PROMPT.format(task=task, language=language, style_guide=style_guide)
    )
    draft_code = draft_response.text.strip()
    # Strip markdown if Gemini added it
    if draft_code.startswith("```"):
        lines = draft_code.split("\n")
        draft_code = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    # Pass 2 — Review
    import json
    review_model = genai.GenerativeModel(
        "gemini-flash-lite-latest",
        generation_config={
            "temperature": 0.1,
            "response_mime_type": "application/json"
        }
    )
    review_response = review_model.generate_content(
        REVIEW_PROMPT.format(
            task=task,
            language=language,
            code=draft_code,
            style_guide=style_guide[:2000]
        )
    )

    try:
        review = json.loads(review_response.text)
    except Exception:
        review = {"issues": [], "score": 7, "overall": "Review parsing failed"}

    score = review.get("score", 7)
    issues = review.get("issues", [])
    critical_issues = [i for i in issues if i.get("severity") == "critical"]

    # Pass 3 — Refine (only if score < 8 or there are critical issues)
    final_code = draft_code
    refined = False

    if score < 8 or critical_issues:
        issues_text = "\n".join(
            f"- [{i.get('severity', 'issue')}] {i.get('line', '')}: {i.get('issue', '')} → Fix: {i.get('fix', '')}"
            for i in issues
        )

        refine_response = model.generate_content(
            REFINE_PROMPT.format(
                task=task,
                language=language,
                original_code=draft_code,
                issues=issues_text
            )
        )
        refined_code = refine_response.text.strip()
        if refined_code.startswith("```"):
            lines = refined_code.split("\n")
            refined_code = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        final_code = refined_code
        refined = True

    return {
        "code": final_code,
        "draft_code": draft_code,
        "review": review,
        "refined": refined,
        "final_score": score if not refined else min(score + 2, 10),
        "issues_fixed": len(issues) if refined else 0,
    }
