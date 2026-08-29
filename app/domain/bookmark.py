from __future__ import annotations

import datetime as dt
import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String, Table, Text, or_
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import Session as OrmSession

from app.db import Base
from app.time_utils import utcnow


class BookmarkStatus(str, enum.Enum):
    DA_ORGANIZZARE = "da_organizzare"
    ORGANIZZATO = "organizzato"


bookmark_tags = Table(
    "bookmark_tags",
    Base.metadata,
    Column("bookmark_id", ForeignKey("bookmarks.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str | None] = mapped_column(String(500))
    note: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(2048))
    favicon_url: Mapped[str | None] = mapped_column(String(2048))
    ai_suggested_tags: Mapped[str | None] = mapped_column(String(300))
    status: Mapped[BookmarkStatus] = mapped_column(
        Enum(BookmarkStatus, values_callable=lambda enum_cls: [member.value for member in enum_cls]),
        nullable=False,
        default=BookmarkStatus.DA_ORGANIZZARE,
    )
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)

    tags: Mapped[list[Tag]] = relationship(secondary=bookmark_tags, order_by="Tag.name")


def _get_or_create_tags(db: OrmSession, user_id: int, tag_names: list[str]) -> list[Tag]:
    tags = []
    for name in {name.strip().lower() for name in tag_names if name.strip()}:
        tag = db.query(Tag).filter(Tag.user_id == user_id, Tag.name == name).first()
        if tag is None:
            tag = Tag(user_id=user_id, name=name)
            db.add(tag)
        tags.append(tag)
    return tags


def create_bookmark(
    db: OrmSession,
    user_id: int,
    url: str,
    title: str | None = None,
    note: str | None = None,
    description: str | None = None,
    image_url: str | None = None,
    favicon_url: str | None = None,
    tag_names: list[str] | None = None,
    ai_suggested_tags: list[str] | None = None,
) -> Bookmark:
    bookmark = Bookmark(
        user_id=user_id,
        url=url,
        title=title,
        note=note,
        description=description,
        image_url=image_url,
        favicon_url=favicon_url,
        ai_suggested_tags=", ".join(ai_suggested_tags) if ai_suggested_tags else None,
        tags=_get_or_create_tags(db, user_id, tag_names or []),
    )
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return bookmark


def get_bookmark(db: OrmSession, user_id: int, bookmark_id: int) -> Bookmark | None:
    return (
        db.query(Bookmark)
        .filter(Bookmark.id == bookmark_id, Bookmark.user_id == user_id)
        .first()
    )


def find_bookmark_by_url(db: OrmSession, user_id: int, url: str) -> Bookmark | None:
    return db.query(Bookmark).filter(Bookmark.user_id == user_id, Bookmark.url == url).first()


def list_bookmarks(
    db: OrmSession,
    user_id: int,
    status: BookmarkStatus | None = None,
    tag: str | None = None,
    query_text: str | None = None,
) -> list[Bookmark]:
    query = db.query(Bookmark).filter(Bookmark.user_id == user_id)
    if status is not None:
        query = query.filter(Bookmark.status == status)
    if tag is not None:
        query = query.join(Bookmark.tags).filter(Tag.name == tag.strip().lower())
    if query_text and query_text.strip():
        pattern = f"%{query_text.strip()}%"
        query = query.filter(
            or_(
                Bookmark.title.ilike(pattern),
                Bookmark.note.ilike(pattern),
                Bookmark.url.ilike(pattern),
                Bookmark.tags.any(Tag.name.ilike(pattern)),
            )
        )
    return query.order_by(Bookmark.created_at.desc()).all()


def list_tag_names(db: OrmSession, user_id: int, pinned: bool | None = None) -> list[str]:
    query = db.query(Tag).filter(Tag.user_id == user_id)
    if pinned is not None:
        query = query.filter(Tag.pinned == pinned)
    return [tag.name for tag in query.order_by(Tag.name).all()]


def pin_tag(db: OrmSession, user_id: int, name: str) -> Tag:
    tag = _get_or_create_tags(db, user_id, [name])[0]
    tag.pinned = True
    db.commit()
    db.refresh(tag)
    return tag


def unpin_tag(db: OrmSession, user_id: int, name: str) -> None:
    tag = db.query(Tag).filter(Tag.user_id == user_id, Tag.name == name.strip().lower()).first()
    if tag is not None:
        tag.pinned = False
        db.commit()


def count_to_organize(db: OrmSession, user_id: int) -> int:
    return (
        db.query(Bookmark)
        .filter(Bookmark.user_id == user_id, Bookmark.status == BookmarkStatus.DA_ORGANIZZARE)
        .count()
    )


def get_next_to_organize(
    db: OrmSession, user_id: int, exclude_id: int | None = None
) -> Bookmark | None:
    query = db.query(Bookmark).filter(
        Bookmark.user_id == user_id, Bookmark.status == BookmarkStatus.DA_ORGANIZZARE
    )
    if exclude_id is not None:
        query = query.filter(Bookmark.id != exclude_id)
    return query.order_by(Bookmark.created_at.asc()).first()


def update_bookmark(
    db: OrmSession,
    user_id: int,
    bookmark_id: int,
    title: str | None = None,
    note: str | None = None,
    status: BookmarkStatus | None = None,
    tag_names: list[str] | None = None,
) -> Bookmark | None:
    bookmark = get_bookmark(db, user_id, bookmark_id)
    if bookmark is None:
        return None

    if title is not None:
        bookmark.title = title
    if note is not None:
        bookmark.note = note
    if status is not None:
        bookmark.status = status
    if tag_names is not None:
        bookmark.tags = _get_or_create_tags(db, user_id, tag_names)

    db.commit()
    db.refresh(bookmark)
    return bookmark


def delete_bookmark(db: OrmSession, user_id: int, bookmark_id: int) -> bool:
    bookmark = get_bookmark(db, user_id, bookmark_id)
    if bookmark is None:
        return False
    db.delete(bookmark)
    db.commit()
    return True
