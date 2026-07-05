import time
from collections import defaultdict
from fastapi import HTTPException

# Config
MAX_REQUESTS = 5       # per user
WINDOW_SECONDS = 60    # per minute

# In-memory store: user_id -> list of timestamps
_request_log: dict = defaultdict(list)


def check_rate_limit(user_id: str):
    """
    Raises HTTP 429 if user has exceeded the rate limit.
    Call this at the start of any expensive endpoint.
    """
    now = time.time()
    window_start = now - WINDOW_SECONDS

    # Remove timestamps outside the window
    _request_log[user_id] = [
        t for t in _request_log[user_id] if t > window_start
    ]

    count = len(_request_log[user_id])

    if count >= MAX_REQUESTS:
        oldest = _request_log[user_id][0]
        retry_in = int(WINDOW_SECONDS - (now - oldest)) + 1
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": f"You've sent {count} tasks in the last minute. Wait {retry_in}s before trying again.",
                "retry_after_seconds": retry_in
            }
        )

    # Log this request
    _request_log[user_id].append(now)


def rate_limit_status(user_id: str) -> dict:
    """Return current usage for a user — useful for UI display."""
    now = time.time()
    window_start = now - WINDOW_SECONDS
    recent = [t for t in _request_log[user_id] if t > window_start]
    return {
        "used": len(recent),
        "limit": MAX_REQUESTS,
        "window_seconds": WINDOW_SECONDS,
        "remaining": max(0, MAX_REQUESTS - len(recent))
    }
