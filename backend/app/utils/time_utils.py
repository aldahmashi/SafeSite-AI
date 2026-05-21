from datetime import datetime


def format_timestamp(seconds: float) -> str:
    """Convert float seconds to HH:MM:SS.mmm string."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def utc_now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"
