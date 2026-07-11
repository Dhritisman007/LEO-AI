import subprocess
import tempfile
import os


def analyze_python(code: str) -> dict:
    """Run flake8 + black check on Python code."""
    issues = []
    formatted_code = code

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        tmp = f.name

    try:
        # Run flake8 for style issues
        flake8 = subprocess.run(
            ["docker", "run", "--rm",
             "-v", f"{tmp}:/tmp/check.py",
             "leo-sandbox",
             "bash", "-c", "pip install flake8 -q && flake8 /tmp/check.py --max-line-length=100"],
            capture_output=True, text=True, timeout=30
        )
        if flake8.stdout:
            for line in flake8.stdout.strip().split("\n"):
                if line:
                    issues.append({"tool": "flake8", "message": line.replace("/tmp/check.py", "")})

        # Run black for formatting
        black = subprocess.run(
            ["docker", "run", "--rm",
             "-v", f"{tmp}:/tmp/check.py",
             "leo-sandbox",
             "bash", "-c", "pip install black -q && black /tmp/check.py --quiet && cat /tmp/check.py"],
            capture_output=True, text=True, timeout=30
        )
        if black.returncode == 0 and black.stdout:
            formatted_code = black.stdout

    except Exception as e:
        issues.append({"tool": "error", "message": str(e)})
    finally:
        os.unlink(tmp)

    return {
        "issues": issues,
        "formatted_code": formatted_code,
        "clean": len(issues) == 0
    }


def analyze_javascript(code: str) -> dict:
    """Run basic JS analysis."""
    issues = []

    checks = [
        ("var ", "Use 'const' or 'let' instead of 'var'"),
        ("console.log(", "Remove debug console.log before production"),
        ("== ", "Use === instead of == for strict equality"),
        ("!= ", "Use !== instead of != for strict inequality"),
        ("any", "Avoid TypeScript 'any' type — use specific types"),
    ]

    for pattern, message in checks:
        if pattern in code:
            issues.append({"tool": "custom", "message": message})

    return {"issues": issues, "formatted_code": code, "clean": len(issues) == 0}


def run_analysis(code: str, language: str) -> dict:
    """Run static analysis for the given language."""
    language = language.lower()
    if language == "python":
        return analyze_python(code)
    elif language in ("javascript", "typescript", "js", "ts"):
        return analyze_javascript(code)
    else:
        return {"issues": [], "formatted_code": code, "clean": True}
