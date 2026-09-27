from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session as OrmSession

from app.api.deps import get_current_user
from app.api.schemas import LoginRequest, UserOut
from app.config import settings
from app.db import get_db
from app.domain.session import COOKIE_NAME, create_session, delete_session
from app.domain.user import User, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest, response: Response, db: OrmSession = Depends(get_db)) -> User:
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    session = create_session(db, user.id)
    max_age = int((session.expires_at - session.created_at).total_seconds())
    response.set_cookie(
        COOKIE_NAME,
        session.token,
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
        max_age=max_age,
    )
    return user


@router.post("/logout")
def logout(
    response: Response,
    session_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: OrmSession = Depends(get_db),
) -> dict[str, str]:
    if session_token is not None:
        delete_session(db, session_token)
    response.delete_cookie(COOKIE_NAME)
    return {"status": "ok"}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
