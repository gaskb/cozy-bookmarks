from app.integrations.metadata_extractor import PageMetadata
from app.orchestration import save_bookmark
from app.orchestration.save_bookmark import save_bookmark_with_metadata


def test_save_bookmark_uses_extracted_metadata(db_session, user, monkeypatch):
    monkeypatch.setattr(
        save_bookmark,
        "fetch_metadata",
        lambda url: PageMetadata(
            title="Extracted title",
            description="Extracted description",
            image_url="https://example.com/cover.png",
            favicon_url="https://example.com/favicon.ico",
        ),
    )

    bookmark = save_bookmark_with_metadata(db_session, user_id=user.id, url="https://example.com")

    assert bookmark.title == "Extracted title"
    assert bookmark.description == "Extracted description"
    assert bookmark.image_url == "https://example.com/cover.png"
    assert bookmark.favicon_url == "https://example.com/favicon.ico"


def test_save_bookmark_prefers_user_supplied_title(db_session, user, monkeypatch):
    monkeypatch.setattr(
        save_bookmark,
        "fetch_metadata",
        lambda url: PageMetadata(title="Extracted title"),
    )

    bookmark = save_bookmark_with_metadata(
        db_session, user_id=user.id, url="https://example.com", title="My own title"
    )

    assert bookmark.title == "My own title"


def test_save_bookmark_survives_metadata_extraction_failure(db_session, user, monkeypatch):
    def _boom(url):
        raise RuntimeError("network exploded")

    monkeypatch.setattr(save_bookmark, "fetch_metadata", _boom)

    bookmark = save_bookmark_with_metadata(db_session, user_id=user.id, url="https://example.com")

    assert bookmark.url == "https://example.com"
    assert bookmark.title is None
    assert bookmark.description is None


def test_save_bookmark_stores_ai_suggestion_without_applying_it_as_real_tags(
    db_session, user, monkeypatch
):
    monkeypatch.setattr(
        save_bookmark, "suggest_tags_safely", lambda *args, **kwargs: ["python", "homelab"]
    )

    bookmark = save_bookmark_with_metadata(db_session, user_id=user.id, url="https://example.com")

    assert bookmark.ai_suggested_tags == "python, homelab"
    assert bookmark.tags == []


def test_save_bookmark_skips_ai_suggestion_when_tags_already_given(db_session, user, monkeypatch):
    called = []
    monkeypatch.setattr(
        save_bookmark,
        "suggest_tags_safely",
        lambda *args, **kwargs: called.append(1) or ["should-not-be-used"],
    )

    bookmark = save_bookmark_with_metadata(
        db_session, user_id=user.id, url="https://example.com", tag_names=["manual"]
    )

    assert called == []
    assert bookmark.ai_suggested_tags is None
    assert [t.name for t in bookmark.tags] == ["manual"]


def test_save_bookmark_skips_ai_suggestion_when_feature_flag_disabled(
    db_session, user, monkeypatch
):
    called = []
    monkeypatch.setattr(save_bookmark.settings, "ai_tagging_enabled", False)
    monkeypatch.setattr(
        save_bookmark, "suggest_tags_safely", lambda *args, **kwargs: called.append(1) or []
    )

    bookmark = save_bookmark_with_metadata(db_session, user_id=user.id, url="https://example.com")

    assert called == []
    assert bookmark.ai_suggested_tags is None
