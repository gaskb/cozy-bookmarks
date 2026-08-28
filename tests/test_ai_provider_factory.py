from app.integrations.ai_provider import get_active_provider
from app.integrations.ai_provider_claude import ClaudeProvider
from app.integrations.ai_provider_openai_compatible import OpenAICompatibleProvider


def test_defaults_to_openai_compatible_provider(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ai_provider", "openai_compatible")

    provider = get_active_provider()

    assert isinstance(provider, OpenAICompatibleProvider)


def test_any_non_claude_value_routes_to_openai_compatible(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ai_provider", "qwen")
    monkeypatch.setattr(settings, "ai_openai_compatible_base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    monkeypatch.setattr(settings, "ai_openai_compatible_model", "qwen-plus")

    provider = get_active_provider()

    assert isinstance(provider, OpenAICompatibleProvider)


def test_selects_claude_provider_when_configured(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ai_provider", "claude")
    monkeypatch.setattr(settings, "ai_claude_api_key", "test-key")

    provider = get_active_provider()

    assert isinstance(provider, ClaudeProvider)
