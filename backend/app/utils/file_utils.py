from pathlib import Path
import uuid


def unique_filename(original: str) -> str:
    suffix = Path(original).suffix
    return f"{uuid.uuid4()}{suffix}"


def ensure_dir(path: str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
