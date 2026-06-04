import os
from pathlib import Path

import httpx


BRANCH_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = BRANCH_ROOT.parent


def load_env_file(path=None):
    if path is None:
        paths = [Path(".env"), BRANCH_ROOT / ".env", REPOSITORY_ROOT / ".env"]
    else:
        paths = [Path(path)]

    seen_paths = set()

    for env_path in paths:
        env_path = env_path.resolve()

        if env_path in seen_paths or not env_path.exists():
            continue

        seen_paths.add(env_path)

        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


class OpenRouterClient:
    """Small wrapper around OpenRouter's OpenAI-compatible chat API."""

    def __init__(self, model=None, api_key=None, temperature=0.3, max_tokens=4096, timeout=60):
        load_env_file()
        if api_key is None:
            self.api_key = os.getenv("OPENROUTER_API_KEY")
        else:
            self.api_key = api_key

        if model is None:
            self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        else:
            self.model = model

        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def chat_raw(self, messages):
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            raise RuntimeError(
                "Missing OPENROUTER_API_KEY. Set it in your shell before running."
            )

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    def chat(self, messages):
        data = self.chat_raw(messages)
        choices = data.get("choices", [])
        if len(choices) == 0:
            raise RuntimeError("OpenRouter response has no choices.")

        first_choice = choices[0]
        message = first_choice.get("message", {})
        content = message.get("content")

        if content is None:
            finish_reason = first_choice.get("finish_reason", "")
            raise RuntimeError(
                "OpenRouter returned empty message content. "
                "finish_reason: " + str(finish_reason)
            )

        return content
