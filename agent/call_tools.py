from typing import TypedDict, Optional, List
import json

def dict_entry_to_str(entry):
  fields = entry["fields"]
  fields_texts = []
  for key, value in fields.items():
    fields_texts.append(f"{key}: {value}")
  entry_text = f"""
{entry["title"]}
文本来源：{entry["catalog"]} {entry["page"]}页
基本介绍：{entry["text"]}
{"\n".join(fields_texts)}
"""
  return entry_text

def data_entry_to_str(entry):
  return json.dumps(entry, ensure_ascii=False, indent=2)

class ToolCall(TypedDict):
  tool_name: str
  parameters: dict
  action_description: str
  result: str
  error: Optional[str]

def call_tools(database, actions) -> List[ToolCall]:
  """
  调用工具并返回结果列表
  
  Args:
    database: Database 实例
    actions: 工具调用列表，格式为 [{"tool": "TOOL_NAME", "parameters": {...}}, ...]
  
  Returns:
    List[ToolCall]: 工具调用结果列表
  """
  results = []
  
  # 遍历每个工具调用
  for action in actions:
    if not isinstance(action, dict):
      results.append({
        "tool_name": "unknown",
        "parameters": {},
        "action_description": json.dumps(action, ensure_ascii=False),
        "result": "",
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
        "error": "缺少工具名称"
      })
      continue
    
    # 根据工具类型生成更详细的描述
    if tool_name == "search_dictionary":
      action_description = f"查询《辞典》条目 '{parameters.get('title', '')} {parameters.get('page', '?')}页'"
    elif tool_name == "check_existing_entry":
      action_description = f"查询官制表条目 '{parameters.get('title', '')} {parameters.get('page', '?')}页'"
    elif tool_name in ["insert", "update"]:
      action_description = f"更新官制表条目 '{parameters.get('title', '')} {parameters.get('page', '?')}页 ({parameters.get('bgn_time', '?')}-{parameters.get('end_time', '?')})' 的 {parameters.get('attr_key', '')} 属性"
    elif tool_name in ["append_list", "update_list", "remove_list"]:
      action_description = f"更新官制表条目 '{parameters.get('title', '')} {parameters.get('page', '?')}页 ({parameters.get('bgn_time', '?')}-{parameters.get('end_time', '?')})' 的 {parameters.get('attr_key', '')} 列表属性"
    elif tool_name == "new_time_point":
      action_description = f"在官制表条目 '{parameters.get('title', '')} {parameters.get('page', '?')}页 ({parameters.get('bgn_time', '?')}-{parameters.get('end_time', '?')})' 添加中间时间点"
    else:
      action_description = f"调用工具 {tool_name}"
    
    # 调用对应的工具方法
    try:
      if tool_name == "search_dictionary":
        result = database.search_dictionary(
          title=parameters.get("title"),
          page=parameters.get("page")
        )
      
      elif tool_name == "check_existing_entry":
        result = database.check_existing_entry(
          title=parameters.get("title"),
          page=parameters.get("page")
        )
      
      elif tool_name == "insert":
        result = database.insert(
          title=parameters.get("title"),
          page=parameters.get("page"),
          bgn_time=parameters.get("bgn_time"),
          end_time=parameters.get("end_time"),
          attr_key=parameters.get("attr_key"),
          attr_value=parameters.get("attr_value")
        )
      
      elif tool_name == "update":
        result = database.update(
          title=parameters.get("title"),
          page=parameters.get("page"),
          bgn_time=parameters.get("bgn_time"),
          end_time=parameters.get("end_time"),
          attr_key=parameters.get("attr_key"),
          attr_value=parameters.get("attr_value")
        )
      
      elif tool_name == "append_list":
        result = database.append_list(
          title=parameters.get("title"),
          page=parameters.get("page"),
          bgn_time=parameters.get("bgn_time"),
          end_time=parameters.get("end_time"),
          attr_key=parameters.get("attr_key"),
          attr_value=parameters.get("attr_value"),
          index=parameters.get("index")
        )
      
      elif tool_name == "update_list":
        result = database.update_list(
          title=parameters.get("title"),
          page=parameters.get("page"),
          bgn_time=parameters.get("bgn_time"),
          end_time=parameters.get("end_time"),
          attr_key=parameters.get("attr_key"),
          attr_value=parameters.get("attr_value"),
          index=parameters.get("index")
        )
      
      elif tool_name == "remove_list":
        result = database.remove_list(
          title=parameters.get("title"),
          page=parameters.get("page"),
          bgn_time=parameters.get("bgn_time"),
          end_time=parameters.get("end_time"),
          attr_key=parameters.get("attr_key"),
          attr_value=parameters.get("attr_value"),
          index=parameters.get("index")
        )
      
      elif tool_name == "new_time_point":
        result  = database.new_time_point(
          title=parameters.get("title"),
          page=parameters.get("page"),
          bgn_time=parameters.get("bgn_time"),
          end_time=parameters.get("end_time"),
          time_point=parameters.get("time_point"),
          event=parameters.get("event")
        )
      
      else:
        result = {"error": f"未知的工具名称: {tool_name}"}
      
      # 检查结果中是否有错误
      if isinstance(result, dict) and "error" in result:
        results.append({
          "tool_name": tool_name,
          "parameters": parameters,
          "action_description": action_description,
          "result": json.dumps(result, ensure_ascii=False),
          "error": result["error"]
        })
      else:
        # 成功执行，将结果转换为 JSON 字符串
        if tool_name == "search_dictionary":
          result_text = dict_entry_to_str(result)
        else:
          result_text = json.dumps(result, ensure_ascii=False)
        results.append({
          "tool_name": tool_name,
          "parameters": parameters,
          "action_description": action_description,
          "result": result_text,
          "error": None
        })
    
    except Exception as e:
      # 捕获异常
      results.append({
        "tool_name": tool_name,
        "parameters": parameters,
        "action_description": action_description,
        "result": "",
        "error": f"工具调用异常: {str(e)}"
      })
  
  return results

def tool_results_to_str(results):
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