from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session as OrmSession

from app.config import settings
from app.db import get_db
from app.domain.session import COOKIE_NAME, create_session, delete_session
from app.domain.user import User, verify_password
from app.web.deps import get_current_user_web
from app.web.templating import templates

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "login.html", {"current_user": None})


@router.post("/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: OrmSession = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Email o password non corretti", "current_user": None},
            status_code=401,
        )

    session = create_session(db, user.id)
    max_age = int((session.expires_at - session.created_at).total_seconds())
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        COOKIE_NAME,
        session.token,
        httponly=True,
        samesite="lax",
        secure=settings.env != "development",
        max_age=max_age,
    )
    return response


@router.post("/logout")
def logout_submit(
    request: Request,
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
):
    session_token = request.cookies.get(COOKIE_NAME)
    if session_token is not None:
        delete_session(db, session_token)
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(COOKIE_NAME)
    return response
