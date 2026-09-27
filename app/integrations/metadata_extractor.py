from __future__ import annotations

import ipaddress
import logging
import socket
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = "cozy-bookmarks-bot/0.1 (+personal bookmark manager, single user)"
MAX_BYTES = 2_000_000
DEFAULT_TIMEOUT = 5.0
MAX_REDIRECTS = 3


def is_restricted_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        return True
    mapped = getattr(ip, "ipv4_mapped", None)
    if mapped is not None and is_restricted_ip(mapped):
        return True
    return False


def is_safe_url(url: str, resolver=None) -> bool:
    try:
        parsed = urlsplit(url)
    except Exception:
        return False

    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        return False

    hostname = parsed.hostname
    if not hostname:
        return False

    try:
        ip = ipaddress.ip_address(hostname)
        return not is_restricted_ip(ip)
    except ValueError:
        pass

    port = parsed.port or (443 if scheme == "https" else 80)
    dns_func = resolver or socket.getaddrinfo

    try:
        addr_info = dns_func(hostname, port, type=socket.SOCK_STREAM)
    except Exception as exc:
        logger.warning("DNS resolution failed for %s: %s", hostname, exc)
        return False

    if not addr_info:
        return False

    for item in addr_info:
        ip_str = item[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
            if is_restricted_ip(ip):
                logger.warning("Restricted IP (%s) resolved for host %s", ip_str, hostname)
                return False
        except ValueError:
            return False

    return True


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
    current_url = url
    for _ in range(MAX_REDIRECTS + 1):
        if not is_safe_url(current_url):
            logger.warning("SSRF check blocked access to URL: %s", current_url)
            return None

        with client.stream(
            "GET",
            current_url,
            timeout=timeout,
            follow_redirects=False,
            headers={"User-Agent": USER_AGENT},
        ) as response:
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("location")
                if not location:
                    logger.warning("Redirect without Location header: %s", current_url)
                    return None
                current_url = urljoin(current_url, location)
                continue

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

    logger.warning("Too many redirects fetching %s", url)
    return None


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
