"""Dedup state. seen.json holds IDs of items already delivered.

The file is committed back to the repo by GitHub Actions so dedup survives
across daily runs without external storage.
"""
import json
from pathlib import Path

SEEN_FILE = Path(__file__).parent / "seen.json"
MAX_KEEP = 2000  # cap so the file doesn't grow forever


def load_seen() -> set[str]:
    if not SEEN_FILE.exists():
        return set()
    try:
        return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return set()


def save_seen(seen: set[str]) -> None:
    # Keep the most recent IDs only (sets are unordered, so just slice).
    trimmed = list(seen)[-MAX_KEEP:]
    SEEN_FILE.write_text(json.dumps(trimmed, indent=0), encoding="utf-8")


def filter_new(items: list[dict], seen: set[str]) -> list[dict]:
    """Return only items whose 'id' isn't in seen."""
    return [item for item in items if item["id"] not in seen]
