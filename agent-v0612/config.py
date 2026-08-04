"""
Runtime configuration for the v0612 agent.

All paths are resolved from the repository layout, so the code works whether it
is launched from the repository root, from ``agent-v0612/``, or from a notebook.
Environment variables can override the database paths for experiments.

v0612 变更：
  * 结果数据库默认指向 ``song_bureaucracy_entries_v0612.db``，避免误写 v0304
    主结果库；
  * ``validate_paths()`` 只强制要求辞典数据库存在——结果数据库不存在时由
    ``Database.__init__`` 自动建库建表。
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict


AGENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = AGENT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_DIR = DATA_DIR / "database"

DICT_TABLE = os.getenv("SONG_DICT_TABLE", "chapter8t10")
DICT_DB_PATH = Path(
  os.getenv("SONG_DICT_DB_PATH", str(DATABASE_DIR / "song_bureaucracy_dictionary.db"))
).expanduser()
ENTRY_DB_PATH = Path(
  os.getenv(
    "SONG_ENTRY_DB_PATH",
    str(AGENT_DIR / "records" / "v0613-v4-flash" / "song_bureaucracy_entries_v0613.db"),
  )
).expanduser()


def _derive_run_tag() -> str:
  """推导本次运行的版本标签，用于隔离日志与词条记录目录。

  优先用环境变量 ``SONG_RUN_TAG``；否则从结果库文件名推导
  （``song_bureaucracy_entries_v0612.db`` → ``v0612``），保证不同版本的
  产物落进不同目录，互不覆盖。
  """
  explicit = os.getenv("SONG_RUN_TAG", "").strip()
  if explicit:
    return explicit
  stem = ENTRY_DB_PATH.stem
  m = re.match(r"song_bureaucracy_entries_(.+)$", stem)
  return m.group(1) if m else stem


# 运行版本标签，以及按版本隔离的日志 / 词条记录目录。
RUN_TAG = _derive_run_tag()
LOGS_DIR = AGENT_DIR / "logs"
RECORDS_DIR = AGENT_DIR / "records"
OUTPUT_DIR = Path(os.getenv("SONG_OUTPUT_DIR", str(RECORDS_DIR / RUN_TAG))).expanduser()
# SAVE_DIR 仍是写词条记录（records_*.json、failed_entries.json）的目录。
# 默认是 records/<RUN_TAG>/；run.sh 可通过 SONG_OUTPUT_DIR 指到任意输出目录。
SAVE_DIR = OUTPUT_DIR


def ensure_save_dir() -> Path:
  """创建并返回本版本的词条记录目录 records/<RUN_TAG>/。"""
  SAVE_DIR.mkdir(parents=True, exist_ok=True)
  return SAVE_DIR


def ensure_logs_dir() -> Path:
  """创建并返回日志目录 logs/。"""
  LOGS_DIR.mkdir(parents=True, exist_ok=True)
  return LOGS_DIR


def log_path() -> Path:
  """本版本运行日志的建议落盘路径 logs/<RUN_TAG>.log。"""
  return LOGS_DIR / f"{RUN_TAG}.log"


def validate_paths() -> Dict[str, Path]:
  """Validate required local files and return normalized paths.

  辞典数据库必须存在；结果数据库允许不存在（首次运行时自动创建）。
  """
  required = {
    "dictionary database": DICT_DB_PATH,
    "entry database": ENTRY_DB_PATH,
  }
  if not DICT_DB_PATH.exists():
    raise FileNotFoundError(f"缺少运行所需文件:\ndictionary database: {DICT_DB_PATH}")
  if not ENTRY_DB_PATH.exists():
    print(f"提示：结果数据库不存在，将在首次连接时自动创建: {ENTRY_DB_PATH}")
  return required
