import chromadb
import os
import time

MEMORY_DIR = "/tmp/leo_memory"
os.makedirs(MEMORY_DIR, exist_ok=True)

client = chromadb.PersistentClient(path=MEMORY_DIR)

_scratchpads = {}  # user_id -> list of notes


def get_collection(user_id: str = "anonymous"):
    return client.get_or_create_collection(name=f"leo_tasks_{user_id}")


def scratchpad_write(note: str, user_id: str = "anonymous"):
    _scratchpads.setdefault(user_id, []).append(note)


def scratchpad_read(user_id: str = "anonymous") -> list:
    return _scratchpads.get(user_id, [])


def scratchpad_clear(user_id: str = "anonymous"):
    _scratchpads[user_id] = []


def remember_task(task: str, final_answer: str, success: bool, user_id: str = "anonymous"):
    try:
        collection = get_collection(user_id)
        doc_id = f"task_{int(time.time() * 1000)}"
        collection.add(
            documents=[f"Task: {task}\nOutcome: {final_answer}"],
            metadatas=[{
                "task": task, "final_answer": final_answer,
                "success": success, "timestamp": time.time()
            }],
            ids=[doc_id]
        )
    except Exception as e:
        print(f"Memory write failed: {e}")


def recall_similar_tasks(task: str, user_id: str = "anonymous", n: int = 3) -> list:
    try:
        collection = get_collection(user_id)
        if collection.count() == 0:
            return []
        results = collection.query(query_texts=[task], n_results=min(n, collection.count()))
        memories = []
        if results["metadatas"] and results["metadatas"][0]:
            for meta in results["metadatas"][0]:
                memories.append(meta)
        return memories
    except Exception as e:
        print(f"Memory recall failed: {e}")
        return []


def memory_stats(user_id: str = "anonymous") -> dict:
    try:
        return {"total_tasks_remembered": get_collection(user_id).count()}
    except Exception:
        return {"total_tasks_remembered": 0}
