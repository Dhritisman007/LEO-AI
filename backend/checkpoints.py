import json
import os
import time

CHECKPOINT_DIR = "/tmp/leo_checkpoints"
os.makedirs(CHECKPOINT_DIR, exist_ok=True)


def save_checkpoint(user_id: str, task: str, history: list, steps: list, plan: list, current_plan_idx: int) -> str:
    """Save agent state so it can be resumed later."""
    checkpoint_id = f"{user_id}_{int(time.time())}"
    checkpoint = {
        "id": checkpoint_id,
        "user_id": user_id,
        "task": task,
        "history": history,
        "steps": steps,
        "plan": plan,
        "current_plan_idx": current_plan_idx,
        "saved_at": time.time(),
    }
    path = os.path.join(CHECKPOINT_DIR, f"{checkpoint_id}.json")
    with open(path, "w") as f:
        json.dump(checkpoint, f)
    return checkpoint_id


def load_checkpoint(checkpoint_id: str) -> dict | None:
    """Load a saved checkpoint."""
    path = os.path.join(CHECKPOINT_DIR, f"{checkpoint_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


def delete_checkpoint(checkpoint_id: str):
    """Delete a checkpoint after successful completion."""
    path = os.path.join(CHECKPOINT_DIR, f"{checkpoint_id}.json")
    if os.path.exists(path):
        os.remove(path)


def list_checkpoints(user_id: str) -> list:
    """List all resumable checkpoints for a user."""
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
