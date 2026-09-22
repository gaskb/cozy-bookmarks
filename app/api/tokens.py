from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as OrmSession

from app.api.deps import get_current_user
from app.api.schemas import TokenCreate, TokenCreatedOut, TokenOut
from app.db import get_db
from app.domain import api_token as token_domain
from app.domain.user import User

router = APIRouter(prefix="/api/tokens", tags=["tokens"])


@router.get("", response_model=list[TokenOut])
def list_tokens(
    current_user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> list[token_domain.ApiToken]:
    return token_domain.list_api_tokens(db, current_user.id)


@router.post("", response_model=TokenCreatedOut, status_code=status.HTTP_201_CREATED)
def create_token(
    payload: TokenCreate,
    current_user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> TokenCreatedOut:
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token name cannot be empty")

    token_obj, raw_token = token_domain.create_api_token(db, current_user.id, name)
    return TokenCreatedOut(
        id=token_obj.id,
        name=token_obj.name,
        token=raw_token,
        token_prefix=token_obj.token_prefix,
        created_at=token_obj.created_at,
    )


@router.delete("/{token_id}")
def revoke_token(
    token_id: int,
    current_user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> dict[str, str]:
    success = token_domain.revoke_api_token(db, current_user.id, token_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found or already revoked")
    return {"status": "ok"}
