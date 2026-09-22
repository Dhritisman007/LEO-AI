"""Pings LEO's own /health endpoint periodically to stop Render's free-tier
web service from spinning down due to inactivity. Production only."""
import os
import threading
import time
import requests
from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

PING_INTERVAL_SECONDS = 10 * 60


def _keepalive_loop():
    url = os.getenv("RENDER_EXTERNAL_URL")
    if not url:
        print("keepalive: RENDER_EXTERNAL_URL not set, skipping")
        return

    health_url = url.rstrip("/") + "/health"
    while True:
        time.sleep(PING_INTERVAL_SECONDS)
        try:
            requests.get(health_url, timeout=10)
        except Exception as e:
            print(f"keepalive ping failed: {e}")


def start_keepalive():
    """Start the keepalive background thread. No-op outside production."""
    if not IS_PRODUCTION:
        return
    thread = threading.Thread(target=_keepalive_loop, daemon=True)
    thread.start()
