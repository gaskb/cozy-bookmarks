import pytest

from app.domain.bookmark import (
    Bookmark,
    EnrichmentStatus,
    create_bookmark,
    get_bookmark,
    list_pending_or_failed_enrichments,
)
from app.orchestration import save_bookmark
from app.orchestration.save_bookmark import (
    enrich_bookmark,
    enrich_bookmark_task,
    save_bookmark_fast,
    save_bookmark_with_metadata,
)
from app.scripts.retry_failed_enrichments import retry_enrichments


def test_save_bookmark_fast_initializes_with_pending_status(db_session, user):
    bm = save_bookmark_fast(db_session, user.id, "https://example.com/fast")
    assert bm.enrichment_status == EnrichmentStatus.PENDING

    reloaded = get_bookmark(db_session, user.id, bm.id)
    assert reloaded.enrichment_status == EnrichmentStatus.PENDING


def test_save_bookmark_with_metadata_sets_completed_status(db_session, user):
    bm = save_bookmark_with_metadata(db_session, user.id, "https://example.com/sync")
    assert bm.enrichment_status == EnrichmentStatus.COMPLETED


def test_enrich_bookmark_updates_status_to_completed(db_session, user):
    bm = save_bookmark_fast(db_session, user.id, "https://example.com/enrich-me")
    assert bm.enrichment_status == EnrichmentStatus.PENDING

    enriched = enrich_bookmark(db_session, bm)
    assert enriched.enrichment_status == EnrichmentStatus.COMPLETED


def test_enrich_bookmark_task_sets_failed_on_exception(db_session, user, monkeypatch):
    from sqlalchemy.orm import sessionmaker

    bm = save_bookmark_fast(db_session, user.id, "https://example.com/will-fail")

    # Override SessionLocal to spawn sessions on the same test database
    monkeypatch.setattr("app.db.SessionLocal", sessionmaker(bind=db_session.get_bind()))

    def _broken_enrich(db, bookmark):
        raise RuntimeError("AI or Network error occurred during enrichment")

    monkeypatch.setattr(save_bookmark, "enrich_bookmark", _broken_enrich)

    enrich_bookmark_task(bm.id, user.id)

    db_session.expire_all()
    reloaded = db_session.get(Bookmark, bm.id)
    assert reloaded is not None
    assert reloaded.enrichment_status == EnrichmentStatus.FAILED


def test_retry_enrichments_cli_script_is_idempotent(db_session, user, monkeypatch):
    from sqlalchemy.orm import sessionmaker
    import app.scripts.retry_failed_enrichments as retry_mod

    # Setup 1 pending, 1 failed, and 1 already completed bookmark
    bm_pending = create_bookmark(
        db_session, user.id, "https://example.com/pending", enrichment_status=EnrichmentStatus.PENDING
    )
    bm_failed = create_bookmark(
        db_session, user.id, "https://example.com/failed", enrichment_status=EnrichmentStatus.FAILED
    )
    bm_completed = create_bookmark(
        db_session, user.id, "https://example.com/completed", enrichment_status=EnrichmentStatus.COMPLETED
    )

    monkeypatch.setattr(retry_mod, "SessionLocal", sessionmaker(bind=db_session.get_bind()))

    # First retry execution should pick up both pending and failed
    success, failed = retry_enrichments(limit=10)
    assert success == 2
    assert failed == 0

    reloaded_pending = db_session.get(Bookmark, bm_pending.id)
    reloaded_failed = db_session.get(Bookmark, bm_failed.id)
    reloaded_completed = db_session.get(Bookmark, bm_completed.id)

    assert reloaded_pending.enrichment_status == EnrichmentStatus.COMPLETED
    assert reloaded_failed.enrichment_status == EnrichmentStatus.COMPLETED
    assert reloaded_completed.enrichment_status == EnrichmentStatus.COMPLETED

    # Second execution should be a no-op (idempotent)
    success2, failed2 = retry_enrichments(limit=10)
    assert success2 == 0
    assert failed2 == 0
