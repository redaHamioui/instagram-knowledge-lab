"""All paths in one place. Easy to change later."""
from pathlib import Path

# Project root = two levels up from this file
ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
DB_DIR = DATA_DIR / "db"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"

DB_PATH = DB_DIR / "library.db"


def ensure_dirs() -> None:
    """Create every folder we need if it does not exist."""
    for folder in (RAW_DIR, DB_DIR, KNOWLEDGE_DIR):
        folder.mkdir(parents=True, exist_ok=True)


# Default import mode. "own" = only the user's own posts (BYOP-safe).
# "all" = own + saved + liked (opt-in).
DEFAULT_MODE = "own"
