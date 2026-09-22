from __future__ import annotations

import html
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.bookmark import Bookmark


def export_netscape_html(bookmarks: list[Bookmark]) -> str:
    """Export bookmarks to the standard Netscape Bookmark HTML format."""
    lines = [
        "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
        "<!-- This is an automatically generated file.",
        "     It will be read and overwritten.",
        "     DO NOT EDIT! -->",
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
        "<TITLE>Bookmarks</TITLE>",
        "<H1>Bookmarks</H1>",
        "<DL><p>",
    ]

    for b in bookmarks:
        url_escaped = html.escape(b.url, quote=True)
        title_escaped = html.escape(b.title or b.url)
        add_date = int(b.created_at.timestamp()) if b.created_at else 0
        tag_names = sorted(t.name for t in b.tags) if b.tags else []
        tags_attr = f' TAGS="{html.escape(",".join(tag_names), quote=True)}"' if tag_names else ""

        lines.append(f'    <DT><A HREF="{url_escaped}" ADD_DATE="{add_date}"{tags_attr}>{title_escaped}</A>')

        desc = b.note or b.description
        if desc:
            lines.append(f"    <DD>{html.escape(desc)}")

    lines.append("</DL><p>")
    lines.append("")
    return "\n".join(lines)


def export_json_data(bookmarks: list[Bookmark]) -> list[dict]:
    """Export bookmarks to a complete structured JSON-compatible list."""
    items = []
    for b in bookmarks:
        ai_tags = [t.strip() for t in b.ai_suggested_tags.split(",") if t.strip()] if b.ai_suggested_tags else []
        items.append({
            "id": b.id,
            "url": b.url,
            "title": b.title,
            "note": b.note,
            "description": b.description,
            "status": b.status.value if hasattr(b.status, "value") else str(b.status),
            "image_url": b.image_url,
            "favicon_url": b.favicon_url,
            "tags": sorted(t.name for t in b.tags) if b.tags else [],
            "ai_suggested_tags": ai_tags,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        })
    return items
