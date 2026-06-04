from typing import TypedDict, Optional, List, Any
import json
from database import Database

class Citation(TypedDict):
  reference: str
  content: str

class Reasoning(TypedDict):
  citations: List[Citation]
  inference: str

class ToolCall(TypedDict):
  tool_name: str
  parameters: dict
  action_description: str
  result: str
  reasoning: Reasoning
  error: Optional[str]

class CoT(TypedDict):
  role: str
  type: str
  content: Any

def call_tools(database, actions) -> List[ToolCall]:
  """
  调用工具并返回结果列表
  """
  results = []
  for action in actions:
    if not isinstance(action, dict):
      results.append({
        "tool_name": "unknown",
        "parameters": {},
        "action_description": json.dumps(action, ensure_ascii=False),
        "result": "",
        "reasoning": None,
        "error": f"无效的工具调用格式"
      })
      continue
    tool_name = action.get("tool", "")
    parameters = action.get("parameters", {})
    if not tool_name:
      results.append({
        "tool_name": "unknown",
        "parameters": parameters,
        "action_description": json.dumps(action, ensure_ascii=False),
        "result": "",
        "reasoning": None,
        "error": "缺少工具名称"
      })
      continue
    
    action_description = f"调用工具 {tool_name}"
    reasoning = action.get("reasoning", None)

    if tool_name not in ["search_dictionary", "check_existing_entry"] and reasoning is None:
      # 更新数据但是没有提供 Reasoning，报错
      results.append({
        "tool_name": tool_name,
        "parameters": parameters,
        "action_description": action_description,
        "error": "更新数据但是没有提供引用依赖信息"
      })
      continue

    try:
      ret = None
      
      # 查询工具（不需要 reasoning）
      if tool_name == "search_dictionary":
        ret = database.get_dict_entry(
          title=parameters.get("title"),
          page=parameters.get("page")
        )
        action_description = f"查询《辞典》条目 '{parameters.get('title', '')} {parameters.get('page', '?')}页'"
      
      elif tool_name == "check_existing_entry":
        ret = database.get_table_entries(
          title=parameters.get("title"),
          page=parameters.get("page")
        )
        action_description = f"查询官制表条目 '{parameters.get('title', '')} {parameters.get('page', '?')}页'"
      
      # 更新工具（需要 reasoning）
      elif tool_name == "update_attr":
        ret = database.update_attr(
          title=parameters.get("title"),
          page=parameters.get("page"),
          bgn_time=parameters.get("bgn_time"),
          end_time=parameters.get("end_time"),
          attr_key=parameters.get("attr_key"),
          attr_value=parameters.get("attr_value")
        )
        action_description = f"更新官制表条目 '{parameters.get('title', '')} {parameters.get('page', '?')}页 ({parameters.get('bgn_time', '?')}-{parameters.get('end_time', '?')})' 的 {parameters.get('attr_key', '')} 属性"
      
      elif tool_name == "append_list":
        ret = database.append_list(
          title=parameters.get("title"),
          page=parameters.get("page"),
          bgn_time=parameters.get("bgn_time"),
          end_time=parameters.get("end_time"),
          attr_key=parameters.get("attr_key"),
          attr_value=parameters.get("attr_value"),
          index=parameters.get("index")
        )
        action_description = f"向官制表条目 '{parameters.get('title', '')} {parameters.get('page', '?')}页 ({parameters.get('bgn_time', '?')}-{parameters.get('end_time', '?')})' 的 {parameters.get('attr_key', '')} 列表属性中插入值"
      
      elif tool_name == "update_list":
        ret = database.update_list(
          title=parameters.get("title"),
          page=parameters.get("page"),
          bgn_time=parameters.get("bgn_time"),
          end_time=parameters.get("end_time"),
          attr_key=parameters.get("attr_key"),
          attr_value=parameters.get("attr_value"),
          index=parameters.get("index")
        )
        action_description = f"更新官制表条目 '{parameters.get('title', '')} {parameters.get('page', '?')}页 ({parameters.get('bgn_time', '?')}-{parameters.get('end_time', '?')})' 的 {parameters.get('attr_key', '')} 列表属性中的指定值"
      
      elif tool_name == "remove_list":
        ret = database.remove_list(
          title=parameters.get("title"),
          page=parameters.get("page"),
          bgn_time=parameters.get("bgn_time"),
          end_time=parameters.get("end_time"),
          attr_key=parameters.get("attr_key"),
          attr_value=parameters.get("attr_value"),
          index=parameters.get("index")
        )
        action_description = f"删除官制表条目 '{parameters.get('title', '')} {parameters.get('page', '?')}页 ({parameters.get('bgn_time', '?')}-{parameters.get('end_time', '?')})' 的 {parameters.get('attr_key', '')} 列表属性中的指定值"
      
      elif tool_name == "insert_time_point":
        ret = database.insert_time_point(
          title=parameters.get("title"),
          page=parameters.get("page"),
          bgn_time=parameters.get("bgn_time"),
          end_time=parameters.get("end_time"),
          time_point=parameters.get("time_point"),
          event=parameters.get("event")
        )
        action_description = f"在官制表条目 '{parameters.get('title', '')} {parameters.get('page', '?')}页 ({parameters.get('bgn_time', '?')}-{parameters.get('end_time', '?')})' 插入时间点 {parameters.get('time_point', '?')}"
      
      elif tool_name == "expend_time_point":
        ret = database.expend_time_point(
          title=parameters.get("title"),
          page=parameters.get("page"),
          bgn_time=parameters.get("bgn_time"),
          end_time=parameters.get("end_time"),
          exp_type=parameters.get("exp_type"),
          time_point=parameters.get("time_point"),
          event=parameters.get("event")
        )
        action_description = f"扩展官制表条目 '{parameters.get('title', '')} {parameters.get('page', '?')}页 ({parameters.get('bgn_time', '?')}-{parameters.get('end_time', '?')})' 的时间范围 ({parameters.get('exp_type', '?')})"
      
      else:
        results.append({
          "tool_name": tool_name,
          "parameters": parameters,
          "action_description": action_description,
          "result": "",
          "reasoning": reasoning,
          "error": f"未知的工具名称: {tool_name}"
        })
        continue
      
      # 处理返回结果
      if isinstance(ret, dict) and "error" in ret:
        # 调用工具，但没有成功执行
        results.append({
          "tool_name": tool_name,
          "parameters": parameters,
          "action_description": action_description,
          "result": json.dumps(ret, ensure_ascii=False),
          "reasoning": reasoning,
          "error": ret["error"]
        })
      else:
        # 成功执行，将结果转换为 JSON 字符串
        if tool_name == "search_dictionary":
          # 对于查询《辞典》数据，使用格式化输出
          result_text = Database.dict_entry_to_str(ret)
        elif tool_name == "check_existing_entry":
          # 对于查询官制条目，使用 JSON 格式化输出
          result_text = Database.table_entries_to_str(ret)
        else:
          # 对于其他操作，直接使用 JSON 格式
          if isinstance(ret, list):
            result_text = Database.table_entries_to_str(ret)
          else:
            result_text = Database.table_entry_to_str(ret)
        
        results.append({
          "tool_name": tool_name,
          "parameters": parameters,
          "action_description": action_description,
          "result": result_text,
          "reasoning": reasoning,
          "error": None
        })
        
    except Exception as e:
      results.append({
        "tool_name": tool_name,
        "parameters": parameters,
        "action_description": action_description,
        "result": "",
        "reasoning": reasoning,
        "error": f"工具调用异常: {str(e)}"
      })
  return results

def cot_to_str(CoTs):
  contexts = []
  for idx, cot in enumerate(CoTs):
    contexts.append(f"#{idx+1:>5d}: {cot["role"]}'s {cot["type"]}\n{cot["content"]}\n")
  return "\n".join(contexts)

def tool_results_to_log_str(results):
  results_texts = []
  for result in results:
    parameter_texts = []
    for key, value in result["parameters"].items():
      parameter_texts.append(f"{key}={value}")
    text = f"""
调用工具：{result["tool_name"]}({", ".join(parameter_texts)})
{result["action_description"]}
"""
    if result["error"] is not None:
      text += f"失败：{result["error"]}"
    else:
      text += f"成功：{result["result"]}"
    results_texts.append(text)
  return "\n\n".join(results_texts)