import json

import httpx
import pytest

from app.integrations.ai_provider import AIProviderError, ChatMessage
from app.integrations.ai_provider_local import LocalLLMProvider


def _provider_for(handler, api_key: str = "") -> LocalLLMProvider:
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return LocalLLMProvider(
        base_url="http://ai.local/v1", model="test-model", api_key=api_key, client=client
    )


def test_complete_returns_message_content():
    def handler(request):
        assert request.url.path == "/v1/chat/completions"
        return httpx.Response(200, json={"choices": [{"message": {"content": "hello there"}}]})

    provider = _provider_for(handler)

    result = provider.complete([ChatMessage(role="user", content="hi")])

    assert result == "hello there"


def test_complete_sends_messages_as_payload():
    captured = {}

    def handler(request):
        captured["body"] = request.content
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    provider = _provider_for(handler)
    provider.complete(
        [ChatMessage(role="system", content="sys"), ChatMessage(role="user", content="hi")]
    )

    body = json.loads(captured["body"])
    assert body["model"] == "test-model"
    assert body["messages"] == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hi"},
    ]


def test_complete_sends_bearer_token_when_api_key_set():
    captured = {}

    def handler(request):
        captured["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    provider = _provider_for(handler, api_key="secret-token")
    provider.complete([ChatMessage(role="user", content="hi")])

    assert captured["auth"] == "Bearer secret-token"


def test_complete_omits_auth_header_when_no_api_key():
    captured = {}

    def handler(request):
        captured["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    provider = _provider_for(handler)
    provider.complete([ChatMessage(role="user", content="hi")])

    assert captured["auth"] is None


def test_complete_raises_on_http_error():
    def handler(request):
        return httpx.Response(500, text="boom")

    provider = _provider_for(handler)

    with pytest.raises(AIProviderError):
        provider.complete([ChatMessage(role="user", content="hi")])


def test_complete_raises_on_unexpected_shape():
    def handler(request):
        return httpx.Response(200, json={"unexpected": "shape"})

    provider = _provider_for(handler)

    with pytest.raises(AIProviderError):
        provider.complete([ChatMessage(role="user", content="hi")])


def test_complete_raises_on_invalid_json():
    def handler(request):
        return httpx.Response(200, text="not json")

    provider = _provider_for(handler)

    with pytest.raises(AIProviderError):
        provider.complete([ChatMessage(role="user", content="hi")])


def test_complete_raises_on_timeout():
    def handler(request):
        raise httpx.TimeoutException("timed out", request=request)

    provider = _provider_for(handler)

    with pytest.raises(AIProviderError):
        provider.complete([ChatMessage(role="user", content="hi")])
