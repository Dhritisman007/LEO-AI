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

def get_file_tree() -> dict:
    """Return files as a nested tree structure for UI rendering."""
    try:
        tree = {"name": "workspace", "type": "folder", "children": []}

        for root, dirs, filenames in os.walk(WORKSPACE_DIR):
            rel_root = os.path.relpath(root, WORKSPACE_DIR)
            # Find the node for this directory
            if rel_root == ".":
                node = tree
            else:
                parts = rel_root.split(os.sep)
                node = tree
                for part in parts:
                    found = next((c for c in node["children"] if c["name"] == part and c["type"] == "folder"), None)
                    if not found:
                        found = {"name": part, "type": "folder", "children": []}
                        node["children"].append(found)
                    node = found

            for fname in sorted(filenames):
                size = os.path.getsize(os.path.join(root, fname))
                node["children"].append({
                    "name": fname,
                    "type": "file",
                    "size": size
                })

        return {"success": True, "tree": tree}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_file_content(filename: str) -> dict:
    """Get content of a specific file for preview (alias of read_file, kept separate for clarity)."""
    return read_file(filename)
