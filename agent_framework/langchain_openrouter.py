from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from agent_framework.llm import OpenRouterClient


class OpenRouterChatModel(BaseChatModel):
    """LangChain chat model wrapper for the existing OpenRouter HTTP client."""

    model: str | None = None
    api_key: str | None = None
    temperature: float = 0
    max_tokens: int = 4096

    def _message_to_dict(self,  message: BaseMessage) -> dict[str, str]:
        role: str = "user"

        if message.type == "system":
            role = "system"
        elif message.type == "human":
            role = "user"
        elif message.type == "ai":
            role = "assistant"

        return {
            "role": role,
            "content": str(message.content),
        }

    def _messages_to_dicts(
        self,
        messages: list[BaseMessage],
    ) -> list[dict[str, str]]:
        result: list[dict[str, str]] = []

        for message in messages:
            result.append(self._message_to_dict(message))

        return result

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs,
    ) -> ChatResult:
        client = OpenRouterClient(
            model=self.model,
            api_key=self.api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        response_text: str = client.chat(self._messages_to_dicts(messages))
        ai_message: AIMessage = AIMessage(content=response_text)
        generation: ChatGeneration = ChatGeneration(message=ai_message)

        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "openrouter-chat-model"
