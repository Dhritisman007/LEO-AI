"""LEO's task memory: recalls similar past tasks to inform new ones.

Uses a Supabase table with keyword-overlap scoring in production (no
embeddings set up yet), falls back to local ChromaDB in development.
"""
import os
import re
import time
from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

_scratchpads = {}  # user_id -> list of notes

_supabase_client = None
_chroma_client = None


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


def _get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        # pyrefly: ignore [missing-import]
        import chromadb
        memory_dir = "/tmp/leo_memory"
        os.makedirs(memory_dir, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=memory_dir)
    return _chroma_client


def get_collection(user_id: str = "anonymous"):
    return _get_chroma_client().get_or_create_collection(name=f"leo_tasks_{user_id}")


def scratchpad_write(note: str, user_id: str = "anonymous"):
    _scratchpads.setdefault(user_id, []).append(note)


def scratchpad_read(user_id: str = "anonymous") -> list:
    return _scratchpads.get(user_id, [])


def scratchpad_clear(user_id: str = "anonymous"):
    _scratchpads[user_id] = []


_WORD_RE = re.compile(r"[a-z0-9]+")


def _keywords(text: str) -> set:
    return set(_WORD_RE.findall((text or "").lower()))


def remember_task(task: str, final_answer: str, success: bool, user_id: str = "anonymous"):
    if IS_PRODUCTION:
        try:
            supabase = get_supabase()
            supabase.table("leo_memories").insert({
                "user_id": user_id,
                "task": task,
                "final_answer": final_answer,
                "success": success,
                "created_at": time.time(),
            }).execute()
        except Exception as e:
            print(f"Memory write failed: {e}")
        return

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
    if IS_PRODUCTION:
        try:
            supabase = get_supabase()
            result = supabase.table("leo_memories") \
                .select("task, final_answer, success, created_at") \
                .eq("user_id", user_id) \
                .execute()
            rows = result.data or []
            if not rows:
                return []

            query_kw = _keywords(task)
            scored = []
            for row in rows:
                row_kw = _keywords(row.get("task", ""))
                overlap = len(query_kw & row_kw)
                if overlap > 0:
                    scored.append((overlap, row))

            scored.sort(key=lambda x: x[0], reverse=True)
            return [row for _score, row in scored[:n]]
        except Exception as e:
            print(f"Memory recall failed: {e}")
            return []

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
    if IS_PRODUCTION:
        try:
            supabase = get_supabase()
            result = supabase.table("leo_memories") \
                .select("id", count="exact") \
                .eq("user_id", user_id) \
                .execute()
            return {"total_tasks_remembered": result.count or 0}
        except Exception:
            return {"total_tasks_remembered": 0}

    try:
        return {"total_tasks_remembered": get_collection(user_id).count()}
    except Exception:
        return {"total_tasks_remembered": 0}
