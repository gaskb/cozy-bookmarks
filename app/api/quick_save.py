from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy.orm import Session as OrmSession

from app.api.deps import get_current_user
from app.api.schemas import QuickSaveOut
from app.db import get_db
from app.domain.user import User
from app.orchestration.resolve_share_input import resolve_shared_url
from app.orchestration.save_bookmark import save_bookmark_with_metadata

router = APIRouter(tags=["quick-save"])


@router.post("/save", response_model=QuickSaveOut, status_code=status.HTTP_201_CREATED)
def quick_save(
    url: str | None = Form(default=None),
    title: str | None = Form(default=None),
    text: str | None = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> QuickSaveOut:
    resolved_url = resolve_shared_url(url, text)
    if resolved_url is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No URL found in the shared content"
        )

    bookmark = save_bookmark_with_metadata(
        db,
        user_id=current_user.id,
        url=resolved_url,
        title=title or None,
        note=text or None,
    )
    return QuickSaveOut(status="saved", bookmark_id=bookmark.id)
