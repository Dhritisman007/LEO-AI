import subprocess
import tempfile
import os
import time


LANGUAGE_CONFIG = {
    "python": {
        "extension": ".py",
        "run_cmd": lambda f: f"python3 /workspace/{f}",
        "compile_cmd": None,
    },
    "javascript": {
        "extension": ".js",
        "run_cmd": lambda f: f"node /workspace/{f}",
        "compile_cmd": None,
    },
    "java": {
        "extension": ".java",
        # Java needs compile then run — classname must match filename
        "compile_cmd": lambda f: f"cd /workspace && javac {f}",
        "run_cmd": lambda f: f"cd /workspace && java {f.replace('.java', '')}",
    },
    "cpp": {
        "extension": ".cpp",
        "compile_cmd": lambda f: f"cd /workspace && g++ -o program {f}",
        "run_cmd": lambda f: "cd /workspace && ./program",
    },
    "c": {
        "extension": ".c",
        "compile_cmd": lambda f: f"cd /workspace && gcc -o program {f}",
        "run_cmd": lambda f: "cd /workspace && ./program",
    },
    "go": {
        "extension": ".go",
        "compile_cmd": None,
        "run_cmd": lambda f: f"cd /workspace && go run {f}",
    },
    "rust": {
        "extension": ".rs",
        "compile_cmd": lambda f: f"cd /workspace && rustc {f} -o program",
        "run_cmd": lambda f: "cd /workspace && ./program",
    },
    "bash": {
        "extension": ".sh",
        "compile_cmd": None,
        "run_cmd": lambda f: f"bash /workspace/{f}",
    },
}


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
            timeout=60  # longer timeout for compilation
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


def run_code(code: str, language: str = "python", filename: str = None) -> dict:
    """
    Universal code runner — handles any supported language.
    Automatically compiles if needed, then runs.
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


# Keep these for backward compatibility — they now call run_code internally
def run_python(code: str) -> dict:
    return run_code(code, "python")


def run_shell(command: str) -> dict:
    """Run an arbitrary shell command in the sandbox."""
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


async def run_python_streaming(code: str, websocket):
    """Streaming version for the terminal panel — Python only for now."""
    import asyncio

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
        import asyncio
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
