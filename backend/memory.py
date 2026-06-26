import os
import chromadb
import uuid

# A simple in-memory scratchpad
_scratchpad = []

def scratchpad_write(note: str):
    _scratchpad.append(note)

def scratchpad_read() -> list:
    return _scratchpad.copy()

def scratchpad_clear():
    _scratchpad.clear()

# ChromaDB for long-term memory
try:
    client = chromadb.PersistentClient(path="/tmp/leo_memory")
    collection = client.get_or_create_collection(name="tasks")
except Exception as e:
    print(f"Failed to init ChromaDB: {e}")
    collection = None

def remember_task(task: str, final_answer: str, success: bool):
    if collection is None:
        return
    doc_id = str(uuid.uuid4())
    try:
        collection.add(
            documents=[task],
            metadatas=[{"task": task, "final_answer": str(final_answer), "success": success}],
            ids=[doc_id]
        )
    except Exception as e:
        print(f"Failed to remember task: {e}")

def recall_similar_tasks(task: str, n: int = 2) -> list:
    if collection is None:
        return []
    try:
        if collection.count() == 0:
            return []
        
        results = collection.query(
            query_texts=[task],
            n_results=min(n, collection.count())
        )
        memories = []
        if results and results.get("metadatas") and len(results["metadatas"]) > 0:
            for meta in results["metadatas"][0]:
                memories.append(meta)
        return memories
    except Exception as e:
        print(f"Memory recall failed: {e}")
        return []

def memory_stats() -> dict:
    """Quick stats for debugging/UI."""
    try:
        if collection is None:
            return {"total_tasks_remembered": 0}
        return {"total_tasks_remembered": collection.count()}
    except Exception:
        return {"total_tasks_remembered": 0}
