import httpx
from functools import lru_cache

@lru_cache(maxsize=1)
def is_online() -> bool:
    """Checks for internet connectivity by pinging Google DNS"""
    try:
        # Use a short timeout to prevent blocking the UI
        with httpx.Client(timeout=1.5) as client:
            client.get("https://8.8.8.8")
            return True
    except Exception:
        return False
