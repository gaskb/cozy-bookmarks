from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = "cozy-bookmarks-bot/0.1 (+personal bookmark manager, single user)"
MAX_BYTES = 2_000_000
DEFAULT_TIMEOUT = 5.0


@dataclass
class PageMetadata:
    title: str | None = None
    description: str | None = None
    image_url: str | None = None
    favicon_url: str | None = None


def fetch_metadata(
    url: str, timeout: float = DEFAULT_TIMEOUT, client: httpx.Client | None = None
) -> PageMetadata:
    try:
        html = _download_html(url, timeout, client)
    except httpx.HTTPError as exc:
        logger.warning("metadata fetch failed for %s: %s", url, exc)
        return PageMetadata()

    if html is None:
        return PageMetadata()

    return _parse_html(html, base_url=url)


def _download_html(url: str, timeout: float, client: httpx.Client | None) -> str | None:
    if client is not None:
        return _stream_html(client, url, timeout)
    with httpx.Client() as owned_client:
        return _stream_html(owned_client, url, timeout)


def _stream_html(client: httpx.Client, url: str, timeout: float) -> str | None:
    with client.stream(
        "GET", url, timeout=timeout, follow_redirects=True, headers={"User-Agent": USER_AGENT}
    ) as response:
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type:
            return None

        chunks = []
        size = 0
        for chunk in response.iter_bytes():
            chunks.append(chunk)
            size += len(chunk)
            if size >= MAX_BYTES:
                break

        return b"".join(chunks).decode(response.encoding or "utf-8", errors="replace")


def _parse_html(html: str, base_url: str) -> PageMetadata:
    soup = BeautifulSoup(html, "html.parser")

    title = _meta_content(soup, "og:title") or _plain_title(soup)
    description = _meta_content(soup, "og:description") or _meta_content(
        soup, "description", attr="name"
    )

    image = _meta_content(soup, "og:image")
    image_url = urljoin(base_url, image) if image else None

    favicon = _find_favicon(soup)
    favicon_url = urljoin(base_url, favicon) if favicon else urljoin(base_url, "/favicon.ico")

    return PageMetadata(
        title=title, description=description, image_url=image_url, favicon_url=favicon_url
    )


def _meta_content(soup: BeautifulSoup, key: str, attr: str = "property") -> str | None:
    tag = soup.find("meta", attrs={attr: key})
    content = tag.get("content") if tag else None
    return content.strip() if content else None


def _plain_title(soup: BeautifulSoup) -> str | None:
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return None


def _find_favicon(soup: BeautifulSoup) -> str | None:
    for link in soup.find_all("link", href=True):
        rel = link.get("rel") or []
        rel_values = rel if isinstance(rel, list) else [rel]
        if any("icon" in value.lower() for value in rel_values):
            return link["href"].strip()
    return None
