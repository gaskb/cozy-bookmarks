from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as OrmSession

from app.api.deps import get_current_user
from app.api.schemas import BookmarkCreate, BookmarkOut, BookmarkUpdate
from app.db import get_db
from app.domain import bookmark as bookmark_domain
from app.domain.bookmark import BookmarkStatus
from app.domain.user import User
from app.orchestration.save_bookmark import save_bookmark_with_metadata

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


@router.post("", response_model=BookmarkOut, status_code=status.HTTP_201_CREATED)
def create_bookmark(
    payload: BookmarkCreate,
    current_user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> BookmarkOut:
    bookmark = save_bookmark_with_metadata(
        db,
        user_id=current_user.id,
        url=payload.url,
        title=payload.title,
        note=payload.note,
        tag_names=payload.tags,
    )
    return BookmarkOut.from_bookmark(bookmark)


@router.get("", response_model=list[BookmarkOut])
def list_bookmarks(
    status_filter: BookmarkStatus | None = None,
    current_user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> list[BookmarkOut]:
    bookmarks = bookmark_domain.list_bookmarks(db, user_id=current_user.id, status=status_filter)
    return [BookmarkOut.from_bookmark(b) for b in bookmarks]


@router.get("/{bookmark_id}", response_model=BookmarkOut)
def get_bookmark(
    bookmark_id: int,
    current_user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> BookmarkOut:
    bookmark = bookmark_domain.get_bookmark(db, user_id=current_user.id, bookmark_id=bookmark_id)
    if bookmark is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found")
    return BookmarkOut.from_bookmark(bookmark)


@router.patch("/{bookmark_id}", response_model=BookmarkOut)
def update_bookmark(
    bookmark_id: int,
    payload: BookmarkUpdate,
    current_user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> BookmarkOut:
    bookmark = bookmark_domain.update_bookmark(
        db,
        user_id=current_user.id,
        bookmark_id=bookmark_id,
        title=payload.title,
        note=payload.note,
        status=payload.status,
        tag_names=payload.tags,
    )
    if bookmark is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found")
    return BookmarkOut.from_bookmark(bookmark)


@router.delete("/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bookmark(
    bookmark_id: int,
    current_user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> None:
    deleted = bookmark_domain.delete_bookmark(db, user_id=current_user.id, bookmark_id=bookmark_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found")
