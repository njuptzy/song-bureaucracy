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

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Literal, Iterable

from database import Database
from tools import (
  search_dictionary,
  dict_entry_to_str,
  get_entity,
  entity_to_str,
  create_entity,
  create_timepoint,
  update_timepoint_attr,
  create_timepoints_relationship,
  append_citation
)


CotEventType = Literal[
  "info",
  "entry_start",
  "entry_end",
  "tool_call",
  "tool_result",
  "model_thought",
  "atomic_facts",
  "error",
]


@dataclass
class CoTEvent:
  """
  单条 CoT 事件记录。

  用于追踪一次 Agent 运行中的关键步骤与工具调用情况，
  便于后续写入 save/ 目录或进行调试分析。
  """

  type: CotEventType
  message: str
  step: Optional[str] = None
  data: Dict[str, Any] = field(default_factory=dict)
  timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class DictionaryContext:
  """
  S1：当前辞典条目上下文。

  - entries：来自《辞典》数据库的原始记录集合（search_dictionary 的返回值）；
      使用 "title-page" 作为键，entry 作为值；初始包含原始输入词条；
  - merged_text：将 entries 转为结构化文本后合并的长文本，直接作为提示词输入的一部分；
      随着 entries 更新而更新。
  """

  entries: Dict[str, Dict[str, Any]] = field(default_factory=dict)
  merged_text: str = ""

  def add_page_entry(self, title: str, page: str, entry: Dict[str, Any]) -> None:
    """
    记录新查询到的一页辞典数据。

    使用 "title-page" 作为键存入 entries；若键已存在，则以新值覆盖。
    """
    key = f"{title}-{page}"
    self.entries[key] = entry
    self.update_merged_text()

  def update_merged_text(self) -> str:
    merged_text = []
    for key, value in self.entries.items():
      text = dict_entry_to_str(value)
      merged_text.append(text)
    self.merged_text = "\n".join(merged_text)
    return self.merged_text


@dataclass
class EntityContext:
  """
  S2：当前实体上下文。

  仅维护当前涉及到的所有实体信息（保持最新状态）。
  - entities_state：entity_id → 对应的 get_entity 返回结果；
    在调用工具修改后，应使用工具返回的最新实体信息刷新该结构。
  """

  entities_state: Dict[int, Dict[str, Any]] = field(default_factory=dict)

  def set_entity_state(self, entity_id: int, state: Dict[str, Any]) -> None:
    """设置或更新某个实体的当前视图（通常来自 tools.get_entity）。"""
    self.entities_state[entity_id] = state


@dataclass
class AtomicFactsContext:
  """
  原子事实（atomic facts）上下文。

  - facts：当前轮从辞典文本中抽取出的全部原子事实列表；
  - pending_ids / applied_ids / skipped_ids：
      使用 fact_id（由上层抽取原子事实时定义）跟踪处理状态。
  """

  facts: List[Dict[str, Any]] = field(default_factory=list)
  pending_ids: List[str] = field(default_factory=list)
  applied_ids: List[str] = field(default_factory=list)
  skipped_ids: List[str] = field(default_factory=list)

  def set_facts(self, facts: Iterable[Dict[str, Any]], id_key: str = "fact_id") -> None:
    """
    覆盖式设置当前原子事实列表，并按给定 id 字段初始化为待处理状态。

    Args:
      facts: 原子事实列表（通常由内圈第一步的 LLM 输出）；
      id_key: 在 fact 中用于标识 fact_id 的键名，默认 "fact_id"。
    """
    self.facts = list(facts)
    self.pending_ids = []
    self.applied_ids = []
    self.skipped_ids = []

    for fact in self.facts:
      fid = fact.get(id_key)
      if isinstance(fid, str) and fid:
        self.pending_ids.append(fid)

  def ensure_pending_ids(self, fact_ids: Iterable[str]) -> None:
    """
    将一批 fact_id 视为待处理（若尚未在任一列表中出现）。

    方便在第二步初始化阶段一次性灌入所有原子事实，
    或在运行过程中补充新的 fact_id。
    """
    existing = set(self.pending_ids) | set(self.applied_ids) | set(self.skipped_ids)
    for fid in fact_ids:
      if fid not in existing:
        self.pending_ids.append(fid)

  def mark_applied(self, fact_id: str) -> None:
    """将某个 fact 标记为已成功应用到数据库。"""
    if fact_id in self.pending_ids:
      self.pending_ids.remove(fact_id)
    if fact_id not in self.applied_ids:
      self.applied_ids.append(fact_id)

  def mark_skipped(self, fact_id: str) -> None:
    """
    将某个 fact 标记为跳过 / 暂无法处理。可用于留待人工复核。
    """
    if fact_id in self.pending_ids:
      self.pending_ids.remove(fact_id)
    if fact_id not in self.skipped_ids:
      self.skipped_ids.append(fact_id)


