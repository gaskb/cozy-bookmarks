from app.integrations.ai_provider import get_active_provider
from app.integrations.ai_provider_claude import ClaudeProvider
from app.integrations.ai_provider_local import LocalLLMProvider


def test_defaults_to_local_provider(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ai_provider", "local")

    provider = get_active_provider()

    assert isinstance(provider, LocalLLMProvider)


def test_selects_claude_provider_when_configured(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ai_provider", "claude")
    monkeypatch.setattr(settings, "ai_claude_api_key", "test-key")

    provider = get_active_provider()

    assert isinstance(provider, ClaudeProvider)
