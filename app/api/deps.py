from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session as OrmSession

from app.db import get_db
from app.domain.session import COOKIE_NAME, get_valid_session
from app.domain.user import User

UNAUTHORIZED = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def resolve_current_user(db: OrmSession, session_token: str | None) -> User | None:
    if session_token is None:
        return None

    session = get_valid_session(db, session_token)
    if session is None:
        return None

    return db.get(User, session.user_id)


def get_current_user(
    session_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: OrmSession = Depends(get_db),
) -> User:
    user = resolve_current_user(db, session_token)
    if user is None:
        raise UNAUTHORIZED
    return user
