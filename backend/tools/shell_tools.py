import subprocess
import tempfile
import os

def run_python(code: str) -> dict:
    """Run Python code inside Docker sandbox."""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(code)
            tmp_path = f.name

        filename = os.path.basename(tmp_path)
        cmd = f"docker run --rm -v {tmp_path}:/workspace/{filename} leo-sandbox python3 /workspace/{filename}"

        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        os.unlink(tmp_path)

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Code execution timed out (30s limit)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_shell(command: str) -> dict:
    """Run a shell command inside Docker sandbox."""
    try:
        cmd = f'docker run --rm leo-sandbox bash -c "{command}"'
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out (30s limit)"}
    except Exception as e:
        return {"success": False, "error": str(e)}
