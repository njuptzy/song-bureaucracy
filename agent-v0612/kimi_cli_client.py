"""通过子进程调用 kimi CLI，把它包装成 SimpleLLMClient.chat() 同款接口。

为什么是子进程而不是 HTTP：Kimi For Coding 端的访问控制不只是 User-Agent，
还含 OAuth session token / 动态签名，纯 HTTP 模仿过不去。直接跑真实 `kimi` 进程
让它用自己的合法身份完成协议握手，是合规且稳定的接入方式。

要求：本机已安装 kimi-code（默认路径 ~/.kimi-code/bin/kimi），且已登录。
非交互模式：`kimi -p <prompt> --output-format stream-json`，每行一个 JSON。
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Optional

DEFAULT_KIMI_BIN = Path.home() / ".kimi-code" / "bin" / "kimi"
# Agent 专用 kimi-cli 配置目录（关掉 thinking 模式，避免每轮额外 30~60 秒推理延迟）。
# 通过 KIMI_CODE_HOME 隔离，不影响用户日常用 kimi 客户端时的 thinking 体验。
# oauth/credentials/device_id 通过符号链接共享，无需重新登录。
DEFAULT_KIMI_HOME = Path.home() / ".kimi-code-agent"


class KimiCliClient:
    """与 SimpleLLMClient 接口一致：chat(prompt) -> str。"""

    def __init__(
        self,
        model: Optional[str] = None,
        max_tokens: int = 12000,        # 兼容签名，kimi-cli 不用
        max_retries: int = 3,
        retry_base_delay: float = 2.0,
        retry_max_delay: float = 60.0,
        timeout: float = 120.0,
        kimi_bin: Optional[str] = None,
        kimi_home: Optional[str] = None,
    ):
        self.model = model              # 传给 kimi -m；None 则用其默认
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        self.retry_max_delay = retry_max_delay
        self.timeout = timeout
        bin_path = Path(kimi_bin) if kimi_bin else DEFAULT_KIMI_BIN
        if not bin_path.exists():
            raise FileNotFoundError(
                f"未找到 kimi 可执行文件：{bin_path}。请确认 kimi-code 已安装并登录。"
            )
        self.kimi_bin = str(bin_path)
        # KIMI_CODE_HOME 优先级：构造参数 > 环境变量 > 默认 ~/.kimi-code-agent。
        # 用 agent 专用配置目录避免污染用户日常 kimi 客户端体验。
        home = kimi_home or os.getenv("KIMI_CODE_HOME") or str(DEFAULT_KIMI_HOME)
        if not Path(home).exists():
            raise FileNotFoundError(
                f"未找到 kimi 配置目录：{home}。"
                f"建议先建好 agent 专用配置："
                f"mkdir -p {home} && cp ~/.kimi-code/config.toml {home}/ && "
                f"ln -s ~/.kimi-code/oauth {home}/ && "
                f"ln -s ~/.kimi-code/credentials {home}/ && "
                f"ln -s ~/.kimi-code/device_id {home}/"
            )
        self.kimi_home = home

    def chat(self, prompt: str) -> str:
        cmd = [self.kimi_bin, "-p", prompt, "--output-format", "stream-json"]
        if self.model:
            cmd.extend(["-m", self.model])

        # 用 agent 专用 KIMI_CODE_HOME 覆盖默认 ~/.kimi-code，
        # 让 kimi 子进程读到我们准备好的关 thinking 配置。
        env = os.environ.copy()
        env["KIMI_CODE_HOME"] = self.kimi_home

        last_err: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    env=env,
                )
                if proc.returncode != 0:
                    raise RuntimeError(
                        f"kimi 子进程退出码 {proc.returncode}: "
                        f"{(proc.stderr or proc.stdout or '').strip()[:500]}"
                    )
                content = self._parse_stream_json(proc.stdout)
                if not content:
                    raise RuntimeError(
                        f"kimi 输出无 assistant content，原始 stdout 前 300 字: "
                        f"{proc.stdout[:300]!r}"
                    )
                return content
            except subprocess.TimeoutExpired as e:
                last_err = e
                err_desc = f"kimi 子进程超时（{self.timeout}s）"
            except Exception as e:
                last_err = e
                err_desc = f"{type(e).__name__}: {e}"

            if attempt >= self.max_retries:
                break
            delay = min(self.retry_base_delay * (2 ** (attempt - 1)), self.retry_max_delay)
            print(f"kimi 调用失败（第 {attempt}/{self.max_retries} 次）：{err_desc}，{delay:.1f} 秒后重试")
            time.sleep(delay)

        raise RuntimeError(f"LLM 调用在 {self.max_retries} 次重试后仍失败: {last_err}")

    @staticmethod
    def _parse_stream_json(stdout: str) -> str:
        """逐行解析 stream-json，提取 role=assistant 的 content。

        kimi stream-json 每行一个 JSON 对象：
          {"role":"assistant","content":"..."}
          {"role":"meta","type":"session.resume_hint", ...}
        若有多行 assistant，拼接（实测一般只有一行）。
        """
        chunks = []
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("role") == "assistant" and obj.get("content"):
                chunks.append(obj["content"])
        return "".join(chunks)
