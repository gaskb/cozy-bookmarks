import datetime as dt

from pydantic import BaseModel, Field, field_validator

from app.domain.bookmark import Bookmark, BookmarkStatus, EnrichmentStatus
from app.validation import (
    MAX_NOTE_LENGTH,
    MAX_TITLE_LENGTH,
    MAX_TOKEN_NAME_LENGTH,
    MAX_URL_LENGTH,
    validate_tag_name,
    validate_token_name,
    validate_url,
)


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    email: str


class BookmarkCreate(BaseModel):
    url: str = Field(..., max_length=MAX_URL_LENGTH)
    title: str | None = Field(default=None, max_length=MAX_TITLE_LENGTH)
    note: str | None = Field(default=None, max_length=MAX_NOTE_LENGTH)
    tags: list[str] = Field(default_factory=list)

    @field_validator("url")
    @classmethod
    def validate_bookmark_url(cls, v: str) -> str:
        return validate_url(v)

    @field_validator("tags")
    @classmethod
    def validate_bookmark_tags(cls, v: list[str]) -> list[str]:
        return [validate_tag_name(t) for t in v if t.strip()]


class QuickSaveOut(BaseModel):
    status: str
    bookmark_id: int


class BookmarkUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=MAX_TITLE_LENGTH)
    note: str | None = Field(default=None, max_length=MAX_NOTE_LENGTH)
    status: BookmarkStatus | None = None
    tags: list[str] | None = None

    @field_validator("tags")
    @classmethod
    def validate_bookmark_tags(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            return [validate_tag_name(t) for t in v if t.strip()]
        return None


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
    enrichment_status: EnrichmentStatus = EnrichmentStatus.COMPLETED
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
            enrichment_status=getattr(bookmark, "enrichment_status", EnrichmentStatus.COMPLETED),
            created_at=bookmark.created_at,
            tags=sorted(tag.name for tag in bookmark.tags),
        )


class TokenCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=MAX_TOKEN_NAME_LENGTH)

    @field_validator("name")
    @classmethod
    def validate_token_name_field(cls, v: str) -> str:
        return validate_token_name(v)


class TokenCreatedOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    token: str
    token_prefix: str
    created_at: dt.datetime


class TokenOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    token_prefix: str
    created_at: dt.datetime
    last_used_at: dt.datetime | None = None
    revoked_at: dt.datetime | None = None

