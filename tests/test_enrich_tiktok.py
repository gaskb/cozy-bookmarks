from app.integrations.metadata_extractor import PageMetadata
from app.orchestration import enrich_tiktok
from app.orchestration.enrich_tiktok import enrich_tiktok_metadata_safely, is_tiktok_url


def test_is_tiktok_url_recognizes_known_hosts():
    assert is_tiktok_url("https://www.tiktok.com/@nasa/video/123")
    assert is_tiktok_url("https://vm.tiktok.com/ZMabc123/")
    assert is_tiktok_url("https://vt.tiktok.com/ZMabc123/")


def test_is_tiktok_url_rejects_other_hosts():
    assert not is_tiktok_url("https://example.com")
    assert not is_tiktok_url("https://www.instagram.com/p/abc/")
    assert not is_tiktok_url("not-a-url")


def test_non_tiktok_url_is_left_unchanged():
    metadata = PageMetadata(title="Example", description="A page")

    updated, note = enrich_tiktok_metadata_safely("https://example.com", metadata)

    assert updated is metadata
    assert note is None


def test_tiktok_caption_with_link_produces_note_and_better_description(monkeypatch):
    monkeypatch.setattr(
        enrich_tiktok,
        "fetch_tiktok_caption",
        lambda url, **kwargs: "Guarda anche https://example.com/full-recipe per la ricetta completa",
    )
    metadata = PageMetadata(title="A TikTok", description="Log in to TikTok")

    updated, note = enrich_tiktok_metadata_safely("https://www.tiktok.com/@x/video/1", metadata)

    assert updated.description == "Guarda anche https://example.com/full-recipe per la ricetta completa"
    assert note == "Link citato nella caption: https://example.com/full-recipe"


def test_short_real_caption_wins_over_longer_generic_login_boilerplate(monkeypatch):
    # regression: found saving a real TikTok URL end-to-end - the generic
    # OpenGraph text scraped from TikTok's login wall is often *longer* than
    # the real (short) caption, so a length-based "pick the longer one"
    # comparison picks the useless boilerplate instead of the real content.
    monkeypatch.setattr(
        enrich_tiktok, "fetch_tiktok_caption", lambda url, **kwargs: "Something big just landed on TikTok."
    )
    metadata = PageMetadata(
        description=(
            "Log in or sign up for an account on TikTok. Start watching to "
            "discover real people and real videos that will make your day."
        )
    )

    updated, _ = enrich_tiktok_metadata_safely("https://www.tiktok.com/@nasa/video/1", metadata)

    assert updated.description == "Something big just landed on TikTok."


def test_tiktok_caption_without_link_updates_description_only(monkeypatch):
    monkeypatch.setattr(
        enrich_tiktok, "fetch_tiktok_caption", lambda url, **kwargs: "Solo una didascalia divertente"
    )
    metadata = PageMetadata(title="A TikTok", description=None)

    updated, note = enrich_tiktok_metadata_safely("https://www.tiktok.com/@x/video/1", metadata)

    assert updated.description == "Solo una didascalia divertente"
    assert note is None


def test_tiktok_caption_fetch_failure_leaves_metadata_unchanged(monkeypatch):
    def _boom(url, **kwargs):
        raise RuntimeError("network exploded")

    monkeypatch.setattr(enrich_tiktok, "fetch_tiktok_caption", _boom)
    metadata = PageMetadata(title="A TikTok", description="original")

    updated, note = enrich_tiktok_metadata_safely("https://www.tiktok.com/@x/video/1", metadata)

    assert updated.description == "original"
    assert note is None


def test_tiktok_no_caption_returned_leaves_metadata_unchanged(monkeypatch):
    monkeypatch.setattr(enrich_tiktok, "fetch_tiktok_caption", lambda url, **kwargs: None)
    metadata = PageMetadata(title="A TikTok", description="original")

    updated, note = enrich_tiktok_metadata_safely("https://www.tiktok.com/@x/video/1", metadata)

    assert updated is metadata
    assert note is None
