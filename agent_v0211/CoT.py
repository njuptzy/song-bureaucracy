"""
CoT 思维链相关功能与函数实现
"""

from __future__ import annotations

import json
from typing import TypedDict, List, Any, Dict, Optional, Union, Callable
from datetime import datetime, timezone

from agent_state import AgentState


class ToolCall(TypedDict):
  """工具调用结构，参考 prompt_input2facts.py 中的定义"""
  tool: str  # 工具名称：search_dictionary, add_atomic_fact, remove_atomic_fact, update_atomic_fact
  parameters: Dict[str, Any]  # 工具参数


class ActionResult(TypedDict):
  """工具调用结果结构"""
  tool: str
  parameters: Dict[str, Any]
  status: str  # "success" 或 "failed"
  error: Optional[str]  # 如果失败，记录错误信息
  observation: Optional[str]  # 工具返回的观察结果（可选）


class CoT(TypedDict):
  """CoT 思维链结构"""
  role: str  # "agent", "system", "user"
  type: str  # "thought", "action", "observation"
  content: Any  # 内容，根据 type 不同而不同：
                 # - thought: str (思考内容)
                 # - action: Union[str, List[ToolCall]] (行动，可以是 "Tasks All Finished" 或工具调用列表)
                 # - observation: str (观察结果)


def cot_to_str(cots: List[CoT]) -> str:
  """
  将 CoT 思维链列表转换为可读字符串。
  
  Args:
    cots: CoT 思维链列表
    
  Returns:
    格式化的字符串
  """
  if not cots:
    return "（暂无 CoT 记录）"
  
  lines = []
  for i, cot in enumerate(cots, 1):
    role = cot.get("role", "unknown")
    cot_type = cot.get("type", "unknown")
    content = cot.get("content", "")
    
    header = f"[{i}] {role} - {cot_type}"
    lines.append(header)
    
    if cot_type == "thought":
      lines.append(f"  思考: {content}")
    elif cot_type == "action":
      if isinstance(content, str):
        lines.append(f"  行动: {content}")
      elif isinstance(content, list):
        lines.append("  工具调用:")
        for j, tool_call in enumerate(content, 1):
          if isinstance(tool_call, dict):
            tool_name = tool_call.get("tool", "unknown")
            params = tool_call.get("parameters", {})
            lines.append(f"    [{j}] {tool_name}")
            params_str = json.dumps(params, ensure_ascii=False, indent=6)
            lines.append(f"      参数: {params_str}")
          else:
            lines.append(f"    [{j}] {str(tool_call)}")
      else:
        lines.append(f"  行动: {str(content)}")
    elif cot_type == "observation":
      if content:
        # 如果内容较长，截断显示
        content_str = str(content)
        if len(content_str) > 200:
          content_str = content_str[:200] + "..."
        lines.append(f"  观察: {content_str}")
      else:
        lines.append("  观察: （空）")
    else:
      lines.append(f"  内容: {str(content)}")
    
    lines.append("")  # 空行分隔
  
  return "\n".join(lines)


