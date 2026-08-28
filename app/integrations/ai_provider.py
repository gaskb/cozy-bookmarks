from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ChatMessage:
    role: str
    content: str


class AIProviderError(Exception):
    pass


class AIProvider(ABC):
    @abstractmethod
    def complete(self, messages: list[ChatMessage]) -> str: ...


def get_active_provider() -> AIProvider:
    from app.config import settings

    if settings.ai_provider == "claude":
        from app.integrations.ai_provider_claude import ClaudeProvider

        return ClaudeProvider(
            api_key=settings.ai_claude_api_key,
            model=settings.ai_claude_model,
            timeout=settings.ai_timeout_seconds,
        )

    # Everything else (self-hosted LLM, Qwen, OpenAI/ChatGPT, ...) speaks the
    # same OpenAI-compatible wire format - which one it is is just config.
    from app.integrations.ai_provider_openai_compatible import OpenAICompatibleProvider

    return OpenAICompatibleProvider(
        base_url=settings.ai_openai_compatible_base_url,
        model=settings.ai_openai_compatible_model,
        api_key=settings.ai_openai_compatible_api_key,
        timeout=settings.ai_timeout_seconds,
    )
