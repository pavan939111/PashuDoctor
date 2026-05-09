import httpx
import time
from functools import lru_cache

@lru_cache(maxsize=1)
def is_online() -> bool:
    """Checks for internet connectivity by pinging Google DNS"""
    try:
        # Use a short timeout to prevent blocking the UI/API
        with httpx.Client(timeout=2.0) as client:
            client.get("https://8.8.8.8")
            return True
    except Exception:
        return False

def get_connectivity_status() -> dict:
    online = is_online()
    return {
        "online": online,
        "status": "Connected" if online else "Offline Mode — Limited features",
        "timestamp": time.time()
    }
