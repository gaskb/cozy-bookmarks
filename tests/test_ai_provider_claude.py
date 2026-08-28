import anthropic
import httpx
import pytest

from app.integrations.ai_provider import AIProviderError, ChatMessage
from app.integrations.ai_provider_claude import ClaudeProvider


class _FakeTextBlock:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _FakeResponse:
    def __init__(self, text, stop_reason="end_turn"):
        self.content = [_FakeTextBlock(text)] if text is not None else []
        self.stop_reason = stop_reason


class _FakeMessages:
    def __init__(self, respond_with=None, raise_with=None, captured=None):
        self._respond_with = respond_with
        self._raise_with = raise_with
        self._captured = captured

    def create(self, **kwargs):
        if self._captured is not None:
            self._captured.update(kwargs)
        if self._raise_with is not None:
            raise self._raise_with
        return self._respond_with


class _FakeClient:
    def __init__(self, **kwargs):
        self.messages = _FakeMessages(**kwargs)


def _provider_with(**kwargs) -> ClaudeProvider:
    return ClaudeProvider(api_key="x", model="claude-opus-5", client=_FakeClient(**kwargs))


def test_complete_returns_text_content():
    provider = _provider_with(respond_with=_FakeResponse("python, homelab"))

    result = provider.complete([ChatMessage(role="user", content="hi")])

    assert result == "python, homelab"


def test_complete_moves_system_role_out_of_messages():
    captured = {}
    provider = _provider_with(respond_with=_FakeResponse("ok"), captured=captured)

    provider.complete([ChatMessage(role="system", content="sys"), ChatMessage(role="user", content="hi")])

    assert captured["system"] == "sys"
    assert captured["messages"] == [{"role": "user", "content": "hi"}]
    assert captured["max_tokens"] == 256


def test_complete_raises_on_refusal():
    provider = _provider_with(respond_with=_FakeResponse("", stop_reason="refusal"))

    with pytest.raises(AIProviderError):
        provider.complete([ChatMessage(role="user", content="hi")])


def test_complete_raises_when_no_text_block():
    provider = _provider_with(respond_with=_FakeResponse(None))

    with pytest.raises(AIProviderError):
        provider.complete([ChatMessage(role="user", content="hi")])


def test_complete_raises_on_rate_limit():
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx.Response(429, request=request)
    error = anthropic.RateLimitError("rate limited", response=response, body=None)
    provider = _provider_with(raise_with=error)

    with pytest.raises(AIProviderError):
        provider.complete([ChatMessage(role="user", content="hi")])


def test_complete_raises_on_connection_error():
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    error = anthropic.APIConnectionError(message="connection failed", request=request)
    provider = _provider_with(raise_with=error)

    with pytest.raises(AIProviderError):
        provider.complete([ChatMessage(role="user", content="hi")])
