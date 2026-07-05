import asyncio
import subprocess
import tempfile
import os
import time

WORKSPACE_DIR = "/tmp/leo_workspace"
os.makedirs(WORKSPACE_DIR, exist_ok=True)


def get_user_workspace(user_id: str = "anonymous") -> str:
    path = os.path.join(WORKSPACE_DIR, user_id)
    os.makedirs(path, exist_ok=True)
    return path


def run_python(code: str, user_id: str = "anonymous", _retry: int = 0) -> dict:
    """Run Python code inside Docker sandbox with workspace mounted."""
    try:
        workspace = get_user_workspace(user_id)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, dir=workspace
        ) as f:
            f.write(code)
            tmp_path = f.name

        filename = os.path.basename(tmp_path)
        cmd = (
            f"docker run --rm "
            f"-v {workspace}:/workspace "
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
            return run_python(code, user_id=user_id, _retry=_retry + 1)

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        if _retry < 1:
            return run_python(code, user_id=user_id, _retry=_retry + 1)
        return {"success": False, "error": "Code execution timed out (60s limit)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_shell(command: str, user_id: str = "anonymous", _retry: int = 0) -> dict:
    """Run a shell command inside Docker sandbox with workspace mounted."""
    try:
        workspace = get_user_workspace(user_id)
        # Escape double quotes in the command to prevent shell injection
        safe_command = command.replace('"', '\\"')
        cmd = (
            f'docker run --rm '
            f'-v {workspace}:/workspace '
            f'-w /workspace '
            f'leo-sandbox bash -c "{safe_command}"'
        )
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=60
        )

        # Detect transient Docker daemon hiccups and retry once automatically
        if result.returncode != 0 and "Cannot connect to the Docker daemon" in result.stderr and _retry < 1:
            time.sleep(1)
            return run_shell(command, user_id=user_id, _retry=_retry + 1)

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        if _retry < 1:
            return run_shell(command, user_id=user_id, _retry=_retry + 1)
        return {"success": False, "error": "Command timed out (60s limit)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def run_python_streaming(code: str, websocket):
    """Run Python in Docker, streaming output line-by-line over a WebSocket."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        tmp_path = f.name

    filename = os.path.basename(tmp_path)
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{tmp_path}:/workspace/{filename}",
        "leo-sandbox", "python3", f"/workspace/{filename}"
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        async def stream_output(stream, stream_name):
            while True:
                line = await stream.readline()
                if not line:
                    break
                text = line.decode().rstrip()
                await websocket.send_json({
                    "type": stream_name,
                    "content": text
                })

        await asyncio.gather(
            stream_output(process.stdout, "stdout"),
            stream_output(process.stderr, "stderr")
        )

        await process.wait()
        os.unlink(tmp_path)

        await websocket.send_json({
            "type": "exit",
            "exit_code": process.returncode,
            "success": process.returncode == 0
        })

    except Exception as e:
        await websocket.send_json({"type": "error", "content": str(e)})
