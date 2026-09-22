from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session as OrmSession

from app.db import get_db
from app.domain import api_token as token_domain
from app.domain.user import User
from app.web.deps import get_current_user_web
from app.web.templating import templates

router = APIRouter()


@router.get("/tokens", response_class=HTMLResponse)
def tokens_page(
    request: Request,
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
) -> HTMLResponse:
    tokens = token_domain.list_api_tokens(db, current_user.id)
    return templates.TemplateResponse(
        request,
        "tokens.html",
        {
            "tokens": tokens,
            "current_user": current_user,
            "new_token": None,
        },
    )


@router.post("/tokens", response_class=HTMLResponse)
def create_token_submit(
    request: Request,
    name: str = Form(""),
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
) -> HTMLResponse:
    cleaned_name = name.strip()
    new_raw_token = None
    error = None

    if not cleaned_name:
        error = "Il nome del token non può essere vuoto."
    else:
        _, new_raw_token = token_domain.create_api_token(db, current_user.id, cleaned_name)

    tokens = token_domain.list_api_tokens(db, current_user.id)
    return templates.TemplateResponse(
        request,
        "tokens.html",
        {
            "tokens": tokens,
            "current_user": current_user,
            "new_token": new_raw_token,
            "error": error,
        },
    )


@router.post("/tokens/{token_id}/revoke")
def revoke_token_submit(
    token_id: int,
    current_user: User = Depends(get_current_user_web),
    db: OrmSession = Depends(get_db),
) -> RedirectResponse:
    token_domain.revoke_api_token(db, current_user.id, token_id)
    return RedirectResponse("/tokens", status_code=303)
