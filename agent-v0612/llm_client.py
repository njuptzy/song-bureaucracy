"""
最小化 LLM 客户端，基于 agent_framework 的 OpenRouterClient。

基于 agent_framework.llm.OpenRouterClient 直接调用 OpenRouter 兼容格式的 Chat Completion API，
支持通过环境变量配置 key 与模型参数。

v0612 修复（针对 v0304 批跑中 79 个词条整条失败的问题）：
  * chat() 内置自动重试（指数退避）。v0304 批跑使用的 graph_agent 框架在 API
    调用失败时静默返回 None，notebook 取下标直接崩溃且无重试，一次 API 抖动
    即废掉整个词条；
  * 对返回内容做显式校验：内容为空时抛出带上下文的 RuntimeError，绝不向调用
    方返回 None；
  * 4xx 客户端错误（除 429 限流外）不重试，立即抛出，避免对认证/参数错误做
    无意义的退避等待。

环境变量：
  LLM_PROFILE          – 当前 provider 名称，例如 opencode_go；
  <PROFILE>_API_KEY    – 当前 provider 自己的 API 密钥；
  <PROFILE>_MODEL      – 模型 ID；
  <PROFILE>_BASE_URL   – OpenAI 兼容 Chat Completions 端点；
  <PROFILE>_MAX_TOKENS – 最大输出 token 数。
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

# 将项目根目录加入 sys.path，以便导入 agent_framework
_project_root = Path(__file__).resolve().parents[1]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import json as _json

from agent_framework.llm import OpenRouterClient, load_env_file

_local_env = Path(__file__).resolve().with_name(".env")


class SimpleLLMClient:
    """简易 OpenAI 兼容 Chat Completion 客户端，带自动重试。"""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        max_tokens: int = 16384,
        temperature: float = 0.0,
        timeout: float = 120.0,
        max_retries: int = 5,
        retry_base_delay: float = 2.0,
        retry_max_delay: float = 60.0,
        base_url: Optional[str] = None,
    ):
        # 先加载 .env，使 os.getenv 能读到文件中的变量。
        # load_env_file() 默认不查 agent-v0612/.env；这里补充本地文件，
        # 让从仓库根目录或 notebook 启动时也能读到同一份配置。
        load_env_file()
        load_env_file(_local_env)

        # ===== Provider profile 机制 =====
        # 由 LLM_PROFILE 选择激活的 provider，取其 <PROFILE>_API_KEY /
        # <PROFILE>_BASE_URL / <PROFILE>_MODEL / <PROFILE>_MAX_TOKENS。
        # 显式构造参数（model/api_key/base_url/max_tokens）优先级最高，
        # 用于一次性临时覆盖。只有当前 profile 本身是 OPENROUTER 时才读
        # OPENROUTER_*；自定义 provider 缺配置必须立即失败，不能把其他
        # 平台的 key 静默发到当前端点。
        profile = (os.getenv("LLM_PROFILE") or "").strip().upper() or "OPENROUTER"
        self.profile = profile

        self.model = model or os.getenv(f"{profile}_MODEL")
        self.api_key = api_key or os.getenv(f"{profile}_API_KEY")
        resolved_base_url = base_url or os.getenv(f"{profile}_BASE_URL")
        if profile == "OPENROUTER":
            self.model = self.model or "deepseek-chat"
            self.api_key = self.api_key or os.getenv("OPENROUTER_API_KEY")
            resolved_base_url = resolved_base_url or os.getenv("OPENROUTER_BASE_URL")
        # max_tokens 显式传入优先；否则按 profile 读；最后回落到默认值
        env_max_tokens = os.getenv(f"{profile}_MAX_TOKENS")
        if env_max_tokens and max_tokens == 16384:
            # 16384 是构造函数默认值，说明调用方没显式指定，此时优先用 .env 值
            try:
                max_tokens = int(env_max_tokens)
            except ValueError:
                pass
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.stream = (
            os.getenv(f"{profile}_STREAM", "").strip().lower()
            in {"1", "true", "yes", "on"}
        )
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        self.retry_max_delay = retry_max_delay

        if not self.api_key:
            raise RuntimeError(
                f"未配置 API Key。当前 LLM_PROFILE={profile.lower()}，"
                f"请在 .env 设置 {profile}_API_KEY 等四个变量，"
                f"或切换 LLM_PROFILE 到已配置的 provider。"
            )
        if not self.model:
            raise RuntimeError(
                f"未配置模型。请在 .env 设置 {profile}_MODEL。"
            )
        if not resolved_base_url:
            raise RuntimeError(
                f"未配置 API 端点。请在 .env 设置 {profile}_BASE_URL。"
            )

        # provider-specific 额外请求体字段（JSON 字符串）：
        # 例 NVIDIA 关 thinking → NVIDIA_EXTRA_BODY='{"chat_template_kwargs":{"thinking":false}}'
        extra_body_raw = os.getenv(f"{profile}_EXTRA_BODY", "").strip()
        extra_body = None
        if extra_body_raw:
            try:
                extra_body = _json.loads(extra_body_raw)
            except _json.JSONDecodeError as e:
                raise RuntimeError(
                    f"{profile}_EXTRA_BODY 不是合法 JSON：{e}（原文前 80 字: {extra_body_raw[:80]!r}）"
                )

        self._client = OpenRouterClient(
            model=self.model,
            api_key=self.api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout,
            base_url=resolved_base_url,
            extra_body=extra_body,
        )
        self.extra_body = extra_body or {}
        self.base_url = self._client.base_url

    def _chat_stream(self, messages) -> str:
        """读取 OpenAI-compatible SSE，持续接收推理片段但只返回正文。"""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
            **self.extra_body,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        content_parts = []
        finish_reason = ""
        saw_done = False
        usage: Dict[str, Any] = {}
        with httpx.Client(timeout=self.timeout) as client:
            with client.stream(
                "POST",
                self.base_url,
                json=payload,
                headers=headers,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if not raw:
                        continue
                    if raw == "[DONE]":
                        saw_done = True
                        continue
                    data = _json.loads(raw)
                    if data.get("usage"):
                        usage = data["usage"]
                    choices = data.get("choices") or []
                    if not choices:
                        continue
                    choice = choices[0]
                    finish_reason = choice.get("finish_reason") or finish_reason
                    delta = choice.get("delta") or {}
                    content = delta.get("content")
                    if content:
                        content_parts.append(content)
        content = "".join(content_parts)
        completion_tokens = usage.get("completion_tokens")
        completion_details = usage.get("completion_tokens_details") or {}
        reasoning_tokens = completion_details.get("reasoning_tokens")
        usage_text = (
            f", completion_tokens={completion_tokens or 'unknown'}, "
            f"reasoning_tokens={reasoning_tokens or 'unknown'}"
        )
        if finish_reason == "length":
            raise RuntimeError(
                "流式响应达到输出 token 上限，"
                f"finish_reason=length, max_tokens={self.max_tokens}{usage_text}"
            )
        if not saw_done:
            raise RuntimeError(
                "流式响应未收到 [DONE]，可能提前断流，"
                f"finish_reason={finish_reason or 'unknown'}{usage_text}"
            )
        if not content:
            raise RuntimeError(
                "流式响应没有 message.content，"
                f"finish_reason={finish_reason or 'unknown'}{usage_text}"
            )
        return content

    def chat(self, prompt: str, system: Optional[str] = None) -> str:
        """
        发送单轮 chat 请求，返回模型生成的文本内容。

        失败时自动重试（指数退避），重试耗尽后抛出 RuntimeError。
        返回值保证为非空字符串，调用方无需再做 None 检查。
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                content = (
                    self._chat_stream(messages)
                    if self.stream
                    else self._client.chat(messages)
                )
                if not content or not content.strip():
                    raise RuntimeError("LLM 返回内容为空")
                return content
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                # 429（限流）和 5xx 值得重试；其余 4xx 是请求本身的问题，立即抛出
                if 400 <= status < 500 and status != 429:
                    raise
                last_error = e
            except (httpx.HTTPError, RuntimeError, ValueError) as e:
                last_error = e

            if attempt < self.max_retries:
                delay = min(self.retry_base_delay * (2 ** attempt), self.retry_max_delay)
                print(
                    f"LLM 调用失败（第 {attempt + 1}/{self.max_retries + 1} 次）："
                    f"{last_error}，{delay:.0f} 秒后重试"
                )
                time.sleep(delay)

        raise RuntimeError(
            f"LLM 调用在 {self.max_retries + 1} 次尝试后仍然失败：{last_error}"
        ) from last_error


class LLMTool:
    """
    兼容原 graph_agent.llms.llm.LLMTool 调用接口的包装器。

    原接口调用方式：
      llm_tool = LLMTool("qwen3-max", llm)
      llm_tool.compile()
      response = llm_tool.invoke({"prompt": prompt})
      content_text = response["response"]["response"]["choices"][0]["message"]["content"]

    注意：v0612 的 agent.ipynb 已改为直接调用 SimpleLLMClient.chat()，
    不再使用本包装器；保留它仅为兼容旧 notebook。由于 chat() 保证返回
    非空字符串，本包装器构造的嵌套结构中不会出现 None。
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
