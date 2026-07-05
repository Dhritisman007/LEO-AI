import os

BASE_WORKSPACE_DIR = "/tmp/leo_workspace"

def get_workspace_dir(user_id: str = "anonymous") -> str:
    path = os.path.join(BASE_WORKSPACE_DIR, user_id)
    os.makedirs(path, exist_ok=True)
    return path


def read_file(filename: str, user_id: str = "anonymous") -> dict:
    try:
        workspace = get_workspace_dir(user_id)
        filepath = os.path.join(workspace, filename)
        if not os.path.exists(filepath):
            return {"success": False, "error": f"File '{filename}' not found"}
        with open(filepath, "r") as f:
            content = f.read()
        return {"success": True, "content": content, "filename": filename}
    except Exception as e:
        return {"success": False, "error": str(e)}


def write_file(filename: str, content: str, user_id: str = "anonymous") -> dict:
    try:
        workspace = get_workspace_dir(user_id)
        filepath = os.path.join(workspace, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            f.write(content)
        return {"success": True, "message": f"File '{filename}' written successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_files(user_id: str = "anonymous") -> dict:
    try:
        workspace = get_workspace_dir(user_id)
        files = []
        for root, dirs, filenames in os.walk(workspace):
            for fname in filenames:
                full = os.path.join(root, fname)
                rel = os.path.relpath(full, workspace)
                files.append(rel)
        return {"success": True, "files": files}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_file_tree(user_id: str = "anonymous") -> dict:
    try:
        workspace = get_workspace_dir(user_id)
        tree = {"name": "workspace", "type": "folder", "children": []}

        for root, dirs, filenames in os.walk(workspace):
            rel_root = os.path.relpath(root, workspace)
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
                node["children"].append({"name": fname, "type": "file", "size": size})

        return {"success": True, "tree": tree}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_file_content(filename: str, user_id: str = "anonymous") -> dict:
    return read_file(filename, user_id)
