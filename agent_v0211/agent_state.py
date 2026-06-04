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
from typing import Any, Dict, List, Optional, Literal, Iterable, TypedDict

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

@dataclass
class AtomicFactsContext:
  index: int = 0
  facts: Dict[str, str] = field(default_factory=dict)

  def new_fact(self, fact: str) -> str:
    self.index += 1
    self.facts[self.index] = fact
    return self.index

  def update_fact(self, fact_id: str, fact: str) -> None:
    self.facts[fact_id] = fact
  
  def remove_fact(self, fact_id: str) -> None:
    del self.facts[fact_id]
  
  def get_merged_text(self) -> str:
    return "\n".join(self.facts.values())

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

@dataclass
class AgentState:
  db: Database
  dict_index: Dict[str, bool]
  dict_index_text: str
  dict_todo: List[str]
  loaded_dict_entries: Dict[str, Dict[str, Any]]
  loaded_data_items: Dict[str, Dict[str, Any]]
  atomic_facts: Dict[str, Any]
  cot: CoTContext
  finished: bool = False

  def __init__(self, db: Database):
    self.db = db
    dict_index_list = db.get_dictionary_index()
    self.dict_index = {index: False for index in dict_index_list}
    self.dict_index_text = "\n".join(dict_index_list)
  
  def init_short_memory(self):
    self.loaded_dict_entries = DictionaryContext()
    self.loaded_data_items = DataItemContext()
    self.atomic_facts = AtomicFactsContext()
    self.cot = CoTContext()
    self.finished = False
  
  def dictionary_query(self, title: str, page: str):
    entry = search_dictionary(self.db, title, page)
    if "error" in entry:
      print(f"Error: {entry['error']}")
      return {"error": entry["error"]}
    self.loaded_dict_entries.new_queried(title, page, entry)
    return entry
