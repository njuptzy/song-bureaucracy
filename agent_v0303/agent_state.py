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
import json
from typing import Any, Dict, List, Optional, Literal, Iterable, TypedDict, Callable

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
  append_citation,
  load_json_string
)
from prompt_input2facts import build_input2facts_prompt
from prompt_facts2data import build_facts2data_prompt

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
  
  def prepare_for_update(self):
    self.loaded_data_items = DataItemContext()
    self.cot = CoTContext()
    self.finished_update = False
  
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
    prompt = build_input2facts_prompt(
      dictionary_index_summary=self.dict_index_text,
      current_dictionary_texts=self.loaded_dict_entries.get_merged_text(),
      current_atomic_facts=self.atomic_facts.get_merged_text(),
      history_summary=self.cot.get_merged_text(),
    )
    return prompt
  
  def build_prompt_facts2data(self):
    entities_index_text = "\n".join(self.db.get_entities_index())
    if entities_index_text == "":
      entities_index_text = "当前没有创建任何实体"
    prompt = build_facts2data_prompt(
      entity_index_summary=entities_index_text,
      current_atomic_facts=self.atomic_facts.get_merged_text(),
      current_data_items=self.loaded_data_items.get_merged_text(),
      history_summary=self.cot.get_merged_text(),
    )
    return prompt
  
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

    def build_return(config):
      result_text = ""
      output_text = ""
      tool_name = config.get("tool", 'unknown')
      params = []
      for key, value in config["parameters"].items():
        params.append(f"{key}={value}")
      result_text += f"调用工具：{tool_name}({', '.join(params)})\n"
      if config["status"] == "success":
        result_text += "成功"
        if config["result"] is not None:
          result_text += f"：{config['result']}"
      else:
        result_text += "失败"
        if config["error"] is not None:
          result_text += f"：{config['error']}"
      
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
    return build_return(config)
  
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
        self.cot.add_item({
          "role": "assistant",
          "type": "action",
          "content": cot["action"]
        })
        return True
      elif isinstance(cot["action"], list):
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
          "content": '\n'.join(tool_results)
        })
        observation = '\n'.join(tool_outputs)
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
    response = get_entity(self.db, entity_id)
    if "error" in response:
      return response, None
    self.loaded_data_items.update_item(entity_id, response)
    return f"查询到实体信息: #{entity_id}", None
  
  def tool_create_entity(self, title: str, type: str, allow_duplicate: bool = False):
    response = create_entity(self.db, title, type, allow_duplicate=allow_duplicate)
    if "error" in response:
      return response, None
    self.loaded_data_items.update_item(response["entity"]["id"], response)
    return f"创建或复用实体: #{response['entity']['id']}", None

  def tool_create_timepoint(
    self,
    entity_id: str,
    time: str,
    event: str,
    succ_timepoint_id: Optional[str] = None,
    citation: Optional[str] = None,
    quotation: Optional[str] = None,
  ):
    response = create_timepoint(self.db, entity_id, succ_timepoint_id, time, event, citation, quotation)
    if "error" in response:
      return response, None
    self.loaded_data_items.update_item(entity_id, response)
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
    staff_quota: Optional[str] = None,
    staff_type: Optional[str] = None,
    citation: Optional[str] = None,
    quotation: Optional[str] = None,
  ):
    response = create_timepoints_relationship(
      self.db,
      timepoint_id_1,
      timepoint_id_2,
      relation_type,
      staff_quota,
      staff_type,
      citation,
      quotation,
    )
    if "error" in response:
      return response, None
    self.loaded_data_items.update_item(response["entity_1"]["entity"]["id"], response["entity_1"])
    self.loaded_data_items.update_item(response["entity_2"]["entity"]["id"], response["entity_2"])
    return f"更新实体 #{response["entity_1"]["entity"]["id"]} 和 #{response["entity_2"]["entity"]["id"]} 之间的关系", None

  def tool_append_citation(
    self,
    target_table: str,
    target_id: str,
    citation: Optional[str] = None,
    quotation: Optional[str] = None,
    note: Optional[str] = None,
    conflict_flag: bool = False,
  ):
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
