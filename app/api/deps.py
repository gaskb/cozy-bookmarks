from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session as OrmSession

from app.db import get_db
from app.domain.session import COOKIE_NAME, get_valid_session
from app.domain.user import User

UNAUTHORIZED = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def get_current_user(
    session_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: OrmSession = Depends(get_db),
) -> User:
    if session_token is None:
        raise UNAUTHORIZED

    session = get_valid_session(db, session_token)
    if session is None:
        raise UNAUTHORIZED

    user = db.get(User, session.user_id)
    if user is None:
        raise UNAUTHORIZED

    return user
