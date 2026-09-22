from __future__ import annotations

import logging

from sqlalchemy.orm import Session as OrmSession

from app.config import settings
from app.domain.bookmark import (
    Bookmark,
    create_bookmark,
    list_most_used_tag_names,
    list_tag_names,
)
from app.integrations.ai_provider import get_active_provider
from app.integrations.metadata_extractor import PageMetadata, fetch_metadata
from app.orchestration.enrich_tiktok import enrich_tiktok_metadata_safely
from app.orchestration.suggest_tags import suggest_tags_safely

logger = logging.getLogger(__name__)


def save_bookmark_fast(
    db: OrmSession,
    user_id: int,
    url: str,
    title: str | None = None,
    note: str | None = None,
    tag_names: list[str] | None = None,
) -> Bookmark:
    return create_bookmark(
        db,
        user_id=user_id,
        url=url,
        title=title,
        note=note,
        tag_names=tag_names,
    )


def enrich_bookmark(db: OrmSession, bookmark: Bookmark) -> Bookmark:
    metadata = _fetch_metadata_safely(bookmark.url)
    metadata, tiktok_note = enrich_tiktok_metadata_safely(bookmark.url, metadata)
    resolved_title = bookmark.title or metadata.title
    combined_note = (
        f"{bookmark.note}\n{tiktok_note}"
        if bookmark.note and tiktok_note
        else (tiktok_note or bookmark.note)
    )

    suggested_tags: list[str] = []
    if settings.ai_tagging_enabled and not bookmark.tags:
        provider = get_active_provider()
        existing_tags = (
            list_most_used_tag_names(db, bookmark.user_id, limit=20)
            or list_tag_names(db, bookmark.user_id)[:20]
        )
        suggested_tags = suggest_tags_safely(
            provider,
            bookmark.url,
            resolved_title,
            metadata.description,
            existing_tags=existing_tags,
        )

    bookmark.title = resolved_title
    bookmark.note = combined_note
    bookmark.description = metadata.description
    bookmark.image_url = metadata.image_url
    bookmark.favicon_url = metadata.favicon_url
    if suggested_tags:
        bookmark.ai_suggested_tags = ", ".join(suggested_tags)
    db.commit()
    db.refresh(bookmark)
    return bookmark


def enrich_bookmark_task(bookmark_id: int, user_id: int) -> None:
    from app.db import SessionLocal
    from app.domain.bookmark import get_bookmark

    db = SessionLocal()
    try:
        bookmark = get_bookmark(db, user_id, bookmark_id)
        if bookmark is not None:
            enrich_bookmark(db, bookmark)
    except Exception:
        logger.exception("unexpected error in background enrichment for bookmark %s", bookmark_id)
    finally:
        db.close()


def save_bookmark_with_metadata(
    db: OrmSession,
    user_id: int,
    url: str,
    title: str | None = None,
    note: str | None = None,
    tag_names: list[str] | None = None,
) -> Bookmark:
    bookmark = save_bookmark_fast(
        db,
        user_id=user_id,
        url=url,
        title=title,
        note=note,
        tag_names=tag_names,
    )
    return enrich_bookmark(db, bookmark)


def _fetch_metadata_safely(url: str) -> PageMetadata:
    try:
        return fetch_metadata(url)
    except Exception:
        logger.exception("unexpected error extracting metadata for %s", url)
        return PageMetadata()

