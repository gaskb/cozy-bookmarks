from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as OrmSession

from app.db import get_db
from app.domain.user import User
from app.orchestration.resolve_share_input import resolve_shared_url
from app.orchestration.save_bookmark import save_bookmark_with_metadata
from app.web.deps import get_current_user_web

router = APIRouter()


@router.post("/share-target")
def share_target(
    url: str | None = Form(default=None),
    title: str | None = Form(default=None),
    text: str | None = Form(default=None),
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
) -> RedirectResponse:
    resolved_url = resolve_shared_url(url, text)
    if resolved_url is None:
        return RedirectResponse("/?share_error=no_url", status_code=303)

    save_bookmark_with_metadata(
        db,
        user_id=current_user.id,
        url=resolved_url,
        title=title or None,
        note=text or None,
    )
    return RedirectResponse("/?status=da_organizzare&shared=1", status_code=303)