def exec_action(
  action: Union[str, List[ToolCall]],
  tools: Dict[str, Callable],
  agent_state: AgentState
) -> tuple[Union[str, List[ActionResult]], Optional[str]]:
  """
  执行 action 中的工具调用。
  
  如果 action 为工具调用列表，则根据调用请求从 tools 字典中查找对应的工具函数并执行。
  工具的返回值分成两部分：
    * status: 工具调用结果，成功或失败以及失败原因
    * observation: （可选）具体的工具返回值；部分情况下工具的返回值直接体现在其他上下文中，此部分留空
  
  本函数只负责工具调用准备、执行和信息填充，不涉及具体工具的实现逻辑。
  执行完成后，会在 agent_state 的 CoT 记录中添加工具调用相关事件。
  
  Args:
    action: 行动内容，可以是 "Tasks All Finished" 字符串，或工具调用列表
    tools: 工具字典，key 为工具名称，value 为工具函数（Callable）
    agent_state: Agent 状态实例，用于更新上下文和记录 CoT
    
  Returns:
    (new_action, observation) 元组：
      - new_action: 更新后的 action（添加了 status 和 error 字段的 ActionResult 列表）
      - observation: 整体的观察结果摘要（可选）
  """
  # 如果 action 是字符串（如 "Tasks All Finished"），直接返回
  if isinstance(action, str):
    return action, None
  
  # 如果 action 不是列表，返回错误
  if not isinstance(action, list):
    return action, "错误：action 格式不正确，应为字符串或工具调用列表"
  
  results: List[ActionResult] = []
  observations: List[str] = []
  
  for tool_call in action:
    if not isinstance(tool_call, dict):
      result = {
        "tool": "unknown",
        "parameters": {},
        "status": "failed",
        "error": "工具调用格式不正确",
        "observation": None
      }
      results.append(result)
      # 记录到 CoT
      agent_state.add_cot_event(
        type="tool_call",
        message=f"工具调用失败：格式不正确",
        data={"result": result}
      )
      continue
    
    tool_name = tool_call.get("tool", "")
    parameters = tool_call.get("parameters", {})
    
    if not tool_name:
      result = {
        "tool": "unknown",
        "parameters": parameters,
        "status": "failed",
        "error": "缺少工具名称",
        "observation": None
      }
      results.append(result)
      # 记录到 CoT
      agent_state.add_cot_event(
        type="tool_call",
        message=f"工具调用失败：缺少工具名称",
        data={"result": result}
      )
      continue
    
    # 检查工具是否存在
    if tool_name not in tools:
      result = {
        "tool": tool_name,
        "parameters": parameters,
        "status": "failed",
        "error": f"工具 '{tool_name}' 不存在于 tools 字典中",
        "observation": None
      }
      results.append(result)
      # 记录到 CoT
      agent_state.add_cot_event(
        type="tool_call",
        message=f"工具调用失败：工具 '{tool_name}' 不存在",
        data={"result": result}
      )
      continue
    
    # 获取工具函数
    tool_func = tools[tool_name]
    
    # 执行工具调用
    try:
      # 记录工具调用开始
      agent_state.add_cot_event(
        type="tool_call",
        message=f"调用工具：{tool_name}",
        data={"tool": tool_name, "parameters": parameters}
      )
      
      # 调用工具函数（工具函数应该接收 parameters 和 agent_state 作为参数）
      # 工具函数返回格式：{"status": "success"/"failed", "error": Optional[str], "observation": Optional[str]}
      tool_result = tool_func(parameters, agent_state)
      
      # 处理工具返回结果
      if isinstance(tool_result, dict):
        status = tool_result.get("status", "success")
        error = tool_result.get("error")
        observation = tool_result.get("observation")
      else:
        # 如果工具返回的不是字典，假设成功
        status = "success"
        error = None
        observation = str(tool_result) if tool_result else None
      
      result: ActionResult = {
        "tool": tool_name,
        "parameters": parameters,
        "status": status,
        "error": error,
        "observation": observation
      }
      results.append(result)
      
      # 记录工具调用结果
      agent_state.add_cot_event(
        type="tool_result",
        message=f"工具调用结果：{tool_name} - {status}",
        data={"result": result}
      )
      
      if status == "success" and observation:
        observations.append(f"{tool_name}: {observation}")
      elif status == "failed" and error:
        observations.append(f"{tool_name} 失败: {error}")
    
    except Exception as e:
      result = {
        "tool": tool_name,
        "parameters": parameters,
        "status": "failed",
        "error": f"工具执行异常: {str(e)}",
        "observation": None
      }
      results.append(result)
      # 记录错误到 CoT
      agent_state.add_cot_event(
        type="error",
        message=f"工具调用异常：{tool_name}",
        data={"result": result, "exception": str(e)}
      )
      observations.append(f"{tool_name} 执行异常: {str(e)}")
  
  # 生成整体观察结果
  observation_summary = None
  if observations:
    observation_summary = "\n".join(observations)
  
  return results, observation_summary
