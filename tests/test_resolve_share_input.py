from app.orchestration.resolve_share_input import resolve_shared_url


def test_prefers_explicit_url():
    assert resolve_shared_url("https://a.example.com", "text with https://b.example.com") == (
        "https://a.example.com"
    )


def test_extracts_url_from_text_when_url_missing():
    assert resolve_shared_url(None, "check this https://vm.tiktok.com/abc123 out") == (
        "https://vm.tiktok.com/abc123"
    )


def test_returns_none_when_nothing_found():
    assert resolve_shared_url(None, "no link here") is None
    assert resolve_shared_url("", "") is None
    assert resolve_shared_url(None, None) is None
