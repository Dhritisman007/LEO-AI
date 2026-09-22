"""Agent checkpoints so a paused/interrupted task can be resumed.

Uses a Supabase table in production, local JSON files in development.
"""
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

CHECKPOINT_DIR = "/tmp/leo_checkpoints"
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

CHECKPOINT_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days

_supabase_client = None


def get_supabase():
    global _supabase_client
    if _supabase_client is None:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in production")
        _supabase_client = create_client(url, key)
    return _supabase_client


def save_checkpoint(user_id: str, task: str, history: list, steps: list, plan: list, current_plan_idx: int) -> str:
    """Save agent state so it can be resumed later."""
    checkpoint_id = f"{user_id}_{int(time.time())}"
    now = time.time()

    if IS_PRODUCTION:
        try:
            supabase = get_supabase()
            supabase.table("checkpoints").insert({
                "id": checkpoint_id,
                "user_id": user_id,
                "task": task,
                "history": history,
                "steps": steps,
                "plan": plan,
                "current_plan_idx": current_plan_idx,
                "created_at": now,
                "expires_at": now + CHECKPOINT_TTL_SECONDS,
            }).execute()
        except Exception as e:
            print(f"Checkpoint save failed: {e}")
        return checkpoint_id

    checkpoint = {
        "id": checkpoint_id,
        "user_id": user_id,
        "task": task,
        "history": history,
        "steps": steps,
        "plan": plan,
        "current_plan_idx": current_plan_idx,
        "saved_at": now,
    }
    path = os.path.join(CHECKPOINT_DIR, f"{checkpoint_id}.json")
    with open(path, "w") as f:
        json.dump(checkpoint, f)
    return checkpoint_id


def load_checkpoint(checkpoint_id: str) -> dict | None:
    """Load a saved checkpoint."""
    if IS_PRODUCTION:
        try:
            supabase = get_supabase()
            result = supabase.table("checkpoints") \
                .select("*") \
                .eq("id", checkpoint_id) \
                .limit(1) \
                .execute()
            rows = result.data or []
            if not rows:
                return None
            row = rows[0]
            return {
                "id": row["id"],
                "user_id": row["user_id"],
                "task": row["task"],
                "history": row["history"],
                "steps": row["steps"],
                "plan": row["plan"],
                "current_plan_idx": row["current_plan_idx"],
                "saved_at": row["created_at"],
            }
        except Exception as e:
            print(f"Checkpoint load failed: {e}")
            return None

    path = os.path.join(CHECKPOINT_DIR, f"{checkpoint_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


def delete_checkpoint(checkpoint_id: str):
    """Delete a checkpoint after successful completion."""
    if IS_PRODUCTION:
        try:
            supabase = get_supabase()
            supabase.table("checkpoints").delete().eq("id", checkpoint_id).execute()
        except Exception as e:
            print(f"Checkpoint delete failed: {e}")
        return

    path = os.path.join(CHECKPOINT_DIR, f"{checkpoint_id}.json")
    if os.path.exists(path):
        os.remove(path)


def list_checkpoints(user_id: str) -> list:
    """List all resumable checkpoints for a user."""
    if IS_PRODUCTION:
        try:
            supabase = get_supabase()
            result = supabase.table("checkpoints") \
                .select("id, task, steps, created_at") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True) \
                .execute()
            return [
                {
                    "id": row["id"],
                    "task": (row["task"] or "")[:60],
                    "steps_completed": len(row["steps"] or []),
                    "saved_at": row["created_at"],
                }
                for row in (result.data or [])
            ]
        except Exception as e:
            print(f"Checkpoint list failed: {e}")
            return []

    checkpoints = []
    for fname in os.listdir(CHECKPOINT_DIR):
        if fname.startswith(user_id) and fname.endswith(".json"):
            path = os.path.join(CHECKPOINT_DIR, fname)
            with open(path, "r") as f:
                data = json.load(f)
                checkpoints.append({
                    "id": data["id"],
                    "task": data["task"][:60],
                    "steps_completed": len(data["steps"]),
                    "saved_at": data["saved_at"],
                })
    return sorted(checkpoints, key=lambda x: x["saved_at"], reverse=True)
