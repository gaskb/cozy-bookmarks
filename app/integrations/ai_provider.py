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
    from app.integrations.ai_provider_local import LocalLLMProvider

    if settings.ai_provider == "claude":
        from app.integrations.ai_provider_claude import ClaudeProvider

        return ClaudeProvider(
            api_key=settings.ai_claude_api_key,
            model=settings.ai_claude_model,
            timeout=settings.ai_timeout_seconds,
        )

    return LocalLLMProvider(
        base_url=settings.ai_local_base_url,
        model=settings.ai_local_model,
        api_key=settings.ai_local_api_key,
        timeout=settings.ai_timeout_seconds,
    )
