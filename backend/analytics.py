import sqlite3
import json
import time
import os
from datetime import datetime, timedelta
from typing import Optional

# Store DB next to this file so it survives system restarts (unlike /tmp)
DB_PATH = os.path.join(os.path.dirname(__file__), "leo_analytics.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id          TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL,
            task        TEXT NOT NULL,
            language    TEXT,
            status      TEXT NOT NULL,
            steps_taken INTEGER DEFAULT 0,
            max_steps   INTEGER DEFAULT 10,
            duration_ms INTEGER DEFAULT 0,
            tools_used  TEXT DEFAULT '[]',
            model       TEXT DEFAULT 'gemini-1.5-flash',
            input_chars INTEGER DEFAULT 0,
            output_chars INTEGER DEFAULT 0,
            created_at  REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tool_calls (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id     TEXT NOT NULL,
            user_id     TEXT NOT NULL,
            tool_name   TEXT NOT NULL,
            success     INTEGER DEFAULT 1,
            duration_ms INTEGER DEFAULT 0,
            created_at  REAL NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        );

        CREATE TABLE IF NOT EXISTS daily_stats (
            date        TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL,
            tasks_total INTEGER DEFAULT 0,
            tasks_success INTEGER DEFAULT 0,
            tasks_error INTEGER DEFAULT 0,
            tool_calls  INTEGER DEFAULT 0,
            total_duration_ms INTEGER DEFAULT 0,
            estimated_cost_usd REAL DEFAULT 0.0
        );
    """)
    conn.commit()
    conn.close()


# Initialize on import
init_db()


# ── Cost estimation ────────────────────────────────────────────

INPUT_COST_PER_1M  = 0.075
OUTPUT_COST_PER_1M = 0.30
CHARS_PER_TOKEN    = 4


def estimate_cost(input_chars: int, output_chars: int) -> float:
    """Estimate Gemini API cost in USD."""
    input_tokens  = input_chars / CHARS_PER_TOKEN
    output_tokens = output_chars / CHARS_PER_TOKEN
    cost = (input_tokens / 1_000_000 * INPUT_COST_PER_1M +
            output_tokens / 1_000_000 * OUTPUT_COST_PER_1M)
    return round(cost, 6)


# ── Logging ───────────────────────────────────────────────────

def log_task(
    task_id: str,
    user_id: str,
    task: str,
    status: str,
    steps_taken: int,
    max_steps: int,
    duration_ms: int,
    tools_used: list,
    language: Optional[str] = None,
    input_chars: int = 0,
    output_chars: int = 0,
):
    """Log a completed task."""
    try:
        conn = get_db()
        cost = estimate_cost(input_chars, output_chars)
        today = datetime.now().strftime("%Y-%m-%d")

        conn.execute("""
            INSERT OR REPLACE INTO tasks
            (id, user_id, task, language, status, steps_taken, max_steps,
             duration_ms, tools_used, input_chars, output_chars, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id, user_id, task[:200], language, status,
            steps_taken, max_steps, duration_ms,
            json.dumps(tools_used), input_chars, output_chars, time.time()
        ))

        conn.execute("""
            INSERT INTO daily_stats (date, user_id, tasks_total, tasks_success,
                tasks_error, total_duration_ms, estimated_cost_usd)
            VALUES (?, ?, 1, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                tasks_total = tasks_total + 1,
                tasks_success = tasks_success + ?,
                tasks_error = tasks_error + ?,
                total_duration_ms = total_duration_ms + ?,
                estimated_cost_usd = estimated_cost_usd + ?
        """, (
            today, user_id,
            1 if status == "success" else 0,
            1 if status == "error" else 0,
            duration_ms, cost,
            1 if status == "success" else 0,
            1 if status == "error" else 0,
            duration_ms, cost,
        ))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Analytics log failed: {e}")


