"""
Smoke test for the v0612 agent runtime.

This script does not call the LLM and does not mutate the entry database. It
checks the local macOS-compatible paths, SQLite connectivity, core imports, and
prompt/state plumbing.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from config import DICT_DB_PATH, DICT_TABLE, ENTRY_DB_PATH, validate_paths
from database import Database
from agent_state import AgentState


def main() -> None:
  validate_paths()

  # Database 初始化会执行 CREATE TABLE IF NOT EXISTS。始终在临时副本上测试，
  # 避免 smoke test 触碰真实结果库；配置库不存在时则测试首次建库路径。
  with tempfile.TemporaryDirectory(prefix="song-agent-smoke-") as temp_dir:
    smoke_entry_path = Path(temp_dir) / "entry.db"
    if ENTRY_DB_PATH.exists():
      shutil.copy2(ENTRY_DB_PATH, smoke_entry_path)

    with Database(str(DICT_DB_PATH), DICT_TABLE, str(smoke_entry_path)) as db:
      dict_index = db.get_dictionary_index()
      if isinstance(dict_index, dict) and "error" in dict_index:
        raise RuntimeError(dict_index["error"])
      if not dict_index:
        raise RuntimeError("辞典索引为空")

      state = AgentState(db=db, dict_index_text="\n".join(dict_index))
      state.prepare_new_round()
      state.append_input_entry(dict_index[0])

      prompt_input2facts = state.build_prompt_input2facts()
      if "CURRENT_DICTIONARY_TEXTS" in prompt_input2facts:
        raise RuntimeError("input2facts prompt placeholder was not replaced")

      state.tool_add_atomic_fact(
        "引用信息：smoke test\n  河北兵马大元帅府\n    未明确\n      smoke test fact"
      )
      state.prepare_for_update()
      prompt_facts2data = state.build_prompt_facts2data()
      if "CURRENT_ATOMIC_FACTS" in prompt_facts2data:
        raise RuntimeError("facts2data prompt placeholder was not replaced")

      entity = db.get_entity_by_id(1)

      print("Smoke test OK")
      print(f"Dictionary DB: {DICT_DB_PATH}")
      print(f"Configured Entry DB (not modified): {ENTRY_DB_PATH}")
      print(f"Dictionary entries: {len(dict_index)}")
      if entity is not None:
        print(f"Sample entity #1: {entity['title']} / {entity['type']}")
      else:
        print("Entry DB 为空库（尚未运行批处理），跳过实体抽查")


if __name__ == "__main__":
  main()
