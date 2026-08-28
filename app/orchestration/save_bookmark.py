from __future__ import annotations

import logging

from sqlalchemy.orm import Session as OrmSession

from app.domain.bookmark import Bookmark, create_bookmark
from app.integrations.metadata_extractor import PageMetadata, fetch_metadata

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

    return create_bookmark(
        db,
        user_id=user_id,
        url=url,
        title=title or metadata.title,
        note=note,
        description=metadata.description,
        image_url=metadata.image_url,
        favicon_url=metadata.favicon_url,
        tag_names=tag_names,
    )


def _fetch_metadata_safely(url: str) -> PageMetadata:
    try:
        return fetch_metadata(url)
    except Exception:
        logger.exception("unexpected error extracting metadata for %s", url)
        return PageMetadata()
