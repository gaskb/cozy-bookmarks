from __future__ import annotations

import httpx

from app.integrations.ai_provider import AIProvider, AIProviderError, ChatMessage


class OpenAICompatibleProvider(AIProvider):
    # works for any /chat/completions-shaped service (self-hosted LLM, Qwen, OpenAI) via config alone
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: float = 30.0,
        api_key: str = "",
        client: httpx.Client | None = None,
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._api_key = api_key
        self._client = client

    def complete(self, messages: list[ChatMessage]) -> str:
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}

        owns_client = self._client is None
        http_client = self._client or httpx.Client()
        try:
            response = http_client.post(
                f"{self._base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self._timeout,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise AIProviderError(f"OpenAI-compatible request failed: {exc}") from exc
        except ValueError as exc:
            raise AIProviderError(f"OpenAI-compatible response was not valid JSON: {exc}") from exc
        finally:
            if owns_client:
                http_client.close()

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderError(f"OpenAI-compatible response had an unexpected shape: {exc}") from exc
