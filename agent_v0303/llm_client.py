"""
最小化 LLM 客户端，基于 agent_framework 的 OpenRouterClient。

基于 agent_framework.llm.OpenRouterClient 直接调用 OpenRouter 兼容格式的 Chat Completion API，
支持通过环境变量配置 key 与模型参数。

环境变量：
  OPENROUTER_API_KEY  – 必填，API 密钥
  OPENROUTER_MODEL    – 可选，模型名称，默认 qwen/qwen3-max
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# 将项目根目录加入 sys.path，以便导入 agent_framework
_project_root = Path(__file__).resolve().parents[1]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from agent_framework.llm import OpenRouterClient, load_env_file

_local_env = Path(__file__).resolve().with_name(".env")


class SimpleLLMClient:
    """简易 OpenAI 兼容 Chat Completion 客户端。"""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        max_tokens: int = 16384,
        temperature: float = 0.0,
        timeout: float = 120.0,
    ):
        # 先加载 .env，使 os.getenv 能读到文件中的变量。
        # load_env_file() 默认不查 agent_v0303/.env；这里补充本地文件，
        # 让从仓库根目录或 notebook 启动时也能读到同一份配置。
        load_env_file()
        load_env_file(_local_env)

        self.model = model or os.getenv("OPENROUTER_MODEL", "qwen/qwen3-max")
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

        if not self.api_key:
            raise RuntimeError(
                "未配置 API Key。请设置环境变量 OPENROUTER_API_KEY，"
                "或在初始化 SimpleLLMClient 时传入 api_key。"
            )

        self._client = OpenRouterClient(
            model=self.model,
            api_key=self.api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout,
        )

    def chat(self, prompt: str, system: Optional[str] = None) -> str:
        """
        发送单轮 chat 请求，返回模型生成的文本内容。
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self._client.chat(messages)


class LLMTool:
    """
    兼容原 graph_agent.llms.llm.LLMTool 调用接口的包装器。

    原接口调用方式：
      llm_tool = LLMTool("qwen3-max", llm)
      llm_tool.compile()
      response = llm_tool.invoke({"prompt": prompt})
      content_text = response["response"]["response"]["choices"][0]["message"]["content"]
    """

    def __init__(self, model_name: str, llm_client: SimpleLLMClient):
        self.model_name = model_name
        self._client = llm_client
        self._compiled = False

    def compile(self) -> "LLMTool":
        """空操作，仅保持接口兼容。"""
        self._compiled = True
        return self

    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        接收 {"prompt": ...}，返回与原接口嵌套格式一致的 dict。
        """
        if not self._compiled:
            raise RuntimeError("LLMTool 尚未 compile()")

        prompt = inputs.get("prompt", "")
        system = inputs.get("system")

        content = self._client.chat(prompt, system=system)

        # 构造与原 graph_agent 一致的嵌套响应格式
        return {
            "response": {
                "response": {
                    "choices": [
                        {
                            "message": {
                                "content": content
                            }
                        }
                    ]
                }
            }
        }
