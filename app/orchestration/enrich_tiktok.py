from __future__ import annotations

import logging
from urllib.parse import urlparse

from app.integrations.metadata_extractor import PageMetadata
from app.integrations.tiktok_oembed import fetch_tiktok_caption
from app.orchestration.resolve_share_input import URL_PATTERN

logger = logging.getLogger(__name__)

TIKTOK_HOSTS = {"tiktok.com", "www.tiktok.com", "vm.tiktok.com", "vt.tiktok.com", "m.tiktok.com"}


def is_tiktok_url(url: str) -> bool:
    try:
        host = urlparse(url).hostname or ""
    except ValueError:
        return False
    return host.lower() in TIKTOK_HOSTS


def enrich_tiktok_metadata_safely(
    url: str, metadata: PageMetadata
) -> tuple[PageMetadata, str | None]:
    if not is_tiktok_url(url):
        return metadata, None

    try:
        caption = fetch_tiktok_caption(url)
    except Exception:
        logger.exception("unexpected error enriching TikTok metadata for %s", url)
        return metadata, None

    if not caption:
        return metadata, None

    # The generic OpenGraph description scraped from a TikTok page is always
    # the same "Log in to TikTok" boilerplate (TikTok blocks anonymous
    # scraping) - the oEmbed caption is the real content whenever it's
    # available, so it always wins here regardless of length.
    updated_metadata = PageMetadata(
        title=metadata.title,
        description=caption,
        image_url=metadata.image_url,
        favicon_url=metadata.favicon_url,
    )

    cited_url_match = URL_PATTERN.search(caption)
    extra_note = f"Link citato nella caption: {cited_url_match.group(0)}" if cited_url_match else None

    return updated_metadata, extra_note
