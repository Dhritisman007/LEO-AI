import google.generativeai as genai

TEST_PROMPT = """You are an expert {language} test engineer.

Here is production code that needs comprehensive tests:
```{language}
{code}
```

Write a complete test file that covers:
1. Happy path — normal inputs that should work
2. Edge cases — empty input, None/null, zero, negative numbers, boundary values
3. Error cases — invalid input that should raise exceptions
4. Integration — multiple functions working together

Requirements:
- Use the standard testing framework for {language}
  (Python: pytest | JS/TS: jest | Java: JUnit 5 | Go: testing package | Rust: built-in tests)
- Each test has a descriptive name explaining what it tests
- Tests are independent — no shared mutable state between tests
- At least 80% code coverage
- Include edge cases a junior developer might miss

Return ONLY the test code — no explanation, no markdown backticks.
"""


def generate_tests(code: str, language: str = "python", filename: str = "code") -> str:
    """Generate comprehensive tests for the given code."""
    try:
        model = genai.GenerativeModel(
            "gemini-flash-lite-latest",
            generation_config={"temperature": 0.2}
        )

        response = model.generate_content(
            TEST_PROMPT.format(code=code[:4000], language=language)
        )

        test_code = response.text.strip()
        if test_code.startswith("```"):
            lines = test_code.split("\n")
            test_code = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        return test_code

    except Exception as e:
        return f"# Test generation failed: {str(e)}"


def get_test_filename(filename: str, language: str) -> str:
    """Get the appropriate test filename for a language."""
    base = filename.rsplit(".", 1)[0]
    ext_map = {
        "python": f"test_{base}.py",
        "javascript": f"{base}.test.js",
        "typescript": f"{base}.test.ts",
        "java": f"{base}Test.java",
        "go": f"{base}_test.go",
        "rust": f"{base}_test.rs",
        "cpp": f"{base}_test.cpp",
    }
    return ext_map.get(language.lower(), f"test_{base}.py")
