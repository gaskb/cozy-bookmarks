from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session as OrmSession

from app.db import get_db
from app.domain.api_token import get_user_by_api_token
from app.domain.session import COOKIE_NAME, get_valid_session
from app.domain.user import User

UNAUTHORIZED = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def resolve_current_user(
    db: OrmSession,
    session_token: str | None = None,
    bearer_token: str | None = None,
) -> User | None:
    if bearer_token:
        user = get_user_by_api_token(db, bearer_token)
        if user is not None:
            return user

    if session_token:
        session = get_valid_session(db, session_token)
        if session is not None:
            return db.get(User, session.user_id)

    return None


def get_current_user(
    session_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: OrmSession = Depends(get_db),
) -> User:
    bearer = None
    if authorization and authorization.lower().startswith("bearer "):
        bearer = authorization[7:].strip()

    user = resolve_current_user(db, session_token=session_token, bearer_token=bearer)
    if user is None:
        raise UNAUTHORIZED
    return user

