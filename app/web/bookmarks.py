import json

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response
from sqlalchemy.orm import Session as OrmSession

from app.db import get_db
from app.domain import bookmark as bookmark_domain
from app.domain.bookmark import BookmarkStatus
from app.domain.user import User
from app.integrations.bookmark_export import export_json_data, export_netscape_html
from app.integrations.bookmark_html_import import parse_netscape_bookmarks
from app.orchestration.daily_digest import send_test_daily_digest
from app.orchestration.save_bookmark import (
    enrich_bookmark_task,
    save_bookmark_fast,
    save_bookmark_with_metadata,
)
from app.validation import (
    ValidationError,
    validate_note,
    validate_tag_name,
    validate_title,
    validate_url,
)
from app.web.deps import get_current_user_web
from app.web.templating import templates

MAX_IMPORT_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_IMPORT_BOOKMARKS = 5000
CHUNK_SIZE = 64 * 1024

router = APIRouter()


def _normalize(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _parse_tags(raw: str) -> list[str]:
    return [t.strip() for t in raw.split(",") if t.strip()]


@router.get("/", response_class=HTMLResponse)
def bookmark_list(
    request: Request,
    status: BookmarkStatus = BookmarkStatus.DA_ORGANIZZARE,
    tag: str | None = None,
    q: str | None = None,
    shared: bool = False,
    share_error: str | None = None,
    imported: int | None = None,
    skipped: int | None = None,
    test_digest_sent: int | None = None,
    test_digest_error: str | None = None,
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
) -> HTMLResponse:
    bookmarks = bookmark_domain.list_bookmarks(db, current_user.id, status=status, tag=tag, query_text=q)
    pinned_tags = bookmark_domain.list_tag_names(db, current_user.id, pinned=True)
    all_tags = bookmark_domain.list_tag_names(db, current_user.id, pinned=False)
    return templates.TemplateResponse(
        request,
        "list.html",
        {
            "bookmarks": bookmarks,
            "status": status.value,
            "pinned_tags": pinned_tags,
            "all_tags": all_tags,
            "selected_tag": tag,
            "query": q,
            "shared": shared,
            "share_error": share_error,
            "imported": imported,
            "skipped": skipped,
            "test_digest_sent": test_digest_sent,
            "test_digest_error": test_digest_error,
            "current_user": current_user,
        },
    )


@router.post("/tags/pin")
def pin_tag_route(
    name: str = Form(...),
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
) -> RedirectResponse:
    try:
        cleaned = validate_tag_name(name)
        bookmark_domain.pin_tag(db, current_user.id, cleaned)
    except ValidationError:
        pass
    return RedirectResponse("/", status_code=303)


@router.post("/tags/unpin")
def unpin_tag_route(
    name: str = Form(...),
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
) -> RedirectResponse:
    bookmark_domain.unpin_tag(db, current_user.id, name)
    return RedirectResponse("/", status_code=303)


@router.get("/bookmarks/new", response_class=HTMLResponse)
def new_bookmark_form(
    request: Request,
    current_user: User = Depends(get_current_user_web),
) -> HTMLResponse:
    return templates.TemplateResponse(request, "new_bookmark.html", {"current_user": current_user})


@router.post("/bookmarks/new")
def new_bookmark_submit(
    request: Request,
    background_tasks: BackgroundTasks,
    url: str = Form(""),
    title: str = Form(""),
    note: str = Form(""),
    tags: str = Form(""),
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
):
    try:
        validated_url = validate_url(url)
        validated_title = validate_title(title)
        validated_note = validate_note(note)
        raw_tags = _parse_tags(tags)
        validated_tags = [validate_tag_name(t) for t in raw_tags]
    except ValidationError as exc:
        return templates.TemplateResponse(
            request,
            "new_bookmark.html",
            {"error": str(exc), "current_user": current_user},
            status_code=400,
        )

    bookmark = save_bookmark_fast(
        db,
        user_id=current_user.id,
        url=validated_url,
        title=validated_title,
        note=validated_note,
        tag_names=validated_tags or None,
    )
    background_tasks.add_task(enrich_bookmark_task, bookmark.id, current_user.id)
    return RedirectResponse(f"/bookmarks/{bookmark.id}/organize", status_code=303)



@router.get("/bookmarks/import", response_class=HTMLResponse)
def import_bookmarks_form(
    request: Request,
    current_user: User = Depends(get_current_user_web),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "import_bookmarks.html", {"current_user": current_user}
    )


@router.post("/bookmarks/import")
async def import_bookmarks_submit(
    request: Request,
    file: UploadFile,
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
) -> Response:
    chunks = []
    total_size = 0
    while chunk := await file.read(CHUNK_SIZE):
        total_size += len(chunk)
        if total_size > MAX_IMPORT_FILE_SIZE:
            return templates.TemplateResponse(
                request,
                "import_bookmarks.html",
                {
                    "error": "Il file caricato supera la dimensione massima consentita di 5 MB",
                    "current_user": current_user,
                },
                status_code=400,
            )
        chunks.append(chunk)

    raw = b"".join(chunks)
    content = raw.decode("utf-8", errors="replace")
    links = parse_netscape_bookmarks(content)

    if len(links) > MAX_IMPORT_BOOKMARKS:
        return templates.TemplateResponse(
            request,
            "import_bookmarks.html",
            {
                "error": f"Il file contiene troppi segnalibri (massimo {MAX_IMPORT_BOOKMARKS} per import)",
                "current_user": current_user,
            },
            status_code=400,
        )

    links_tuples = [(link.url, link.title) for link in links]
    imported_count, skipped_count = bookmark_domain.import_bookmarks_batch(
        db, current_user.id, links_tuples
    )

    return RedirectResponse(f"/?imported={imported_count}&skipped={skipped_count}", status_code=303)


@router.delete("/bookmarks/{bookmark_id}/delete")
def delete_bookmark_row(
    bookmark_id: int,
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
) -> PlainTextResponse:
    bookmark_domain.delete_bookmark(db, current_user.id, bookmark_id)
    return PlainTextResponse("")


@router.post("/bookmarks/{bookmark_id}/archive")
def archive_bookmark_route(
    bookmark_id: int,
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
) -> PlainTextResponse:
    bookmark_domain.archive_bookmark(db, current_user.id, bookmark_id)
    return PlainTextResponse("")


@router.post("/bookmarks/{bookmark_id}/unarchive")
def unarchive_bookmark_route(
    bookmark_id: int,
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
) -> PlainTextResponse:
    bookmark_domain.unarchive_bookmark(db, current_user.id, bookmark_id)
    return PlainTextResponse("")



@router.post("/bookmarks/{bookmark_id}/reorder")
def reorder_bookmark_route(
    bookmark_id: int,
    above_id: str = Form(""),
    below_id: str = Form(""),
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
) -> PlainTextResponse:
    bookmark_domain.reorder_bookmark(
        db,
        current_user.id,
        bookmark_id,
        above_id=int(above_id) if above_id else None,
        below_id=int(below_id) if below_id else None,
    )
    return PlainTextResponse("")


@router.post("/bookmarks/{bookmark_id}/tags/add")
def add_tag_route(
    bookmark_id: int,
    name: str = Form(...),
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
) -> PlainTextResponse:
    bookmark_domain.add_tag_to_bookmark(db, current_user.id, bookmark_id, name)
    return PlainTextResponse("")


@router.get("/bookmarks/{bookmark_id}/organize", response_class=HTMLResponse)
def organize_form(
    request: Request,
    bookmark_id: int,
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
):
    bookmark = bookmark_domain.get_bookmark(db, current_user.id, bookmark_id)
    if bookmark is None:
        return RedirectResponse("/", status_code=303)

    remaining_count = bookmark_domain.count_to_organize(db, current_user.id)
    is_suggestion = not bookmark.tags and bool(bookmark.ai_suggested_tags)
    tags_value = ", ".join(tag.name for tag in bookmark.tags) or (bookmark.ai_suggested_tags or "")
    most_used_tags = bookmark_domain.list_most_used_tag_names(db, current_user.id)
    recent_tags = bookmark_domain.list_recent_tag_names(db, current_user.id)
    all_tags = bookmark_domain.list_tag_names(db, current_user.id)
    return templates.TemplateResponse(
        request,
        "organize.html",
        {
            "bookmark": bookmark,
            "remaining_count": remaining_count,
            "tags_value": tags_value,
            "is_suggestion": is_suggestion,
            "current_user": current_user,
            "most_used_tags": most_used_tags,
            "recent_tags": recent_tags,
            "all_tags_json": json.dumps(all_tags).replace("<", "\\u003c"),
        },
    )


@router.post("/bookmarks/{bookmark_id}/organize")
def organize_submit(
    bookmark_id: int,
    title: str = Form(""),
    note: str = Form(""),
    tags: str = Form(""),
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
):
    try:
        clean_title = validate_title(title)
        clean_note = validate_note(note)
        clean_tags = [validate_tag_name(t) for t in _parse_tags(tags)]
    except ValidationError:
        clean_title = _normalize(title)[:500] if title else None
        clean_note = _normalize(note)[:10000] if note else None
        clean_tags = [t.strip().lower()[:50] for t in _parse_tags(tags) if t.strip()]

    bookmark = bookmark_domain.update_bookmark(
        db,
        current_user.id,
        bookmark_id,
        title=clean_title,
        note=clean_note,
        status=BookmarkStatus.ORGANIZZATO,
        tag_names=clean_tags,
    )
    if bookmark is None:
        return RedirectResponse("/", status_code=303)

    return _redirect_to_next_or_list(db, current_user.id, exclude_id=bookmark_id)


@router.post("/bookmarks/{bookmark_id}/organize/delete")
def organize_delete(
    bookmark_id: int,
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
):
    bookmark_domain.delete_bookmark(db, current_user.id, bookmark_id)
    return _redirect_to_next_or_list(db, current_user.id, exclude_id=bookmark_id)


@router.post("/bookmarks/{bookmark_id}/organize/archive")
def organize_archive(
    bookmark_id: int,
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
):
    bookmark_domain.archive_bookmark(db, current_user.id, bookmark_id)
    return _redirect_to_next_or_list(db, current_user.id, exclude_id=bookmark_id)



@router.get("/bookmarks/export/html")
def export_html(
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
) -> Response:
    bookmarks = bookmark_domain.list_bookmarks(db, current_user.id)
    content = export_netscape_html(bookmarks)
    return Response(
        content=content,
        media_type="text/html",
        headers={"Content-Disposition": 'attachment; filename="cozy-bookmarks.html"'},
    )


@router.get("/bookmarks/export/json")
def export_json(
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
) -> Response:
    bookmarks = bookmark_domain.list_bookmarks(db, current_user.id)
    data = export_json_data(bookmarks)
    content = json.dumps(data, indent=2, ensure_ascii=False)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="cozy-bookmarks.json"'},
    )


@router.post("/digest/send-test")
def send_test_digest(
    request: Request,
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
) -> RedirectResponse:
    count, error = send_test_daily_digest(db, current_user)
    referer = request.headers.get("referer") or "/"
    url_parts = referer.split("?", 1)
    base_path = url_parts[0]
    query_params = []
    if len(url_parts) > 1:
        for p in url_parts[1].split("&"):
            if p and not p.startswith("test_digest_"):
                query_params.append(p)

    if error:
        query_params.append(f"test_digest_error={error}")
    else:
        query_params.append(f"test_digest_sent={count}")

    redirect_url = base_path + ("?" + "&".join(query_params) if query_params else "")
    return RedirectResponse(redirect_url, status_code=303)


def _redirect_to_next_or_list(db: OrmSession, user_id: int, exclude_id: int) -> RedirectResponse:
    next_bookmark = bookmark_domain.get_next_to_organize(db, user_id, exclude_id=exclude_id)
    if next_bookmark is not None:
        return RedirectResponse(f"/bookmarks/{next_bookmark.id}/organize", status_code=303)
    return RedirectResponse("/?status=organizzato", status_code=303)
