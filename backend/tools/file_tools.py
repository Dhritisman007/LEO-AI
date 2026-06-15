import os

WORKSPACE_DIR = "/tmp/leo_workspace"
os.makedirs(WORKSPACE_DIR, exist_ok=True)


def read_file(filename: str) -> dict:
    """Read a file from the workspace."""
    try:
        filepath = os.path.join(WORKSPACE_DIR, filename)
        if not os.path.exists(filepath):
            return {"success": False, "error": f"File '{filename}' not found"}
        with open(filepath, "r") as f:
            content = f.read()
        return {"success": True, "filename": filename, "content": content}
    except Exception as e:
        return {"success": False, "error": str(e)}


def write_file(filename: str, content: str) -> dict:
    """Write content to a file in the workspace."""
    try:
        filepath = os.path.join(WORKSPACE_DIR, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True) if os.path.dirname(filepath) else None
        with open(filepath, "w") as f:
            f.write(content)
        return {"success": True, "filename": filename, "message": f"File '{filename}' written successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_files() -> dict:
    """List all files in the workspace."""
    try:
        files = []
        for root, dirs, filenames in os.walk(WORKSPACE_DIR):
            for fname in filenames:
                full_path = os.path.join(root, fname)
                rel_path = os.path.relpath(full_path, WORKSPACE_DIR)
                files.append(rel_path)
        return {"success": True, "files": files}
    except Exception as e:
        return {"success": False, "error": str(e)}
