from __future__ import annotations

import datetime as dt
import hashlib
import secrets

from typing import ClassVar

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import Session as OrmSession

from app.db import Base
from app.time_utils import utcnow

COOKIE_NAME = "session"
SESSION_TTL = dt.timedelta(days=30)


def hash_session_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


class Session(Base):
    __tablename__ = "sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)

    _raw_token: ClassVar[str | None] = None

    @property
    def token(self) -> str:
        return getattr(self, "_raw_token", None) or self.token_hash

    @property
    def raw_token(self) -> str:
        return getattr(self, "_raw_token", None) or self.token_hash


def create_session(db: OrmSession, user_id: int) -> Session:
    raw_token = secrets.token_urlsafe(32)
    session = Session(
        token_hash=hash_session_token(raw_token),
        user_id=user_id,
        expires_at=utcnow() + SESSION_TTL,
    )
    session._raw_token = raw_token
    db.add(session)
    db.commit()
    db.refresh(session)
    session._raw_token = raw_token
    return session


def get_valid_session(db: OrmSession, token: str) -> Session | None:
    if not token or not isinstance(token, str):
        return None
    t_hash = hash_session_token(token)
    session = db.get(Session, t_hash)
    if session is None:
        return None
    if session.expires_at < utcnow():
        db.delete(session)
        db.commit()
        return None
    return session


def delete_session(db: OrmSession, token: str) -> None:
    if not token or not isinstance(token, str):
        return
    t_hash = hash_session_token(token)
    session = db.get(Session, t_hash)
    if session is not None:
        db.delete(session)
        db.commit()
