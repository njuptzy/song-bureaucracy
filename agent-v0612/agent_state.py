"""
Agent 运行时状态管理。

职责：
  * 持有 Database 实例，作为长期记忆（辞典数据 + 实体数据表）的统一入口；
  * 整个生命周期中的短期记忆 / 上下文：（外圈上下文）
      - Dict_Index：《辞典》索引：标题-页码；
      - Dict_TODO：《辞典》待处理列表；
  * 单轮处理过程中的短期记忆 / 上下文：（内圈上下文）
      - Loaded_Dict_Entries：已经获取的辞典词条信息；
      - Loaded_Data_Items：已知的（主动获取或更新后的）数据项信息；
      - Atomic_Facts：原子事实列表；
      - CoT： Thought-Action-Observation 思维链记录；
  * 代理状态记录 Logs 记录关键事件

本模块只负责状态结构与更新接口，不直接调用 LLM，方便在 notebook 或脚本中组合使用。
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
import re
from typing import Any, Dict, List, Optional, TypedDict, Callable

from database import Database
from utils import (
  search_dictionary,
  dict_entry_to_str,
  get_entity,
  entity_to_str,
  create_entity,
  create_timepoint,
  update_timepoint_attr,
  create_timepoints_relationship,
  upsert_entity_timepoint,
  upsert_relationship,
  append_citation,
  load_json_string
)
from prompt_input2facts import build_input2facts_prompt
from prompt_facts2data import build_facts2data_prompt


# ============================================================================
# 上下文压缩开关
#
# 整套压缩只影响"发给模型的 prompt"，不影响落盘 records 字段。
# 主开关 SONG_COMPACT_CONTEXT=1 时，所有子开关默认随主开关；
# 任何子开关可以单独显式覆盖（"0" 或 "1"）。
# ============================================================================

def _env_truthy(name: str, default: Optional[bool] = None) -> Optional[bool]:
  """读环境变量并解析为 True/False/None。默认值 None 表示"未显式设置"。"""
  raw = os.getenv(name)
  if raw is None or raw == "":
    return default
  return raw.strip().lower() in ("1", "true", "yes", "on")


def _resolve_compact_flags() -> Dict[str, Any]:
  """解析压缩开关。默认压缩重复详情和历史，但保留完整索引。"""
  master = _env_truthy("SONG_COMPACT_CONTEXT", default=None)

  def child_default(default: bool) -> bool:
    return default if master is None else master

  return {
    "entity_index": _env_truthy(
      "SONG_COMPACT_ENTITY_INDEX", default=child_default(False)
    ),
    "entity_details": _env_truthy(
      "SONG_COMPACT_ENTITY_DETAILS", default=child_default(True)
    ),
    "history": _env_truthy(
      "SONG_COMPACT_HISTORY", default=child_default(True)
    ),
    "history_turns": int(os.getenv("SONG_COMPACT_HISTORY_TURNS", "2") or "2"),
    "dict_index": _env_truthy(
      "SONG_COMPACT_DICT_INDEX", default=child_default(False)
    ),
  }


# 候选实体召回上限
_COMPACT_CANDIDATE_PER_SEED = 8
_COMPACT_CANDIDATE_TOTAL = 40
_MAX_ATOMIC_FACTS_PER_ACTION = 4
_MAX_FACTS2DATA_CALLS_PER_ACTION = 4
# 从 atomic_facts 文本里提取实体名的正则：
# 原子事实里实体行格式形如 "  河北兵马大元帅府, 河北兵马大元帅"（2 空格缩进）
_FACT_ENTITY_LINE_RE = re.compile(r"^  ([^\s].*?)$", re.MULTILINE)

@dataclass
class DictionaryContext:
  entries: Dict[str, Dict[str, Any]] = field(default_factory=dict)
  texts: Dict[str, str] = field(default_factory=dict)

  def new_queried(self, title: str, page: str, entry: Dict[str, Any]) -> None:
    key = f"{title}-{page}"
    self.entries[key] = entry
    self.texts[key] = dict_entry_to_str(entry)

  def get_merged_text(self) -> str:
    return "\n".join(self.texts.values())

@dataclass
class DataItemContext:
  items: Dict[str, Dict[str, Any]] = field(default_factory=dict)
  texts: Dict[str, str] = field(default_factory=dict)

  def update_item(self, item_id: str, item: Dict[str, Any]) -> None:
    self.items[item_id] = item
    self.texts[item_id] = entity_to_str(item)

  def get_merged_text(self) -> str:
    return "\n".join(self.texts.values())

  def get_compact_text(self) -> str:
    """compact 模式：每次重新用 entity_to_str(detail_level='compact') 渲染。

    self.items 仍保留 full 视图（供落盘和 update_item 增量写入），这里只是
    临时重渲染发给模型的版本，不修改任何状态。
    """
    return "\n".join(
      entity_to_str(item, detail_level="compact") for item in self.items.values()
    )

@dataclass
class AtomicFactsContext:
  index: int = 0
  facts: Dict[str, str] = field(default_factory=dict)

  def new_fact(self, fact: str) -> str:
    self.index += 1
    fact_id = str(self.index)
    self.facts[fact_id] = fact
    return fact_id

  def update_fact(self, fact_id: str, fact: str) -> None:
    self.facts[fact_id] = fact

  def remove_fact(self, fact_id: str) -> None:
    del self.facts[fact_id]

  def get_merged_text(self) -> str:
    # 按 fact_id 数值顺序拼接，方便人工阅读和模型定位
    sorted_items = sorted(self.facts.items(), key=lambda kv: int(kv[0]))
    return "\n".join(v for _, v in sorted_items)

class CoTItem(TypedDict):
  role: str
  type: str
  content: str

@dataclass
class CoTContext:
  chain: List[CoTItem] = field(default_factory=list)

  def add_item(self, item: CoTItem) -> None:
    self.chain.append(item)

  def get_merged_text(self) -> str:
    contexts = []
    for idx, item in enumerate(self.chain):
      contexts.append(f"#{idx+1:>5d}: {item["role"]}'s {item["type"]}\n{item["content"]}\n")
    return "\n".join(contexts)

  def get_compact_text(self, recent_turns: int = 2) -> str:
    """compact 模式：把链条按"轮次"（thought→action[→observation]）切分，
    最近 recent_turns 轮原文保留，更早的轮次每个折成 2~3 行摘要。

    摘要保留：thought 首句（≤40 字）+ action 段里的工具调用名和关键 id 参数；
    舍弃 quotation/citation 原文（这些值已经写进库，prompt 里无需重复出现）。
    """
    if recent_turns < 0:
      recent_turns = 0
    # 把 chain 切成 turn 块：每个 turn 以 thought 起、到下一个 thought 之前结束
    turns: List[List[CoTItem]] = []
    cur: List[CoTItem] = []
    for item in self.chain:
      if item["type"] == "thought" and cur:
        turns.append(cur)
        cur = [item]
      else:
        cur.append(item)
    if cur:
      turns.append(cur)

    if not turns:
      return ""

    head = turns[:-recent_turns] if recent_turns > 0 else turns
    tail = turns[-recent_turns:] if recent_turns > 0 else []
    if recent_turns == 0:
      head = turns
      tail = []

    pieces: List[str] = []
    for idx, turn in enumerate(head):
      pieces.append(self._summarize_turn(idx + 1, turn))

    # 最近 recent_turns 轮：原文输出，沿用 get_merged_text 风格但只针对 tail
    base_idx = len(head)
    for offset, turn in enumerate(tail):
      for sub_offset, item in enumerate(turn):
        absolute = base_idx + offset + 1
        # 子项编号沿用全局位置参考，保持人类可读
        pieces.append(
          f"#{absolute:>5d}.{sub_offset}: {item['role']}'s {item['type']}\n{item['content']}\n"
        )

    return "\n".join(pieces)

  @staticmethod
  def _summarize_turn(turn_no: int, turn: List[CoTItem]) -> str:
    """把单个 turn 折成 1~2 行摘要，舍弃 quotation/citation 原文。"""
    thought_summary = ""
    action_summary = ""
    for item in turn:
      content = item.get("content", "")
      if item["type"] == "thought" and not thought_summary:
        # 取首句 / 前 40 字
        first_seg = re.split(r"[。！？\n]", content, maxsplit=1)[0]
        thought_summary = first_seg.strip()[:40]
      elif item["type"] == "action":
        # 从工具调用文本里抽出 'tool(关键参数)' 简要形式
        action_summary = _summarize_action_text(content)
    head_line = f"#{turn_no} thought: {thought_summary}" if thought_summary else f"#{turn_no}"
    if action_summary:
      return f"{head_line} → {action_summary}"
    return head_line


# 阶段 2 中需要保留的关键参数 key（其余如 citation/quotation/note 在摘要中省略）
_ACTION_KEEP_PARAMS = (
  "entity_id", "timepoint_id", "timepoint_id_1", "timepoint_id_2",
  "target_table", "target_id", "succ_timepoint_id",
  "title", "type", "relation_type", "staff_quota", "staff_type",
  "attr_key", "fact_id", "subject_title", "subject_type", "subject_time",
  "object_title", "object_type", "object_time", "subject_event", "object_event",
)

_ENTITY_DEPENDENT_TOOLS = {
  "get_entity",
  "create_timepoint",
  "update_timepoint_attr",
  "create_timepoints_relationship",
  "append_citation",
}

def _summarize_action_text(content: str) -> str:
  """从 'call_tool' 返回拼接出的 action 文本里抽出 tool(关键参数) 简要形式。"""
  if content == "Tasks All Finished":
    return "Tasks All Finished"
  out_calls: List[str] = []
  for line in content.splitlines():
    line = line.strip()
    if not line.startswith("调用工具："):
      continue
    # "调用工具：xxx(k1=v1, k2=v2, ...)"
    after = line[len("调用工具："):]
    m = re.match(r"([^\(]+)\((.*)\)\s*$", after)
    if not m:
      out_calls.append(after[:40])
      continue
    name = m.group(1).strip()
    params_blob = m.group(2)
    # 粗解析：按 ", " 切，每个再按 = 切。citation/quotation 等长字符串很容易包含 ", "，
    # 但只关心 keep_params 的简单值，遇到截断也无所谓。
    kept = []
    for p in params_blob.split(", "):
      if "=" not in p:
        continue
      k, v = p.split("=", 1)
      k = k.strip()
      if k in _ACTION_KEEP_PARAMS:
        kept.append(f"{k}={v.strip()[:30]}")
    out_calls.append(f"{name}({', '.join(kept)})")
  return "; ".join(out_calls) if out_calls else content[:60]

@dataclass
class AgentState:
  db: Database
  dict_index_text: str
  loaded_dict_entries: Dict[str, Dict[str, Any]]
  loaded_data_items: Dict[str, Dict[str, Any]]
  atomic_facts: Dict[str, Any]
  cot: CoTContext
  """Flag 标记，对应两轮处理：原子事实提取完毕 和 数据项更新完毕"""
  finished_facts: bool = False
  finished_update: bool = False

  def __init__(self, db: Database, dict_index_text: str):
    self.db = db
    self.dict_index_text = dict_index_text
    # 同一阶段内"完全相同的工具调用"计数，用于检测 LLM 决策死循环
    self._repeat_call_counts: Dict[str, int] = {}

  def prepare_new_round(self):
    """
    准备处理新的辞典输入词条
    """
    self.loaded_dict_entries = DictionaryContext()
    self.loaded_data_items = DataItemContext()
    self.atomic_facts = AtomicFactsContext()
    self.cot = CoTContext()
    self.finished_facts = False
    self.finished_update = False
    self._repeat_call_counts = {}

  def prepare_for_update(self):
    self.loaded_data_items = DataItemContext()
    self.cot = CoTContext()
    self.finished_update = False
    self._repeat_call_counts = {}

  """
  以下为 State 内置方法，用于在代理流程的不同阶段修改 State 内容
  本质上是 state = tool(state) 的作用
  """

  def append_input_entry(self, entry_index: str):
    title, page = entry_index.rsplit("-", 1)
    ret, _ = self.tool_search_dictionary(title, page)
    if "error" in ret:
      raise ValueError(f"初始化辞典条目输入错误: {ret['error']}")

  def build_prompt_input2facts(self):
    flags = _resolve_compact_flags()
    # 阶段 1 辞典索引：默认全量，开启 SONG_COMPACT_DICT_INDEX 时换成精简说明
    if flags["dict_index"]:
      total = self.dict_index_text.count("\n") + 1 if self.dict_index_text else 0
      dict_index_summary = (
        f"《辞典》共 {total} 条词条。若当前主词条原文出现"
        "\"详见 'XX' 条\"等跳转指引，请用 search_dictionary(title, page) 查询。"
        "完整辞典索引不再列出，跳转目标的页码请直接从原文中读取。"
      )
    else:
      dict_index_summary = self.dict_index_text
    # CoT 历史：默认全量，开启 SONG_COMPACT_HISTORY 时只留最近 N 轮原文
    history_text = (
      self.cot.get_compact_text(flags["history_turns"])
      if flags["history"] else self.cot.get_merged_text()
    )
    prompt = build_input2facts_prompt(
      dictionary_index_summary=dict_index_summary,
      current_dictionary_texts=self.loaded_dict_entries.get_merged_text(),
      current_atomic_facts=self.atomic_facts.get_merged_text(),
      history_summary=history_text,
    )
    return prompt

  def build_prompt_facts2data(self):
    flags = _resolve_compact_flags()
    # 实体索引：默认全量；开启 SONG_COMPACT_ENTITY_INDEX 时按候选筛选
    if flags["entity_index"]:
      entities_index_text = self._build_compact_entity_index()
    else:
      entities_index_text = "\n".join(self.db.get_entities_index())
    if entities_index_text == "":
      entities_index_text = "当前没有创建任何实体"
    # 已加载实体详情：开启 SONG_COMPACT_ENTITY_DETAILS 时换 compact 渲染
    data_items_text = (
      self.loaded_data_items.get_compact_text()
      if flags["entity_details"] else self.loaded_data_items.get_merged_text()
    )
    # CoT 历史：同 input2facts
    history_text = (
      self.cot.get_compact_text(flags["history_turns"])
      if flags["history"] else self.cot.get_merged_text()
    )
    prompt = build_facts2data_prompt(
      entity_index_summary=entities_index_text,
      current_atomic_facts=self.atomic_facts.get_merged_text(),
      current_data_items=data_items_text,
      history_summary=history_text,
    )
    return prompt

  # ============================================================
  # 候选实体筛选（仅在 SONG_COMPACT_ENTITY_INDEX=1 时使用）
  # ============================================================

  def _seed_titles_from_facts(self) -> List[str]:
    """从当前已抽出的原子事实文本里提取实体名（去重，按出现顺序）。"""
    facts_text = self.atomic_facts.get_merged_text()
    seen: Dict[str, None] = {}
    for line_match in _FACT_ENTITY_LINE_RE.finditer(facts_text):
      raw = line_match.group(1).strip()
      # 行内可能是逗号分隔的多个实体名（关系两端 / 别称组）
      for name in re.split(r"[，,]\s*", raw):
        name = name.strip()
        if name and name not in seen:
          seen[name] = None
    return list(seen.keys())

  def _build_compact_entity_index(self) -> str:
    """根据当前原子事实和已加载实体，召回相关候选 + 附加全库统计 + 复用规则强提示。"""
    # 种子来源 1：原子事实文本里出现的实体名
    seed_titles = self._seed_titles_from_facts()
    # 种子来源 2：当前已加载实体（已经 get_entity / create_entity 拿到过的）
    loaded_titles: List[str] = []
    for item in self.loaded_data_items.items.values():
      try:
        title = item.get("entity", {}).get("title")
        if title and title not in seed_titles and title not in loaded_titles:
          loaded_titles.append(title)
      except AttributeError:
        continue

    candidate_ids: Dict[int, None] = {}
    # 已加载实体直接进候选（即使 title 不在库里也无所谓，filtered 会忽略）
    for item in self.loaded_data_items.items.values():
      try:
        eid = int(item.get("entity", {}).get("id"))
        candidate_ids[eid] = None
      except (TypeError, ValueError, AttributeError):
        continue

    # 召回扩展：种子 title 子串匹配
    for seed in seed_titles + loaded_titles:
      for eid in self.db.get_entities_id_by_title_pattern(seed, limit=_COMPACT_CANDIDATE_PER_SEED):
        candidate_ids[eid] = None
        if len(candidate_ids) >= _COMPACT_CANDIDATE_TOTAL:
          break
      if len(candidate_ids) >= _COMPACT_CANDIDATE_TOTAL:
        break

    candidate_lines = self.db.get_entities_index_filtered(list(candidate_ids.keys()))
    total_in_db = len(self.db.get_entities_index())

    if not candidate_lines:
      header = (
        f"[与当前原子事实相关的候选实体：0 个（库内共 {total_in_db} 个实体）]"
      )
      body = "（候选为空。如果你确定要创建新实体，直接调 create_entity；"
      body += "若怀疑应复用某个已有实体，先用 get_entity 验证 ID 后再决定。）"
    else:
      header = (
        f"[与当前原子事实相关的候选实体：{len(candidate_lines)} 个"
        f"（库内共 {total_in_db} 个实体，未列出的实体未必不相关）]"
      )
      body = "\n".join(candidate_lines)

    footer = (
      "[复用 ID 的硬规则不变] 严禁仅凭包含/前缀/简称/相似就复用 ID。"
      "只有 title 完全一致且 type 合理，才可视为同一实体；"
      "其余情况一律按新实体处理。create_entity 在同名同 type 时会自动复用，"
      "请放心调用——若候选列表不全也不会重复创建。"
    )
    return f"{header}\n{body}\n\n{footer}"

  def call_tool(self, call, tools: Dict[str, Callable]):
    """
    根据 call 请求从工具包中调用工具，返回
      * tool_result: 工具调用结果（action）
      * tool_output: 工具调用输出（observation）
    """
    config = {
      "tool": None,
      "parameters": {},
      "status": None,
      "error": None,
      "result": None,
      "output": None,
    }

    def format_param(key: str, value: Any) -> str:
      if key in {"citation", "quotation", "note"}:
        if value in (None, ""):
          return "空"
        return f"<已提供 {len(str(value))} 字>"
      if key == "attributes" and isinstance(value, dict):
        return "{" + ", ".join(sorted(value)) + "}"
      text = str(value)
      return text if len(text) <= 80 else text[:77] + "..."

    def build_return(config):
      result_text = ""
      output_text = ""
      tool_name = config.get("tool", 'unknown')
      params = []
      for key, value in config["parameters"].items():
        params.append(f"{key}={format_param(key, value)}")
      result_text += f"调用工具：{tool_name}({', '.join(params)})\n"
      if config["status"] == "success":
        result_text += "成功"
        if config["result"] is not None:
          result_text += f"：{config['result']}"
      else:
        result_text += "失败"
        if config["error"] is not None:
          result_text += f"：{config['error']}"

      if config.get("repeat_warning"):
        result_text += f"\n{config['repeat_warning']}"

      if config["output"] is not None:
        output_text += f"调用工具：{tool_name}({', '.join(params)}) 输出：\n{config['output']}"

      return [result_text, output_text]

    if not isinstance(call, dict):
      config["status"] = "failed"
      config["error"] = "工具调用格式不正确"
      return build_return(config)

    config["tool"] = call.get("tool", None)
    config["parameters"] = call.get("parameters", {})
    if not config["tool"] or config["tool"] not in tools:
      config["status"] = "failed"
      config["error"] = f"缺少工具名称或工具不存在: {config['tool']}"
      return build_return(config)

    tool_func = tools[config["tool"]]
    try:
      result, output = tool_func(**config["parameters"])
      if isinstance(result, dict) and "error" in result:
        config["status"] = "failed"
        config["error"] = result["error"]
      else:
        config["status"] = "success"
        config["result"] = result
        config["output"] = output
    except Exception as e:
      config["status"] = "failed"
      config["error"] = f"工具调用异常: {str(e)}"

    # 死循环检测：批跑中 LLM 会对模糊判断点反复发起同一调用（如 get_entity
    # 233 次）直到耗尽轮次。对完全相同的调用计数，超过阈值后在反馈中强制提醒。
    try:
      call_key = f"{config['tool']}|{json.dumps(config['parameters'], ensure_ascii=False, sort_keys=True, default=str)}"
    except Exception:
      call_key = f"{config['tool']}|{config['parameters']}"
    count = self._repeat_call_counts.get(call_key, 0) + 1
    self._repeat_call_counts[call_key] = count
    if count >= 3 and config["status"] == "success":
      config["repeat_warning"] = (
        f"【警告】这是你第 {count} 次发起完全相同的调用，重复执行不会带来新信息。"
        "所需信息已在提示词的「已加载数据项」部分，请直接基于现有信息做出决策并执行下一步写入操作；"
        "若确实无法判断，选择最合理的方案并在 note 中说明，不要再重复本调用。"
      )
    return build_return(config)

  def validate_action_batch(self, calls: List[Any], tools: Dict[str, Callable]) -> Optional[str]:
    """Reject same-round entity creation followed by guessed-ID operations.

    create_entity is the only source of truth for the real database ID. When a
    model creates an entity and then mutates entity/timepoint/relationship rows
    in the same Action list, it is usually guessing IDs such as 1 or 2. In long
    batch runs that silently attaches later facts to early entities.

    Timepoint creation is intentionally handled by tool-level loaded-ID checks
    instead of a coarse batch rejection. This allows efficient batches such as
    "create a new timepoint for one loaded entity, and append a citation to a
    different already-loaded timepoint" while still rejecting guessed IDs.
    """
    tool_names = [
      call.get("tool")
      for call in calls
      if isinstance(call, dict)
    ]

    if "add_atomic_fact" in tools:
      add_fact_count = sum(name == "add_atomic_fact" for name in tool_names)
      if add_fact_count > _MAX_ATOMIC_FACTS_PER_ACTION:
        return (
          f"本轮 Action 被拒绝：一次最多调用 {_MAX_ATOMIC_FACTS_PER_ACTION} 次 "
          f"add_atomic_fact，当前包含 {add_fact_count} 次。"
          "请按原文标签和段落顺序只保留接下来的 1–4 条；"
          "等待 Observation 返回后，下一轮从尚未覆盖的位置继续。"
          "不要重复已经出现在「目前已经提取的原子信息」中的事实。"
        )

    if "upsert_entity_timepoint" in tools and len(tool_names) > _MAX_FACTS2DATA_CALLS_PER_ACTION:
      return (
        f"本轮 Action 被拒绝：阶段 2 每轮最多调用 "
        f"{_MAX_FACTS2DATA_CALLS_PER_ACTION} 次工具，当前包含 {len(tool_names)} 次。"
        "请只处理最靠前的 1 条关系事实，或最多 2 条单实体事实；"
        "复杂事实先写端点，下一轮再补关系或额外证据。"
        "不要在一轮中规划或写入整篇词条。"
      )

    if "create_entity" in tools and "create_entity" in tool_names:
      blocked = [
        name for name in tool_names
        if name in _ENTITY_DEPENDENT_TOOLS
      ]
      if blocked:
        blocked_text = "、".join(blocked)
        return (
          "本轮 Action 被拒绝：同一轮中调用 create_entity 后，不能继续调用 "
          f"{blocked_text}。create_entity 返回的真实实体 ID 必须先出现在 Observation 中，"
          "下一轮再基于该 ID 创建时间点、更新属性、建立关系或追加引用。"
          "严禁使用 entity_id=1、timepoint_id=1 这类猜测 ID。"
        )

    loaded_timepoint_ids = self._loaded_timepoint_ids()
    loaded_relationship_ids = self._loaded_relationship_ids()
    for call in calls:
      if not isinstance(call, dict):
        continue
      tool_name = call.get("tool")
      params = call.get("parameters") or {}
      if not isinstance(params, dict):
        continue

      if tool_name == "create_timepoint":
        succ_timepoint_id = params.get("succ_timepoint_id")
        if succ_timepoint_id is not None and str(succ_timepoint_id) not in loaded_timepoint_ids:
          return (
            "本轮 Action 被拒绝：create_timepoint 的 succ_timepoint_id="
            f"{succ_timepoint_id} 在本轮开始时不属于已加载时间点。"
            "插入位置必须基于已加载的旧时间点；不要引用同一 Action 中刚创建或猜测的时间点 ID。"
          )
      elif tool_name == "update_timepoint_attr":
        timepoint_id = params.get("timepoint_id")
        if str(timepoint_id) not in loaded_timepoint_ids:
          return (
            "本轮 Action 被拒绝：update_timepoint_attr 的 timepoint_id="
            f"{timepoint_id} 在本轮开始时不属于已加载时间点。"
            "刚由 create_timepoint 创建的时间点必须等下一轮 Observation 返回后再更新属性。"
          )
      elif tool_name == "create_timepoints_relationship":
        for key in ("timepoint_id_1", "timepoint_id_2"):
          timepoint_id = params.get(key)
          if str(timepoint_id) not in loaded_timepoint_ids:
            return (
              "本轮 Action 被拒绝：create_timepoints_relationship 的 "
              f"{key}={timepoint_id} 在本轮开始时不属于已加载时间点。"
              "关系两端必须都是本轮开始前已加载的旧时间点；不要引用刚创建或猜测的时间点 ID。"
            )
      elif tool_name == "append_citation":
        target_table = params.get("target_table")
        target_id = params.get("target_id")
        if target_table == "Timepoints" and str(target_id) not in loaded_timepoint_ids:
          return (
            "本轮 Action 被拒绝：append_citation 的 Timepoints target_id="
            f"{target_id} 在本轮开始时不属于已加载时间点。"
            "刚由 create_timepoint 创建的时间点必须等下一轮 Observation 返回后再追加引用。"
          )
        if target_table == "Relationships" and str(target_id) not in loaded_relationship_ids:
          return (
            "本轮 Action 被拒绝：append_citation 的 Relationships target_id="
            f"{target_id} 在本轮开始时不属于已加载关系。"
            "刚创建或猜测的关系 ID 必须等下一轮 Observation 返回后再追加引用。"
          )

    return None

  def _loaded_entity_ids(self) -> set[str]:
    ids: set[str] = set()
    for key, item in self.loaded_data_items.items.items():
      ids.add(str(key))
      try:
        entity_id = item.get("entity", {}).get("id")
      except AttributeError:
        entity_id = None
      if entity_id is not None:
        ids.add(str(entity_id))
    return ids

  def _loaded_timepoint_ids(self) -> set[str]:
    ids: set[str] = set()
    for item in self.loaded_data_items.items.values():
      try:
        timepoints = item.get("timepoints", [])
      except AttributeError:
        continue
      for timepoint in timepoints:
        try:
          timepoint_id = timepoint.get("id")
        except AttributeError:
          continue
        if timepoint_id is not None:
          ids.add(str(timepoint_id))
    return ids

  def _loaded_relationship_ids(self) -> set[str]:
    ids: set[str] = set()
    for item in self.loaded_data_items.items.values():
      try:
        timepoints = item.get("timepoints", [])
      except AttributeError:
        continue
      for timepoint in timepoints:
        try:
          relationships = timepoint.get("relationships", [])
        except AttributeError:
          continue
        for relationship in relationships:
          try:
            relationship_id = relationship.get("id")
          except AttributeError:
            continue
          if relationship_id is not None:
            ids.add(str(relationship_id))
    return ids

  def _require_loaded_entity(self, entity_id: Any, usage: str) -> Optional[Dict[str, str]]:
    if str(entity_id) not in self._loaded_entity_ids():
      return {
        "error": (
          f"{usage} 被拒绝：实体 id={entity_id} 不在当前已加载数据项中。"
          "请先用 get_entity 查询该实体，或先 create_entity 并等待 Observation 返回真实 ID；"
          "不要直接使用实体索引里的裸 ID 或猜测 ID 写库。"
        )
      }
    return None

  def _require_loaded_timepoint(self, timepoint_id: Any, usage: str) -> tuple[Optional[Dict[str, str]], Optional[Dict[str, Any]]]:
    timepoint = self.db.get_timepoint_by_id(timepoint_id)
    if timepoint is None:
      return {"error": f"{usage} 被拒绝：未找到时间点 id={timepoint_id}"}, None
    error = self._require_loaded_entity(timepoint["entity_id"], f"{usage} 使用时间点 id={timepoint_id}")
    if error is not None:
      return error, None
    return None, timepoint

  def _require_loaded_relationship(self, relationship_id: Any, usage: str) -> tuple[Optional[Dict[str, str]], Optional[Dict[str, Any]]]:
    relationship = self.db.get_relationship_by_id(relationship_id)
    if relationship is None:
      return {"error": f"{usage} 被拒绝：未找到关系 id={relationship_id}"}, None
    for role, tp_id in (("主体", relationship["subject_id"]), ("客体", relationship["object_id"])):
      error, _ = self._require_loaded_timepoint(tp_id, f"{usage} 使用关系 id={relationship_id} 的{role}时间点")
      if error is not None:
        return error, None
    return None, relationship

  def parse_cot(self, cot_str: str, tools: Dict[str, Callable]):
    """返回值为是否结束当前轮次（Action 为 Tasks All Finished）"""
    try:
      cot = load_json_string(cot_str)
    except Exception as e:
      print(f"解析思维链 JSON 失败，可能由于格式错误或超出输出长度限制: {e}")
      self.cot.add_item({
        "role": "system",
        "type": "Error",
        "content": f"解析思维链 JSON 失败，可能由于格式错误或超出输出长度限制: {e}\n上轮输出内容为 {cot_str}"
      })
      return False

    if "thought" in cot:
      self.cot.add_item({
        "role": "assistant",
        "type": "thought",
        "content": cot["thought"]
      })
    if "action" in cot:
      if cot["action"] == "Tasks All Finished":
        if "add_atomic_fact" in tools and not self.atomic_facts.facts:
          self.cot.add_item({
            "role": "system",
            "type": "Error",
            "content": (
              "阶段 1 不能在没有任何原子事实时直接完成。"
              "如果 Thought 中已经识别出需要提取的内容，必须在 Action 中调用 add_atomic_fact；"
              "系统不会在后续步骤自动替你添加事实。请重新阅读当前词条并立即提取原子事实。"
            )
          })
          return False
        if "create_entity" in tools and self.atomic_facts.facts and not self.loaded_data_items.items:
          self.cot.add_item({
            "role": "system",
            "type": "Error",
            "content": (
              "阶段 2 不能在没有任何已查询或已更新数据项时直接完成。"
              "上一轮如果出现 JSON 解析失败或工具参数错误，说明工具没有成功执行；"
              "不要声称“已写入数据库”。请重新输出合法 JSON，并调用 get_entity/create_entity/"
              "create_timepoint/update_timepoint_attr/create_timepoints_relationship 等工具处理原子事实。"
            )
          })
          return False
        self.cot.add_item({
          "role": "assistant",
          "type": "action",
          "content": cot["action"]
        })
        return True
      elif isinstance(cot["action"], list):
        batch_error = self.validate_action_batch(cot["action"], tools)
        if batch_error is not None:
          self.cot.add_item({
            "role": "assistant",
            "type": "action",
            "content": json.dumps(cot["action"], ensure_ascii=False, indent=2)
          })
          self.cot.add_item({
            "role": "system",
            "type": "Error",
            "content": batch_error
          })
          return False
        tool_results = []
        tool_outputs = []
        for call in cot["action"]:
          results, outputs = self.call_tool(call, tools)
          if results:
            tool_results.append(results)
          if outputs:
            tool_outputs.append(outputs)
        self.cot.add_item({
          "role": "assistant",
          "type": "action",
          "content": json.dumps(cot["action"], ensure_ascii=False, indent=2)
        })
        observation_parts = []
        if tool_results:
          observation_parts.append('\n'.join(tool_results))
        if tool_outputs:
          observation_parts.append('\n'.join(tool_outputs))
        observation = '\n'.join(part for part in observation_parts if part)
        if observation != "":
          self.cot.add_item({
            "role": "system",
            "type": "observation",
            "content": observation
          })
      else:
        print(f"解析 Action 失败，调用工具方式可能不正确: {cot['action']}")
        self.cot.add_item({
          "role": "system",
          "type": "Error",
          "content": f"解析 Action 失败，调用工具方式可能不正确: {cot['action']}"
        })
    return False

  """
  以下是内置工具封装，便于 CoT 中的 Action 部分调用
  工具会产生三部分影响：
    * 工具调用结果，用于更新 Action
    * 工具对于 State 的影响，直接修改 State 内容（不在返回值中额外出现）
    * 工具调用输出，用于更新 Observation（可选）
  输出包含两个部分
    * tool_call_result
    * tool_call_output
  """

  def tool_search_dictionary(self, title: str, page: str):
    entry = self.db.search_dictionary(title, page)
    if "error" in entry:
      print(f"Error: {entry['error']}")
      return {"error": entry["error"]}, None
    self.loaded_dict_entries.new_queried(title, page, entry)
    return f"查询到《辞典》词条: {title}-{page}", None

  def tool_add_atomic_fact(self, context: str):
    # 内容级去重：批跑中 LLM 会每轮把同一批事实重新添加一遍（南道都总管词条
    # 同样 4 条事实被加了 3 轮），重复内容直接拒绝并提醒收尾
    normalized = "".join(context.split())
    for existing_id, existing_fact in self.atomic_facts.facts.items():
      if "".join(existing_fact.split()) == normalized:
        return (
          f"未新增：该原子事实与已有的 #{existing_id} 内容完全相同。"
          "请勿重复添加；若所有事实均已提取完毕，请直接输出 \"Tasks All Finished\" 结束本阶段。"
        ), None
    fact_id = self.atomic_facts.new_fact(context)
    return f"新增原子事实: #{fact_id}", None

  def tool_remove_atomic_fact(self, fact_id: str):
    fact_id = str(fact_id)
    if fact_id not in self.atomic_facts.facts:
      return {"error": f"原子事实不存在: #{fact_id}"}, None
    self.atomic_facts.remove_fact(fact_id)
    return f"删除原子事实: #{fact_id}", None

  def tool_update_atomic_fact(self, fact_id: str, context: str):
    fact_id = str(fact_id)
    if fact_id not in self.atomic_facts.facts:
      return {"error": f"原子事实不存在: #{fact_id}"}, None
    self.atomic_facts.update_fact(fact_id, context)
    return f"更新原子事实: #{fact_id}", None

  def tool_get_entity(self, entity_id: str):
    # 已加载实体的重复查询不会带来新信息（其状态每轮都注入「已加载数据项」），
    # 在反馈中明确指出，避免 LLM 用"再查一次"代替决策
    already_loaded = any(str(k) == str(entity_id) for k in self.loaded_data_items.items)
    response = get_entity(self.db, entity_id)
    if "error" in response:
      return response, None
    self.loaded_data_items.update_item(entity_id, response)
    if already_loaded:
      return (
        f"实体 #{entity_id} 已在上下文中，其完整信息见提示词「已加载数据项」部分。"
        "请勿重复查询，直接基于该信息决策并执行下一步操作。"
      ), None
    return f"查询到实体信息: #{entity_id}", None

  def tool_create_entity(self, title: str, type: str, allow_duplicate: bool = False):
    response = create_entity(self.db, title, type, allow_duplicate=allow_duplicate)
    if "error" in response:
      return response, None
    # 取出附加字段后再存入上下文，loaded_data_items 中只保留实体状态本身
    created = response.pop("created", None)
    default_timepoint_id = response.pop("default_timepoint_id", None)
    entity_id = response["entity"]["id"]
    self.loaded_data_items.update_item(entity_id, response)
    if created and default_timepoint_id is not None:
      return (
        f"创建实体: #{entity_id}（自带默认时间点 #{default_timepoint_id}，"
        f"可直接对该时间点更新属性或建立关系）"
      ), None
    return f"复用已有实体: #{entity_id}", None

  def tool_create_timepoint(
    self,
    entity_id: str,
    time: str,
    event: str,
    succ_timepoint_id: Optional[str] = None,
    citation: Optional[str] = None,
    quotation: Optional[str] = None,
  ):
    error = self._require_loaded_entity(entity_id, "create_timepoint")
    if error is not None:
      return error, None
    if succ_timepoint_id is not None:
      error, succ_tp = self._require_loaded_timepoint(succ_timepoint_id, "create_timepoint 的 succ_timepoint_id")
      if error is not None:
        return error, None
      if str(succ_tp["entity_id"]) != str(entity_id):
        return {"error": "create_timepoint 被拒绝：succ_timepoint_id 不属于当前 entity_id"}, None
    response = create_timepoint(self.db, entity_id, succ_timepoint_id, time, event, citation, quotation)
    if "error" in response:
      return response, None
    # 新时间点 ID 必须明确反馈：占位复用机制使 ID 不可按自增规律预测，
    # v0304 批跑中 LLM 因猜错 ID 反复触发"未找到时间点"失败
    new_timepoint_id = response.pop("new_timepoint_id", None)
    self.loaded_data_items.update_item(entity_id, response)
    if new_timepoint_id is not None:
      return f"向实体 #{entity_id} 插入时间点 #{new_timepoint_id}", None
    return f"向实体 #{entity_id} 插入时间点", None

  def tool_update_timepoint_attr(
    self,
    timepoint_id: str,
    attr_key: str,
    attr_value: str,
    citation: Optional[str] = None,
    quotation: Optional[str] = None,
    note: Optional[str] = None,
  ):
    error, _ = self._require_loaded_timepoint(timepoint_id, "update_timepoint_attr")
    if error is not None:
      return error, None
    response = update_timepoint_attr(self.db, timepoint_id, attr_key, attr_value, citation, quotation, note)
    if "error" in response:
      return response, None
    self.loaded_data_items.update_item(response["entity"]["id"], response)
    return f"更新实体 #{response["entity"]["id"]} 时间点属性", None

  def tool_create_timepoints_relationship(
    self,
    timepoint_id_1: str,
    timepoint_id_2: str,
    relation_type: str,
    staff_quota: Optional[int] = None,
    staff_type: Optional[str] = None,
    citation: Optional[str] = None,
    quotation: Optional[str] = None,
    note: Optional[str] = None,
  ):
    error, _ = self._require_loaded_timepoint(timepoint_id_1, "create_timepoints_relationship 的主体 timepoint_id_1")
    if error is not None:
      return error, None
    error, _ = self._require_loaded_timepoint(timepoint_id_2, "create_timepoints_relationship 的客体 timepoint_id_2")
    if error is not None:
      return error, None
    response = create_timepoints_relationship(
      self.db,
      timepoint_id_1,
      timepoint_id_2,
      relation_type,
      staff_quota,
      staff_type,
      citation,
      quotation,
      note,
    )
    if "error" in response:
      return response, None
    relationship_id = response.pop("relationship_id", None)
    created = response.pop("created", None)
    self.loaded_data_items.update_item(response["entity_1"]["entity"]["id"], response["entity_1"])
    self.loaded_data_items.update_item(response["entity_2"]["entity"]["id"], response["entity_2"])
    if relationship_id is not None:
      action = "创建" if created else "复用"
      return (
        f"{action}关系 #{relationship_id}：实体 #{response['entity_1']['entity']['id']} "
        f"和 #{response['entity_2']['entity']['id']} 之间的关系"
      ), None
    return f"更新实体 #{response['entity_1']['entity']['id']} 和 #{response['entity_2']['entity']['id']} 之间的关系", None

  def tool_upsert_entity_timepoint(
    self,
    title: str,
    type: str,
    time: str,
    event: str,
    attributes: Optional[Dict[str, str]] = None,
    succ_timepoint_id: Optional[str] = None,
    citation: Optional[str] = None,
    quotation: Optional[str] = None,
    note: Optional[str] = None,
    allow_duplicate: bool = False,
  ):
    response = upsert_entity_timepoint(
      self.db,
      title,
      type,
      time,
      event,
      attributes,
      succ_timepoint_id,
      citation,
      quotation,
      note,
      allow_duplicate,
    )
    if "error" in response:
      return response, None
    entity_created = response.pop("entity_created")
    timepoint_created = response.pop("timepoint_created")
    timepoint_id = response.pop("timepoint_id")
    entity_id = response["entity"]["id"]
    self.loaded_data_items.update_item(entity_id, response)
    entity_action = "创建实体" if entity_created else "复用实体"
    timepoint_action = "创建时间点" if timepoint_created else "复用时间点"
    return (
      f"{entity_action} #{entity_id}；{timepoint_action} #{timepoint_id}；"
      "属性与首条引用已在同一工具调用中处理"
    ), None

  def tool_upsert_relationship(
    self,
    subject_title: str,
    subject_type: str,
    subject_time: str,
    object_title: str,
    object_type: str,
    object_time: str,
    relation_type: str,
    subject_event: Optional[str] = None,
    object_event: Optional[str] = None,
    staff_quota: Optional[int] = None,
    staff_type: Optional[str] = None,
    citation: Optional[str] = None,
    quotation: Optional[str] = None,
    note: Optional[str] = None,
  ):
    response = upsert_relationship(
      self.db,
      subject_title,
      subject_type,
      subject_time,
      object_title,
      object_type,
      object_time,
      relation_type,
      subject_event,
      object_event,
      staff_quota,
      staff_type,
      citation,
      quotation,
      note,
    )
    if "error" in response:
      return response, None
    relationship_id = response.pop("relationship_id")
    created = response.pop("created")
    subject_entity_id = response.pop("subject_entity_id")
    subject_timepoint_id = response.pop("subject_timepoint_id")
    object_entity_id = response.pop("object_entity_id")
    object_timepoint_id = response.pop("object_timepoint_id")
    self.loaded_data_items.update_item(subject_entity_id, response["entity_1"])
    self.loaded_data_items.update_item(object_entity_id, response["entity_2"])
    action = "创建" if created else "复用"
    return (
      f"{action}关系 #{relationship_id}："
      f"实体 #{subject_entity_id} 时间点 #{subject_timepoint_id} -> "
      f"实体 #{object_entity_id} 时间点 #{object_timepoint_id}；引用已同时处理"
    ), None

  def tool_append_citation(
    self,
    target_table: str,
    target_id: str,
    citation: Optional[str] = None,
    quotation: Optional[str] = None,
    note: Optional[str] = None,
    conflict_flag: bool = False,
  ):
    if target_table == "Timepoints":
      error, _ = self._require_loaded_timepoint(target_id, "append_citation")
      if error is not None:
        return error, None
    elif target_table == "Relationships":
      error, _ = self._require_loaded_relationship(target_id, "append_citation")
      if error is not None:
        return error, None
    response = append_citation(self.db, target_table, target_id, citation, quotation, note, conflict_flag)
    if "error" in response:
      return response, None
    if target_table == "Timepoints":
      self.loaded_data_items.update_item(response["entity"]["id"], response)
      return f"追加实体 #{response["entity"]["id"]} 时间点属性引用依赖", None
    else:
      self.loaded_data_items.update_item(response["entity_1"]["entity"]["id"], response["entity_1"])
      self.loaded_data_items.update_item(response["entity_2"]["entity"]["id"], response["entity_2"])
      return f"追加实体 #{response["entity_1"]["entity"]["id"]} 和 #{response["entity_2"]["entity"]["id"]} 之间的关系引用依赖", None
