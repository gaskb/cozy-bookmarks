from __future__ import annotations

from dataclasses import dataclass

from bs4 import BeautifulSoup


@dataclass
class ImportedLink:
    url: str
    title: str | None


def parse_netscape_bookmarks(html: str) -> list[ImportedLink]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href.lower().startswith(("http://", "https://")):
            continue
        title = anchor.get_text(strip=True) or None
        links.append(ImportedLink(url=href, title=title))
    return links
