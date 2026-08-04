#!/usr/bin/env python3
"""宋代官制辞典 → 结构化数据库批跑入口。

跑前请先在 .env 设好 OPENROUTER_API_KEY，并通过 run.sh 设置 SONG_RUN_TAG
（决定结果库 / 日志 / 词条记录的归属版本，详见 run.sh）。
版本修复说明见 README.md。
"""

import os
import sys
import time
import copy
import json
import traceback
from pathlib import Path
from datetime import datetime

AGENT_DIR = Path.cwd()
if not (AGENT_DIR / "database.py").exists():
  AGENT_DIR = Path("agent-v0612").resolve()
if str(AGENT_DIR) not in sys.path:
  sys.path.insert(0, str(AGENT_DIR))

from dotenv import load_dotenv
from llm_client import SimpleLLMClient
from kimi_cli_client import KimiCliClient
from database import Database
from agent_state import AgentState
from config import DICT_DB_PATH, DICT_TABLE, ENTRY_DB_PATH, RUN_TAG, ensure_save_dir, validate_paths


def _parse_int_env(name, default=None):
  value = os.getenv(name, "")
  if value == "":
    return default
  try:
    return int(value)
  except ValueError as exc:
    raise ValueError(f"{name} 必须是整数，当前值为 {value!r}") from exc


def _split_entries(raw):
  """Split comma/newline separated dictionary entry indexes."""
  entries = []
  for chunk in raw.replace("\n", ",").split(","):
    item = chunk.strip()
    if item:
      entries.append(item)
  return entries


def select_todo_entries(dict_index_list):
  """Select dictionary entries from env without editing source code.

  Supported env vars:
    SONG_TODO_ENTRIES: comma/newline separated exact entry indexes, e.g.
      "河北兵马大元帅-482,都督府-483"
    SONG_ENTRY_START: zero-based start offset, default 0
    SONG_ENTRY_LIMIT: number of entries to run, default 25; use "all" for no cap
    SONG_ENTRY_END: zero-based exclusive end offset; overrides LIMIT when set
  """
  explicit = os.getenv("SONG_TODO_ENTRIES", "").strip()
  if explicit:
    wanted = _split_entries(explicit)
    known = set(dict_index_list)
    missing = [entry for entry in wanted if entry not in known]
    if missing:
      raise ValueError("指定词条不在辞典索引中: " + ", ".join(missing))
    return wanted, "指定词条"

  start = _parse_int_env("SONG_ENTRY_START", 0)
  if start < 0:
    raise ValueError("SONG_ENTRY_START 不能小于 0")

  end = _parse_int_env("SONG_ENTRY_END")
  limit_raw = os.getenv("SONG_ENTRY_LIMIT", "25").strip()
  if end is None:
    if limit_raw.lower() in {"", "all", "none", "-1"}:
      end = None
    else:
      limit = _parse_int_env("SONG_ENTRY_LIMIT", 25)
      if limit < 0:
        raise ValueError("SONG_ENTRY_LIMIT 不能小于 0；如需全部运行请设为 all")
      end = start + limit
  elif end < start:
    raise ValueError("SONG_ENTRY_END 不能小于 SONG_ENTRY_START")

  selected = dict_index_list[start:end]
  end_text = "末尾" if end is None else str(end)
  return selected, f"切片 [{start}:{end_text}]"


def acquire_entry_db_lock():
  """Prevent two agent processes from writing the same SQLite DB.

  SQLite can recover from normal crashes, but concurrent long-running writers
  produce persistent "database is locked" failures and misleading model traces.
  Keep a POSIX advisory lock for the whole process lifetime.
  """
  lock_path = Path(str(ENTRY_DB_PATH) + ".agent.lock")
  lock_path.parent.mkdir(parents=True, exist_ok=True)
  lock_file = open(lock_path, "a+", encoding="utf-8")
  try:
    import fcntl
    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
  except BlockingIOError as exc:
    lock_file.seek(0)
    holder = lock_file.read().strip()
    message = (
      "结果库正在被另一个 agent 进程占用，已拒绝启动。\n"
      f"Entry DB: {ENTRY_DB_PATH}\n"
      f"Lock: {lock_path}\n"
    )
    if holder:
      message += f"当前锁信息:\n{holder}\n"
    message += "请先结束旧进程，或换一个 --db/--out 后再启动。"
    raise RuntimeError(message) from exc
  except Exception:
    lock_file.close()
    raise

  lock_file.seek(0)
  lock_file.truncate()
  lock_file.write(
    f"pid={os.getpid()}\n"
    f"started_at={datetime.now().isoformat(timespec='seconds')}\n"
    f"entry_db={ENTRY_DB_PATH}\n"
    f"run_tag={RUN_TAG}\n"
  )
  lock_file.flush()
  return lock_file