@dataclass
class AgentState:
  """
  Agent 顶层状态对象。

  - db：长期记忆（数据库）入口，由外部创建后传入；
  - dict_ctx：当前辞典上下文（S1），在每个新词条开始时重置；
  - entity_ctx：当前实体上下文（S2），在每个新词条开始时重置；
  - atomic_ctx：当前原子事实上下文，在每个新词条开始时重置；
  - cot_log：本轮 CoT 事件列表，可用于最终落盘到 save/ 目录。
  """

  db: Database
  dict_ctx: Optional[DictionaryContext] = None
  entity_ctx: Optional[EntityContext] = None
  atomic_ctx: Optional[AtomicFactsContext] = None
  cot_log: List[CoTEvent] = field(default_factory=list)

  # ========= 轮次级别操作 =========

  def start_new_entry(self, title: str, page: str) -> None:
    """
    开始处理一个新的辞典词条。

    会重置短期记忆（S1 / S2）以及原子事实上下文，并记录一条 entry_start 事件。
    """
    self.dict_ctx = DictionaryContext()
    self.entity_ctx = EntityContext()
    self.atomic_ctx = AtomicFactsContext()
    self.add_cot_event(
      type="entry_start",
      message=f"开始处理辞典词条：{title}（页码：{page}）",
      data={"title": title, "page": str(page)},
    )

  def finish_entry(self, status: str, error: Optional[str] = None) -> None:
    """
    结束当前辞典词条的处理，写入 entry_end 事件。

    status 由上层约定，一般可为：'done' / 'partial' / 'failed'。
    """
    data: Dict[str, Any] = {"status": status}
    if error is not None:
      data["error"] = error
    if self.dict_ctx is not None:
      # 词条的 title/page 组合通常记录在 CoT 的 entry_start 事件中；
      # 这里仅在有需要时，可根据 entries 中的 key 做简单补充。
      data["dict_entries_count"] = len(self.dict_ctx.entries)
    self.add_cot_event(type="entry_end", message="结束当前词条处理", data=data)

  # ========= CoT 记录相关 =========

  def add_cot_event(
    self,
    type: CotEventType,
    message: str,
    step: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
  ) -> None:
    """追加一条 CoT 事件。"""
    event = CoTEvent(type=type, message=message, step=step, data=data or {})
    self.cot_log.append(event)

  def to_cot_dicts(self) -> List[Dict[str, Any]]:
    """
    以可 JSON 序列化的形式返回当前 CoT 记录，便于直接写入文件。
    """
    return [asdict(e) for e in self.cot_log]

  # ========= S1 / S2 便捷访问与修改 =========

  def require_dict_ctx(self) -> DictionaryContext:
    """获取当前辞典上下文，若不存在则抛出异常（用于在调用链早期发现逻辑错误）。"""
    if self.dict_ctx is None:
      raise RuntimeError("DictionaryContext 未初始化，请先调用 start_new_entry。")
    return self.dict_ctx

  def require_entity_ctx(self) -> EntityContext:
    """获取当前实体上下文，若不存在则抛出异常。"""
    if self.entity_ctx is None:
      raise RuntimeError("EntityContext 未初始化，请先调用 start_new_entry。")
    return self.entity_ctx

  def require_atomic_ctx(self) -> AtomicFactsContext:
    """获取当前原子事实上下文，若不存在则抛出异常。"""
    if self.atomic_ctx is None:
      raise RuntimeError("AtomicFactsContext 未初始化，请先调用 start_new_entry。")
    return self.atomic_ctx

  def snapshot_for_save(self) -> Dict[str, Any]:
    """
    构造一个可直接用于保存到 save/ 目录的快照对象。

    包含：
      - dict_context：当前 S1 状态；
      - entity_context：当前 S2 状态；
      - atomic_facts_context：当前原子事实状态；
      - cot_log：CoT 事件列表（已转为字典）。
    具体保存路径与文件命名由上层调用者决定。
    """
    return {
      "dict_context": asdict(self.dict_ctx) if self.dict_ctx is not None else None,
      "entity_context": asdict(self.entity_ctx) if self.entity_ctx is not None else None,
      "atomic_facts_context": asdict(self.atomic_ctx) if self.atomic_ctx is not None else None,
      "cot_log": self.to_cot_dicts(),
    }