from __future__ import annotations

import logging

from sqlalchemy.orm import Session as OrmSession

from app.config import settings
from app.domain.bookmark import Bookmark, create_bookmark
from app.integrations.ai_provider import get_active_provider
from app.integrations.metadata_extractor import PageMetadata, fetch_metadata
from app.orchestration.enrich_tiktok import enrich_tiktok_metadata_safely
from app.orchestration.suggest_tags import suggest_tags_safely

logger = logging.getLogger(__name__)


def save_bookmark_with_metadata(
    db: OrmSession,
    user_id: int,
    url: str,
    title: str | None = None,
    note: str | None = None,
    tag_names: list[str] | None = None,
) -> Bookmark:
    metadata = _fetch_metadata_safely(url)
    metadata, tiktok_note = enrich_tiktok_metadata_safely(url, metadata)
    resolved_title = title or metadata.title
    combined_note = f"{note}\n{tiktok_note}" if note and tiktok_note else (tiktok_note or note)

    suggested_tags: list[str] = []
    if settings.ai_tagging_enabled and not tag_names:
        provider = get_active_provider()
        suggested_tags = suggest_tags_safely(provider, url, resolved_title, metadata.description)

    return create_bookmark(
        db,
        user_id=user_id,
        url=url,
        title=resolved_title,
        note=combined_note,
        description=metadata.description,
        image_url=metadata.image_url,
        favicon_url=metadata.favicon_url,
        tag_names=tag_names,
        ai_suggested_tags=suggested_tags,
    )


def _fetch_metadata_safely(url: str) -> PageMetadata:
    try:
        return fetch_metadata(url)
    except Exception:
        logger.exception("unexpected error extracting metadata for %s", url)
        return PageMetadata()
