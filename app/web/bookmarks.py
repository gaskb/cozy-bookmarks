from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from sqlalchemy.orm import Session as OrmSession

from app.db import get_db
from app.domain import bookmark as bookmark_domain
from app.domain.bookmark import BookmarkStatus
from app.domain.user import User
from app.web.deps import get_current_user_web
from app.web.templating import templates

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
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
) -> HTMLResponse:
    bookmarks = bookmark_domain.list_bookmarks(db, current_user.id, status=status, tag=tag)
    all_tags = bookmark_domain.list_tag_names(db, current_user.id)
    return templates.TemplateResponse(
        request,
        "list.html",
        {
            "bookmarks": bookmarks,
            "status": status.value,
            "all_tags": all_tags,
            "selected_tag": tag,
        },
    )


@router.delete("/bookmarks/{bookmark_id}/delete")
def delete_bookmark_row(
    bookmark_id: int,
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
) -> PlainTextResponse:
    bookmark_domain.delete_bookmark(db, current_user.id, bookmark_id)
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
    return templates.TemplateResponse(
        request, "organize.html", {"bookmark": bookmark, "remaining_count": remaining_count}
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
    bookmark = bookmark_domain.update_bookmark(
        db,
        current_user.id,
        bookmark_id,
        title=_normalize(title),
        note=_normalize(note),
        status=BookmarkStatus.ORGANIZZATO,
        tag_names=_parse_tags(tags),
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


def _redirect_to_next_or_list(db: OrmSession, user_id: int, exclude_id: int) -> RedirectResponse:
    next_bookmark = bookmark_domain.get_next_to_organize(db, user_id, exclude_id=exclude_id)
    if next_bookmark is not None:
        return RedirectResponse(f"/bookmarks/{next_bookmark.id}/organize", status_code=303)
    return RedirectResponse("/?status=organizzato", status_code=303)
