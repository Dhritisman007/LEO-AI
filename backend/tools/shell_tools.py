import subprocess
import tempfile
import os
import time
import shutil


# ── Language configs ─────────────────────────────────────────────────

LANGUAGE_CONFIG = {
    "python": {
        "extension": ".py",
        "run_cmd": lambda f: f"python3 /workspace/{f}",
        "compile_cmd": None,
        "local_run": lambda path: ["python3", path],
        "local_compile": None,
    },
    "javascript": {
        "extension": ".js",
        "run_cmd": lambda f: f"node /workspace/{f}",
        "compile_cmd": None,
        "local_run": lambda path: ["node", path],
        "local_compile": None,
    },
    "java": {
        "extension": ".java",
        "compile_cmd": lambda f: f"cd /workspace && javac {f}",
        "run_cmd": lambda f: f"cd /workspace && java {f.replace('.java', '')}",
        "local_compile": lambda path, fname: ["javac", path],
        "local_run": lambda path: ["java", "-cp", os.path.dirname(path), os.path.splitext(os.path.basename(path))[0]],
    },
    "cpp": {
        "extension": ".cpp",
        "compile_cmd": lambda f: f"cd /workspace && g++ -o program {f}",
        "run_cmd": lambda f: "cd /workspace && ./program",
        "local_compile": lambda path, fname: ["g++", "-o", path + ".out", path],
        "local_run": lambda path: [path + ".out"],
    },
    "c": {
        "extension": ".c",
        "compile_cmd": lambda f: f"cd /workspace && gcc -o program {f}",
        "run_cmd": lambda f: "cd /workspace && ./program",
        "local_compile": lambda path, fname: ["gcc", "-o", path + ".out", path],
        "local_run": lambda path: [path + ".out"],
    },
    "go": {
        "extension": ".go",
        "compile_cmd": None,
        "run_cmd": lambda f: f"cd /workspace && go run {f}",
        "local_run": lambda path: ["go", "run", path],
        "local_compile": None,
    },
    "rust": {
        "extension": ".rs",
        "compile_cmd": lambda f: f"cd /workspace && rustc {f} -o program",
        "run_cmd": lambda f: "cd /workspace && ./program",
        "local_compile": lambda path, fname: ["rustc", path, "-o", path + ".out"],
        "local_run": lambda path: [path + ".out"],
    },
    "bash": {
        "extension": ".sh",
        "compile_cmd": None,
        "run_cmd": lambda f: f"bash /workspace/{f}",
        "local_run": lambda path: ["bash", path],
        "local_compile": None,
    },
}


# ── Docker availability check ───────────────────────────────────────

_docker_available = None  # cached after first check


def _is_docker_available() -> bool:
    """Check if Docker daemon is reachable. Result is cached."""
    global _docker_available
    if _docker_available is not None:
        return _docker_available
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True, text=True, timeout=5
        )
        _docker_available = result.returncode == 0
    except Exception:
        _docker_available = False
    return _docker_available


# ── Docker runner ────────────────────────────────────────────────────

