import os
from storage import upload_file, download_file, list_user_files

# Local scratch directory for code execution (shell_tools runs code on real
# disk regardless of storage backend). Not used for persisted file storage.
EXEC_WORKSPACE_DIR = "/tmp/leo_workspace"


def get_workspace_dir(user_id: str = "anonymous") -> str:
    path = os.path.join(EXEC_WORKSPACE_DIR, user_id)
    os.makedirs(path, exist_ok=True)
    return path


def read_file(filename: str, user_id: str = "anonymous") -> dict:
    result = download_file(filename, user_id)
    if not result.get("success"):
        return {"success": False, "error": result.get("error", f"File '{filename}' not found")}
    try:
        content = result["content"]
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        return {"success": True, "content": content, "filename": filename}
    except Exception as e:
        return {"success": False, "error": str(e)}


def write_file(filename: str, content: str, user_id: str = "anonymous") -> dict:
    result = upload_file(filename, content, user_id)
    if not result.get("success"):
        return {"success": False, "error": result.get("error")}
    return {"success": True, "message": f"File '{filename}' written successfully"}


def list_files(user_id: str = "anonymous") -> dict:
    result = list_user_files(user_id)
    if not result.get("success"):
        return {"success": False, "error": result.get("error")}
    return {"success": True, "files": [f["filename"] for f in result["files"]]}


def get_file_tree(user_id: str = "anonymous") -> dict:
    try:
        result = list_user_files(user_id)
        if not result.get("success"):
            return {"success": False, "error": result.get("error")}

        tree = {"name": "workspace", "type": "folder", "children": []}

        for entry in result["files"]:
            rel = entry["filename"]
            parts = rel.split(os.sep) if os.sep in rel else rel.split("/")
            node = tree
            for part in parts[:-1]:
                found = next((c for c in node["children"] if c["name"] == part and c["type"] == "folder"), None)
                if not found:
                    found = {"name": part, "type": "folder", "children": []}
                    node["children"].append(found)
                node = found
            node["children"].append({
                "name": parts[-1],
                "type": "file",
                "size": entry.get("size_bytes", 0),
            })

        return {"success": True, "tree": tree}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_file_content(filename: str, user_id: str = "anonymous") -> dict:
    return read_file(filename, user_id)