load_dotenv()
# LLM 接入方式：默认走 HTTP（SimpleLLMClient → DeepSeek 等 OpenAI 兼容端点）。
# 设 USE_KIMI_CLI=1 切换到子进程模式，调本机已登录的 kimi-code CLI，
# 由它用自己的合法身份完成 Kimi For Coding 的协议握手（OAuth + 动态签名等）。
if os.getenv("USE_KIMI_CLI") == "1":
  kimi_model = os.getenv("KIMI_CLI_MODEL")  # 不设则用 kimi-cli 默认（kimi-code/kimi-for-coding）
  llm = KimiCliClient(model=kimi_model, max_retries=3)
  print(f"Model: kimi-cli({kimi_model or 'default'}) @ {llm.kimi_bin}")
else:
  # 默认走 HTTP（SimpleLLMClient）。模型/key/base_url/max_tokens 由
  # SimpleLLMClient 内部按 LLM_PROFILE 解析对应的 <PROFILE>_* 环境变量。
  # 临时切换 provider：./run.sh --provider <name> ...
  # 新增 provider：在 .env 加一段 <NAME>_API_KEY/<NAME>_BASE_URL/<NAME>_MODEL/<NAME>_MAX_TOKENS。
  llm = SimpleLLMClient(max_retries=3)
  print(f"Model: {llm.model}  (profile: {llm.profile.lower()})")

validate_paths()
SAVE_DIR = ensure_save_dir()
_ENTRY_DB_LOCK = acquire_entry_db_lock()
db = Database(str(DICT_DB_PATH), DICT_TABLE, str(ENTRY_DB_PATH))
print(f"Run tag: {RUN_TAG}")
print(f"Dictionary DB: {DICT_DB_PATH}")
print(f"Entry DB: {ENTRY_DB_PATH}")
print(f"Output dir: {SAVE_DIR}")

start_time = time.time()
dict_index_list = db.get_dictionary_index()
dict_index_text = "\n".join(dict_index_list)
state = AgentState(db=db, dict_index_text=dict_index_text)
todo_dict_entries, todo_desc = select_todo_entries(dict_index_list)
# 用辞典全局 index 给 records 文件命名，让续跑/单跑/重跑的编号都对齐辞典里
# 那个词条的全局位置（records_1 = 辞典里第 1 个，records_26 = 第 26 个），
# 而不是按本批跑的 0-based 序号命名（那样续跑会跟前面撞号）。
entry_global_index = {name: idx for idx, name in enumerate(dict_index_list)}
print(f"Todo selection: {todo_desc}")
print(f"Todo count: {len(todo_dict_entries)}")
if todo_dict_entries:
  print(f"First entry: {todo_dict_entries[0]}")
  print(f"Last entry: {todo_dict_entries[-1]}")

failed_entries = []

tools_input2facts = {
  "search_dictionary": state.tool_search_dictionary,
  "add_atomic_fact": state.tool_add_atomic_fact,
  "remove_atomic_fact": state.tool_remove_atomic_fact,
  "update_atomic_fact": state.tool_update_atomic_fact,
}

tools_facts2data = {
  "get_entity": state.tool_get_entity,
  "create_entity": state.tool_create_entity,
  "create_timepoint": state.tool_create_timepoint,
  "update_timepoint_attr": state.tool_update_timepoint_attr,
  "create_timepoints_relationship": state.tool_create_timepoints_relationship,
  "upsert_entity_timepoint": state.tool_upsert_entity_timepoint,
  "upsert_relationship": state.tool_upsert_relationship,
  "append_citation": state.tool_append_citation
}

# 保留较高上限兼容异常复杂词条；正常路径优先用复合工具压缩必要轮次，
# 并靠 "Tasks All Finished" 提前结束。
MAX_llm_loop_count = 40
# LLM 服务持续故障（503 等）时，词条级重试的等待时间与次数。
ENTRY_RETRY_WAIT_SECONDS = 120
ENTRY_MAX_ATTEMPTS = 2