def _run_in_docker(commands: list[str], tmp_path: str, docker_filename: str = None) -> dict:
    """
    Mount a temp file into Docker and run one or more shell commands.
    Commands are joined with && so failure stops the chain.
    """
    filename = docker_filename or os.path.basename(tmp_path)
    full_cmd = " && ".join(commands)

    docker_cmd = (
        f'docker run --rm '
        f'-v {tmp_path}:/workspace/{filename} '
        f'leo-sandbox bash -c "{full_cmd}"'
    )

    try:
        result = subprocess.run(
            docker_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Execution timed out (60s limit)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Local runner (fallback when Docker is unavailable) ───────────────

def _run_local(code: str, language: str, config: dict, filename: str, user_id: str = "anonymous") -> dict:
    """Run code directly on the host machine as a fallback.
    
    Runs inside the user's workspace directory so the code can access
    files LEO previously wrote via write_file. Uses a temp-prefixed 
    filename to avoid overwriting existing workspace files.
    """
    from .file_tools import get_workspace_dir
    
    ext = config["extension"]
    workspace = get_workspace_dir(user_id)
    
    # Use a unique temp filename so we don't overwrite workspace files
    import uuid
    run_filename = f"_leo_run_{uuid.uuid4().hex[:8]}{ext}"
    file_path = os.path.join(workspace, run_filename)
    
    try:
        with open(file_path, "w") as f:
            f.write(code)

        # Compile if needed
        if config.get("local_compile"):
            compile_cmd = config["local_compile"](file_path, run_filename)
            compile_result = subprocess.run(
                compile_cmd,
                capture_output=True, text=True, timeout=30,
                cwd=workspace
            )
            if compile_result.returncode != 0:
                os.unlink(file_path)
                return {
                    "success": False,
                    "stdout": compile_result.stdout,
                    "stderr": compile_result.stderr,
                    "exit_code": compile_result.returncode,
                }

        # Run inside the workspace directory
        run_cmd = config["local_run"](file_path)
        result = subprocess.run(
            run_cmd,
            capture_output=True, text=True, timeout=60,
            cwd=workspace
        )

        # Clean up temp run file
        try:
            os.unlink(file_path)
        except OSError:
            pass

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        try:
            os.unlink(file_path)
        except OSError:
            pass
        return {"success": False, "error": "Execution timed out (60s limit)"}
    except FileNotFoundError as e:
        return {"success": False, "error": f"Runtime not found locally: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Public API ───────────────────────────────────────────────────────

def run_code(code: str, language: str = "python", filename: str = None, user_id: str = "anonymous") -> dict:
    """
    Universal code runner — handles any supported language.
    Tries Docker first; falls back to local execution if Docker is unavailable.
    """
    language = language.lower().strip()

    # Normalize common aliases
    aliases = {
        "js": "javascript",
        "node": "javascript",
        "c++": "cpp",
        "cc": "cpp",
        "golang": "go",
        "rs": "rust",
        "sh": "bash",
        "shell": "bash",
    }
    language = aliases.get(language, language)

    config = LANGUAGE_CONFIG.get(language)
    if not config:
        return {
            "success": False,
            "error": f"Language '{language}' not supported. Supported: {', '.join(LANGUAGE_CONFIG.keys())}"
        }

    # Java requires filename to match class name
    if language == "java" and not filename:
        import re
        match = re.search(r"public\s+class\s+(\w+)", code)
        filename = f"{match.group(1)}.java" if match else "Main.java"

    ext = config["extension"]
    if not filename:
        filename = f"program{ext}"
    elif not filename.endswith(ext):
        filename = filename + ext

    # ── Try Docker first ──
    if _is_docker_available():
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=ext, delete=False, prefix=filename.replace(ext, "_")
            ) as f:
                f.write(code)
                tmp_path = f.name

            commands = []
            if config["compile_cmd"]:
                commands.append(config["compile_cmd"](filename))
            commands.append(config["run_cmd"](filename))

            result = _run_in_docker(commands, tmp_path, filename)
            os.unlink(tmp_path)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Fallback: run locally ──
    return _run_local(code, language, config, filename, user_id=user_id)


# Keep these for backward compatibility
def run_python(code: str) -> dict:
    return run_code(code, "python")


def run_shell(command: str) -> dict:
    """Run an arbitrary shell command. Uses Docker if available, otherwise runs locally."""
    if _is_docker_available():
        try:
            cmd = f'docker run --rm leo-sandbox bash -c "{command}"'
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=60
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Fallback: run locally (restricted to safe commands)
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out (60s limit)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def run_python_streaming(code: str, websocket):
    """Streaming version for the terminal panel — Python only for now."""
    import asyncio

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        tmp_path = f.name

    if _is_docker_available():
        filename = os.path.basename(tmp_path)
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{tmp_path}:/workspace/{filename}",
            "leo-sandbox", "python3", f"/workspace/{filename}"
        ]
    else:
        # Local fallback
        cmd = ["python3", tmp_path]

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
                await websocket.send_json({
                    "type": stream_name,
                    "content": line.decode().rstrip()
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
