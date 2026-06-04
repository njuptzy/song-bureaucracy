"""
Runtime configuration for the v0303 agent.

All paths are resolved from the repository layout, so the code works whether it
is launched from the repository root, from ``agent_v0303/``, or from a notebook.
Environment variables can override the database paths for experiments.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict


AGENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = AGENT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_DIR = DATA_DIR / "database"
SAVE_DIR = AGENT_DIR / "save"

DICT_TABLE = os.getenv("SONG_DICT_TABLE", "chapter8t10")
DICT_DB_PATH = Path(
  os.getenv("SONG_DICT_DB_PATH", str(DATABASE_DIR / "song_bureaucracy_dictionary.db"))
).expanduser()
ENTRY_DB_PATH = Path(
  os.getenv("SONG_ENTRY_DB_PATH", str(DATABASE_DIR / "song_bureaucracy_entries_v0304.db"))
).expanduser()


def ensure_save_dir() -> Path:
  """Create and return the v0303 save directory."""
  SAVE_DIR.mkdir(parents=True, exist_ok=True)
  return SAVE_DIR


def validate_paths() -> Dict[str, Path]:
  """Validate required local files and return normalized paths."""
  required = {
    "dictionary database": DICT_DB_PATH,
    "entry database": ENTRY_DB_PATH,
  }
  missing = [f"{label}: {path}" for label, path in required.items() if not path.exists()]
  if missing:
    raise FileNotFoundError("缺少运行所需文件:\n" + "\n".join(missing))
  return required