def run_stage(stage_name, prompt_builder, tools, finished_attr, prompt_records):
  """运行一个 Thought/Action/Observation 阶段，统一两阶段循环控制。"""
  for loop_count in range(1, MAX_llm_loop_count + 1):
    prompt = prompt_builder()
    prompt_records.append(prompt)
    print("=" * 30, f"{stage_name} · 第 {loop_count} 轮", "=" * 30)
    print("=" * 20, "CoT", "=" * 20)
    print(state.cot.get_merged_text())

    content_text = llm.chat(prompt)
    finished = state.parse_cot(content_text, tools)
    setattr(state, finished_attr, finished)
    if finished:
      return loop_count

  raise RuntimeError(f"{stage_name}达到 {MAX_llm_loop_count} 轮仍未完成")


def process_entry(global_idx, entry_index):
  """处理单个词条的两阶段循环，成功后写入 records 文件。"""
  entry_start_time = time.time()

  # 一个词条的阶段 2 写库必须整体成功；若中途异常，回滚该词条所有写入。
  with db.entry_transaction():
    records = {
      "input2facts": {},
      "facts2data": {},
    }

    state.prepare_new_round()
    state.append_input_entry(entry_index)
    records["input2facts"]["prompts"] = []

    input2facts_rounds = run_stage(
      "阶段 1",
      state.build_prompt_input2facts,
      tools_input2facts,
      "finished_facts",
      records["input2facts"]["prompts"],
    )

    print("=" * 30, "Result", "=" * 30)
    print("=" * 20, "CoT", "=" * 20)
    print(state.cot.get_merged_text())
    print("=" * 20, "Atomic Facts", "=" * 20)
    print(state.atomic_facts.get_merged_text())

    records["input2facts"]["cot"] = copy.deepcopy(state.cot.chain)
    records["input2facts"]["atomic_facts"] = copy.deepcopy(state.atomic_facts.get_merged_text())

    state.prepare_for_update()
    records["facts2data"]["prompts"] = []

    facts2data_rounds = run_stage(
      "阶段 2",
      state.build_prompt_facts2data,
      tools_facts2data,
      "finished_update",
      records["facts2data"]["prompts"],
    )

    print("=" * 30, "Result", "=" * 30)
    print("=" * 20, "CoT", "=" * 20)
    print(state.cot.get_merged_text())
    print("=" * 20, "Related Data Items", "=" * 20)
    print(state.loaded_data_items.get_merged_text())

    records["facts2data"]["cot"] = copy.deepcopy(state.cot.chain)
    records["facts2data"]["loaded_data_items"] = copy.deepcopy(state.loaded_data_items.get_merged_text())
    records["rounds"] = {
      "input2facts": input2facts_rounds,
      "facts2data": facts2data_rounds,
      "total": input2facts_rounds + facts2data_rounds,
    }

    entry_end_time = time.time()
    print(f"词条 {entry_index} 处理完成，用时 {entry_end_time - entry_start_time} 秒")

    with open(SAVE_DIR / f"records_{global_idx + 1}_{entry_index}.json", "w") as f:
      json.dump(records, f, indent=2, ensure_ascii=False)


for i, entry_index in enumerate(todo_dict_entries):
  global_idx = entry_global_index[entry_index]
  # 本批跑里第 i+1 个 / 辞典里第 global_idx+1 个，两者都打出来方便对照。
  print("=" * 40, f"本批第 {i+1} 个 / 辞典第 {global_idx + 1} 个：{entry_index}", "=" * 40)
  for attempt in range(1, ENTRY_MAX_ATTEMPTS + 1):
    try:
      process_entry(global_idx, entry_index)
      break
    except Exception as e:
      err_trace = traceback.format_exc()
      is_llm_outage = "LLM 调用在" in str(e)
      if is_llm_outage and attempt < ENTRY_MAX_ATTEMPTS:
        print(f"词条 {entry_index} 因 LLM 服务异常失败（第 {attempt} 次尝试）：{e}")
        print(f"等待 {ENTRY_RETRY_WAIT_SECONDS} 秒后重试该词条")
        time.sleep(ENTRY_RETRY_WAIT_SECONDS)
        continue
      print(f"词条 {entry_index} 处理失败，错误信息：{e}")
      print(err_trace)
      failed_entries.append({
        "index": global_idx + 1,
        "entry": entry_index,
        "error": str(e),
        "traceback": err_trace,
      })
      break

end_time = time.time()
print(f"所有词条处理完成，用时 {end_time - start_time} 秒")
print(f"处理失败词条 {len(failed_entries)} 个:")
for item in failed_entries:
  print(f"  {item['entry']}: {item['error']}")

if failed_entries:
  failed_path = SAVE_DIR / "failed_entries.json"
  with open(failed_path, "w") as f:
    json.dump(failed_entries, f, indent=2, ensure_ascii=False)
  print(f"失败词条详情已写入 {failed_path}")
