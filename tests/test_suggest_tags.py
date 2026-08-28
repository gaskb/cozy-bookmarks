import pytest

from app.integrations.ai_provider import AIProvider, AIProviderError
from app.orchestration.suggest_tags import suggest_tags, suggest_tags_safely


class _StubProvider(AIProvider):
    def __init__(self, reply=None, error=None):
        self._reply = reply
        self._error = error

    def complete(self, messages):
        if self._error is not None:
            raise self._error
        return self._reply


def test_suggest_tags_parses_comma_separated_reply():
    provider = _StubProvider(reply="python, homelab, tutorial")

    tags = suggest_tags(provider, "https://example.com", "Title", "Description")

    assert tags == ["python", "homelab", "tutorial"]


def test_suggest_tags_strips_bullets_and_numbering_noise():
    provider = _StubProvider(reply="- python\n* homelab\n# tutorial")

    tags = suggest_tags(provider, "https://example.com", None, None)

    assert tags == ["python", "homelab", "tutorial"]


def test_suggest_tags_caps_at_five():
    provider = _StubProvider(reply="a, b, c, d, e, f, g")

    tags = suggest_tags(provider, "https://example.com", None, None)

    assert tags == ["a", "b", "c", "d", "e"]


def test_suggest_tags_drops_overly_long_candidates():
    long_tag = "x" * 40
    provider = _StubProvider(reply=f"python, {long_tag}")

    tags = suggest_tags(provider, "https://example.com", None, None)

    assert tags == ["python"]


def test_suggest_tags_propagates_provider_errors():
    provider = _StubProvider(error=AIProviderError("boom"))

    with pytest.raises(AIProviderError):
        suggest_tags(provider, "https://example.com", None, None)


def test_suggest_tags_safely_returns_empty_on_provider_error():
    provider = _StubProvider(error=AIProviderError("boom"))

    tags = suggest_tags_safely(provider, "https://example.com", None, None)

    assert tags == []


def test_suggest_tags_safely_returns_empty_on_unexpected_error():
    provider = _StubProvider(error=RuntimeError("boom"))

    tags = suggest_tags_safely(provider, "https://example.com", None, None)

    assert tags == []