def log_tool_call(
    task_id: str,
    user_id: str,
    tool_name: str,
    success: bool,
    duration_ms: int = 0,
):
    """Log a single tool call."""
    try:
        conn = get_db()
        conn.execute("""
            INSERT INTO tool_calls (task_id, user_id, tool_name, success, duration_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (task_id, user_id, tool_name, 1 if success else 0, duration_ms, time.time()))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Tool call log failed: {e}")


# ── Queries ───────────────────────────────────────────────────

def get_overview(user_id: str, days: int = 30) -> dict:
    """Get high-level stats for the last N days."""
    conn = get_db()
    since = time.time() - (days * 86400)

    tasks = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
            SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error,
            AVG(duration_ms) as avg_duration_ms,
            AVG(steps_taken) as avg_steps,
            SUM(input_chars + output_chars) as total_chars
        FROM tasks
        WHERE user_id = ? AND created_at >= ?
    """, (user_id, since)).fetchone()

    tool_calls = conn.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success
        FROM tool_calls
        WHERE user_id = ? AND created_at >= ?
    """, (user_id, since)).fetchone()

    cost = conn.execute("""
        SELECT SUM(estimated_cost_usd) as total
        FROM daily_stats
        WHERE user_id = ?
        AND date >= date('now', ?)
    """, (user_id, f'-{days} days')).fetchone()

    conn.close()

    total = tasks["total"] or 0
    success = tasks["success"] or 0

    return {
        "period_days": days,
        "tasks": {
            "total": total,
            "success": success,
            "error": tasks["error"] or 0,
            "pass_rate": round(success / total * 100, 1) if total else 0,
        },
        "performance": {
            "avg_duration_seconds": round((tasks["avg_duration_ms"] or 0) / 1000, 1),
            "avg_steps": round(tasks["avg_steps"] or 0, 1),
        },
        "tool_calls": {
            "total": tool_calls["total"] or 0,
            "success": tool_calls["success"] or 0,
            "success_rate": round(
                (tool_calls["success"] or 0) / (tool_calls["total"] or 1) * 100, 1
            ),
        },
        "cost": {
            "estimated_usd": round(cost["total"] or 0, 4),
            "per_task_avg": round((cost["total"] or 0) / max(total, 1), 5),
        },
    }


def get_daily_activity(user_id: str, days: int = 14) -> list:
    """Get daily task counts for a sparkline/bar chart."""
    conn = get_db()
    rows = conn.execute("""
        SELECT date, tasks_total, tasks_success, tasks_error,
               total_duration_ms, estimated_cost_usd
        FROM daily_stats
        WHERE user_id = ?
        AND date >= date('now', ?)
        ORDER BY date ASC
    """, (user_id, f'-{days} days')).fetchall()
    conn.close()

    result = {}
    for i in range(days):
        d = (datetime.now() - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        result[d] = {
            "date": d,
            "total": 0, "success": 0, "error": 0,
            "duration_ms": 0, "cost": 0.0
        }

    for row in rows:
        result[row["date"]] = {
            "date": row["date"],
            "total": row["tasks_total"],
            "success": row["tasks_success"],
            "error": row["tasks_error"],
            "duration_ms": row["total_duration_ms"],
            "cost": row["estimated_cost_usd"],
        }

    return list(result.values())


def get_top_tools(user_id: str, days: int = 30) -> list:
    """Get most used tools with success rates."""
    conn = get_db()
    rows = conn.execute("""
        SELECT
            tool_name,
            COUNT(*) as total,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success,
            AVG(duration_ms) as avg_duration_ms
        FROM tool_calls
        WHERE user_id = ? AND created_at >= ?
        GROUP BY tool_name
        ORDER BY total DESC
        LIMIT 10
    """, (user_id, time.time() - days * 86400)).fetchall()
    conn.close()

    return [
        {
            "tool": row["tool_name"],
            "total": row["total"],
            "success": row["success"],
            "success_rate": round(row["success"] / row["total"] * 100, 1),
            "avg_duration_ms": round(row["avg_duration_ms"] or 0),
        }
        for row in rows
    ]


def get_recent_tasks(user_id: str, limit: int = 20) -> list:
    """Get most recent tasks with their details."""
    conn = get_db()
    rows = conn.execute("""
        SELECT id, task, language, status, steps_taken,
               max_steps, duration_ms, tools_used, created_at
        FROM tasks
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (user_id, limit)).fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "task": row["task"],
            "language": row["language"],
            "status": row["status"],
            "steps_taken": row["steps_taken"],
            "max_steps": row["max_steps"],
            "duration_seconds": round((row["duration_ms"] or 0) / 1000, 1),
            "tools_used": json.loads(row["tools_used"] or "[]"),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def get_language_breakdown(user_id: str, days: int = 30) -> list:
    """Get breakdown of tasks by programming language."""
    conn = get_db()
    rows = conn.execute("""
        SELECT
            COALESCE(language, 'general') as language,
            COUNT(*) as total,
            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success
        FROM tasks
        WHERE user_id = ? AND created_at >= ?
        GROUP BY language
        ORDER BY total DESC
    """, (user_id, time.time() - days * 86400)).fetchall()
    conn.close()

    return [
        {
            "language": row["language"],
            "total": row["total"],
            "success": row["success"],
            "pass_rate": round(row["success"] / row["total"] * 100, 1),
        }
        for row in rows
    ]
