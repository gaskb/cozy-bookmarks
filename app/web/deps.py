from fastapi import Cookie, Depends
from sqlalchemy.orm import Session as OrmSession

from app.api.deps import resolve_current_user
from app.db import get_db
from app.domain.session import COOKIE_NAME
from app.domain.user import User


class NotAuthenticatedRedirect(Exception):
    pass


def get_current_user_web(
    session_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: OrmSession = Depends(get_db),
) -> User:
    user = resolve_current_user(db, session_token)
    if user is None:
        raise NotAuthenticatedRedirect()
    return user
