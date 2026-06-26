import subprocess
import tempfile
import os
import time

WORKSPACE_DIR = "/tmp/leo_workspace"
os.makedirs(WORKSPACE_DIR, exist_ok=True)


def run_python(code: str, _retry: int = 0) -> dict:
    """Run Python code inside Docker sandbox with workspace mounted."""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, dir=WORKSPACE_DIR
        ) as f:
            f.write(code)
            tmp_path = f.name

        filename = os.path.basename(tmp_path)
        cmd = (
            f"docker run --rm "
            f"-v {WORKSPACE_DIR}:/workspace "
            f"leo-sandbox python3 /workspace/{filename}"
        )

        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=60
        )
        # Clean up the temp file after execution
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

        # Detect transient Docker daemon hiccups and retry once automatically
        if result.returncode != 0 and "Cannot connect to the Docker daemon" in result.stderr and _retry < 1:
            time.sleep(1)
            return run_python(code, _retry=_retry + 1)

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        if _retry < 1:
            return run_python(code, _retry=_retry + 1)
        return {"success": False, "error": "Code execution timed out (60s limit)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_shell(command: str, _retry: int = 0) -> dict:
    """Run a shell command inside Docker sandbox with workspace mounted."""
    try:
        # Escape double quotes in the command to prevent shell injection
        safe_command = command.replace('"', '\\"')
        cmd = (
            f'docker run --rm '
            f'-v {WORKSPACE_DIR}:/workspace '
            f'-w /workspace '
            f'leo-sandbox bash -c "{safe_command}"'
        )
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=60
        )

        # Detect transient Docker daemon hiccups and retry once automatically
        if result.returncode != 0 and "Cannot connect to the Docker daemon" in result.stderr and _retry < 1:
            time.sleep(1)
            return run_shell(command, _retry=_retry + 1)

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        if _retry < 1:
            return run_shell(command, _retry=_retry + 1)
        return {"success": False, "error": "Command timed out (60s limit)"}
    except Exception as e:
        return {"success": False, "error": str(e)}
