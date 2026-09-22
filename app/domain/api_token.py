from __future__ import annotations

import datetime as dt
import hashlib
import secrets

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import Session as OrmSession

from app.db import Base
from app.domain.user import User
from app.time_utils import utcnow

TOKEN_PREFIX_STR = "cbk_"


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


class ApiToken(Base):
    __tablename__ = "api_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    token_prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
    last_used_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship()


def create_api_token(db: OrmSession, user_id: int, name: str) -> tuple[ApiToken, str]:
    raw_secret = secrets.token_urlsafe(32)
    raw_token = f"{TOKEN_PREFIX_STR}{raw_secret}"
    prefix = f"{raw_token[:8]}..."
    t_hash = hash_token(raw_token)

    api_token = ApiToken(
        user_id=user_id,
        name=name.strip(),
        token_hash=t_hash,
        token_prefix=prefix,
    )
    db.add(api_token)
    db.commit()
    db.refresh(api_token)
    return api_token, raw_token


def get_user_by_api_token(db: OrmSession, raw_token: str) -> User | None:
    if not raw_token or not isinstance(raw_token, str):
        return None

    t_hash = hash_token(raw_token)
    token = (
        db.query(ApiToken)
        .filter(ApiToken.token_hash == t_hash, ApiToken.revoked_at.is_(None))
        .first()
    )
    if token is None:
        return None

    token.last_used_at = utcnow()
    db.commit()
    return token.user


def list_api_tokens(db: OrmSession, user_id: int) -> list[ApiToken]:
    return (
        db.query(ApiToken)
        .filter(ApiToken.user_id == user_id)
        .order_by(ApiToken.created_at.desc())
        .all()
    )


def revoke_api_token(db: OrmSession, user_id: int, token_id: int) -> bool:
    token = (
        db.query(ApiToken)
        .filter(ApiToken.id == token_id, ApiToken.user_id == user_id)
        .first()
    )
    if token is None or token.revoked_at is not None:
        return False

    token.revoked_at = utcnow()
    db.commit()
    return True
