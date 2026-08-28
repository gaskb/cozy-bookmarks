from __future__ import annotations

import datetime as dt
import secrets

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import Session as OrmSession

from app.db import Base
from app.time_utils import utcnow

COOKIE_NAME = "session"
SESSION_TTL = dt.timedelta(days=30)


class Session(Base):
    __tablename__ = "sessions"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)


def create_session(db: OrmSession, user_id: int) -> Session:
    session = Session(
        token=secrets.token_urlsafe(32),
        user_id=user_id,
        expires_at=utcnow() + SESSION_TTL,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_valid_session(db: OrmSession, token: str) -> Session | None:
    session = db.get(Session, token)
    if session is None:
        return None
    if session.expires_at < utcnow():
        db.delete(session)
        db.commit()
        return None
    return session


def delete_session(db: OrmSession, token: str) -> None:
    session = db.get(Session, token)
    if session is not None:
        db.delete(session)
        db.commit()
