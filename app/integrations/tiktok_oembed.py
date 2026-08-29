from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

OEMBED_URL = "https://www.tiktok.com/oembed"
DEFAULT_TIMEOUT = 5.0


def fetch_tiktok_caption(
    url: str, timeout: float = DEFAULT_TIMEOUT, client: httpx.Client | None = None
) -> str | None:
    owns_client = client is None
    http_client = client or httpx.Client()
    try:
        response = http_client.get(OEMBED_URL, params={"url": url}, timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        logger.warning("TikTok oEmbed fetch failed for %s: %s", url, exc)
        return None
    except ValueError as exc:
        logger.warning("TikTok oEmbed returned invalid JSON for %s: %s", url, exc)
        return None
    finally:
        if owns_client:
            http_client.close()

    title = data.get("title")
    return title.strip() if isinstance(title, str) and title.strip() else None
