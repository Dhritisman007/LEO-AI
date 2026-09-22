"""Storage layer for LEO's workspace files.

Uses Supabase Storage + Postgres in production, falls back to the local
filesystem in development so LEO works without any Supabase setup.
"""
import os
import time
import mimetypes
from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

BUCKET_NAME = "leo-workspace"
LOCAL_WORKSPACE_DIR = "/tmp/leo_workspace"
os.makedirs(LOCAL_WORKSPACE_DIR, exist_ok=True)

_supabase_client = None


def get_supabase():
    """Return a cached Supabase client, creating it on first use."""
    global _supabase_client
    if _supabase_client is None:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in production")
        _supabase_client = create_client(url, key)
    return _supabase_client


def _local_path(user_id: str, filename: str) -> str:
    path = os.path.join(LOCAL_WORKSPACE_DIR, user_id, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def _storage_path(user_id: str, filename: str) -> str:
    return f"{user_id}/{filename}"


def upload_file(filename: str, content: bytes | str, user_id: str = "anonymous") -> dict:
    """Upload/overwrite a file for a user. Accepts bytes or text content."""
    if isinstance(content, str):
        content = content.encode("utf-8")

    if not IS_PRODUCTION:
        try:
            path = _local_path(user_id, filename)
            with open(path, "wb") as f:
                f.write(content)
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    try:
        supabase = get_supabase()
        storage_path = _storage_path(user_id, filename)
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        supabase.storage.from_(BUCKET_NAME).upload(
            storage_path,
            content,
            {"content-type": content_type, "upsert": "true"},
        )

        now = time.time()
        supabase.table("workspace_files").upsert({
            "user_id": user_id,
            "filename": filename,
            "storage_path": storage_path,
            "size_bytes": len(content),
            "content_type": content_type,
            "updated_at": now,
        }, on_conflict="user_id,filename").execute()

        return {"success": True, "path": storage_path}
    except Exception as e:
        return {"success": False, "error": str(e)}


def download_file(filename: str, user_id: str = "anonymous") -> dict:
    """Download a file's content for a user."""
    if not IS_PRODUCTION:
        try:
            path = _local_path(user_id, filename)
            if not os.path.exists(path):
                return {"success": False, "error": f"File '{filename}' not found"}
            with open(path, "rb") as f:
                content = f.read()
            return {"success": True, "content": content, "filename": filename}
        except Exception as e:
            return {"success": False, "error": str(e)}

    try:
        supabase = get_supabase()
        storage_path = _storage_path(user_id, filename)
        content = supabase.storage.from_(BUCKET_NAME).download(storage_path)
        return {"success": True, "content": content, "filename": filename}
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_user_files(user_id: str = "anonymous") -> dict:
    """List all files belonging to a user."""
    if not IS_PRODUCTION:
        try:
            base = os.path.join(LOCAL_WORKSPACE_DIR, user_id)
            os.makedirs(base, exist_ok=True)
            files = []
            for root, _dirs, filenames in os.walk(base):
                for fname in filenames:
                    full = os.path.join(root, fname)
                    rel = os.path.relpath(full, base)
                    files.append({
                        "filename": rel,
                        "size_bytes": os.path.getsize(full),
                        "updated_at": os.path.getmtime(full),
                    })
            return {"success": True, "files": files}
        except Exception as e:
            return {"success": False, "error": str(e)}

    try:
        supabase = get_supabase()
        result = supabase.table("workspace_files") \
            .select("filename, size_bytes, content_type, updated_at") \
            .eq("user_id", user_id) \
            .execute()
        return {"success": True, "files": result.data or []}
    except Exception as e:
        return {"success": False, "error": str(e)}


def delete_file(filename: str, user_id: str = "anonymous") -> dict:
    """Delete a user's file."""
    if not IS_PRODUCTION:
        try:
            path = _local_path(user_id, filename)
            if os.path.exists(path):
                os.remove(path)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    try:
        supabase = get_supabase()
        storage_path = _storage_path(user_id, filename)
        supabase.storage.from_(BUCKET_NAME).remove([storage_path])
        supabase.table("workspace_files") \
            .delete() \
            .eq("user_id", user_id) \
            .eq("filename", filename) \
            .execute()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_file_url(filename: str, user_id: str = "anonymous", expires_in: int = 3600) -> dict:
    """Get a URL to access a file. Local dev returns a file:// path; prod returns a signed URL."""
    if not IS_PRODUCTION:
        path = _local_path(user_id, filename)
        return {"success": True, "url": f"file://{path}"}

    try:
        supabase = get_supabase()
        storage_path = _storage_path(user_id, filename)
        result = supabase.storage.from_(BUCKET_NAME).create_signed_url(storage_path, expires_in)
        return {"success": True, "url": result.get("signedURL") or result.get("signedUrl")}
    except Exception as e:
        return {"success": False, "error": str(e)}
