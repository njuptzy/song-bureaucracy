"""
Smoke test for the v0303 agent runtime.

This script does not call the LLM and does not mutate the entry database. It
checks the local macOS-compatible paths, SQLite connectivity, core imports, and
prompt/state plumbing.
"""

from __future__ import annotations

from config import DICT_DB_PATH, DICT_TABLE, ENTRY_DB_PATH, validate_paths
from database import Database
from agent_state import AgentState


def main() -> None:
  validate_paths()

  with Database(str(DICT_DB_PATH), DICT_TABLE, str(ENTRY_DB_PATH)) as db:
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
    if entity is None:
      raise RuntimeError("结构化结果库缺少 id=1 的实体")

    print("Smoke test OK")
    print(f"Dictionary DB: {DICT_DB_PATH}")
    print(f"Entry DB: {ENTRY_DB_PATH}")
    print(f"Dictionary entries: {len(dict_index)}")
    print(f"Sample entity #1: {entity['title']} / {entity['type']}")


if __name__ == "__main__":
  main()
