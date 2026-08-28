import datetime as dt

from pydantic import BaseModel

from app.domain.bookmark import Bookmark, BookmarkStatus


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    email: str


class BookmarkCreate(BaseModel):
    url: str
    title: str | None = None
    note: str | None = None
    tags: list[str] = []


class BookmarkUpdate(BaseModel):
    title: str | None = None
    note: str | None = None
    status: BookmarkStatus | None = None
    tags: list[str] | None = None


class BookmarkOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    url: str
    title: str | None
    note: str | None
    description: str | None
    image_url: str | None
    favicon_url: str | None
    status: BookmarkStatus
    created_at: dt.datetime
    tags: list[str]

    @classmethod
    def from_bookmark(cls, bookmark: Bookmark) -> "BookmarkOut":
        return cls(
            id=bookmark.id,
            url=bookmark.url,
            title=bookmark.title,
            note=bookmark.note,
            description=bookmark.description,
            image_url=bookmark.image_url,
            favicon_url=bookmark.favicon_url,
            status=bookmark.status,
            created_at=bookmark.created_at,
            tags=sorted(tag.name for tag in bookmark.tags),
        )
