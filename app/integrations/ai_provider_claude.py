from __future__ import annotations

import anthropic

from app.integrations.ai_provider import AIProvider, AIProviderError, ChatMessage

MAX_TOKENS = 256


class ClaudeProvider(AIProvider):
    def __init__(
        self,
        api_key: str,
        model: str,
        timeout: float = 30.0,
        client: anthropic.Anthropic | None = None,
    ):
        self._client = client or anthropic.Anthropic(api_key=api_key, timeout=timeout)
        self._model = model

    def complete(self, messages: list[ChatMessage]) -> str:
        system_prompt = "\n".join(m.content for m in messages if m.role == "system")
        chat_messages = [
            {"role": m.role, "content": m.content} for m in messages if m.role != "system"
        ]

        kwargs: dict = {
            "model": self._model,
            "max_tokens": MAX_TOKENS,
            "messages": chat_messages,
            "output_config": {"effort": "low"},
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        try:
            response = self._client.messages.create(**kwargs)
        except anthropic.RateLimitError as exc:
            raise AIProviderError(f"Claude rate limited: {exc}") from exc
        except anthropic.APIStatusError as exc:
            raise AIProviderError(f"Claude API error ({exc.status_code}): {exc.message}") from exc
        except anthropic.APIConnectionError as exc:
            raise AIProviderError(f"Claude connection error: {exc}") from exc

        if response.stop_reason == "refusal":
            raise AIProviderError("Claude refused the request")

        text = next((block.text for block in response.content if block.type == "text"), None)
        if text is None:
            raise AIProviderError("Claude returned no text content")
        return text
