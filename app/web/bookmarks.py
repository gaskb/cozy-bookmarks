from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy.orm import Session as OrmSession

from app.db import get_db
from app.domain import bookmark as bookmark_domain
from app.domain.bookmark import BookmarkStatus
from app.domain.user import User
from app.web.deps import get_current_user_web
from app.web.templating import templates

router = APIRouter()


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
