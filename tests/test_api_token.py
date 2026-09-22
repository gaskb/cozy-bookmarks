from app.domain import api_token as token_domain
from app.domain.user import User, hash_password


def test_create_and_verify_token_domain(db_session, user):
    tok, raw = token_domain.create_api_token(db_session, user.id, "Test Token")

    assert tok.name == "Test Token"
    assert tok.token_prefix.startswith("cbk_")
    assert tok.last_used_at is None
    assert tok.revoked_at is None

    resolved_user = token_domain.get_user_by_api_token(db_session, raw)
    assert resolved_user is not None
    assert resolved_user.id == user.id

    db_session.refresh(tok)
    assert tok.last_used_at is not None


def test_revoked_token_cannot_authenticate(db_session, user):
    tok, raw = token_domain.create_api_token(db_session, user.id, "To Revoke")

    revoked = token_domain.revoke_api_token(db_session, user.id, tok.id)
    assert revoked is True

    resolved_user = token_domain.get_user_by_api_token(db_session, raw)
    assert resolved_user is None


def test_bearer_token_authenticates_api_requests(client, db_session, user):
    _, raw = token_domain.create_api_token(db_session, user.id, "Script Token")

    headers = {"Authorization": f"Bearer {raw}"}
    me_resp = client.get("/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == user.email

    create_resp = client.post(
        "/bookmarks",
        headers=headers,
        json={"url": "https://token-bookmark.com", "title": "Token Bookmark"},
    )
    assert create_resp.status_code == 201
    assert create_resp.json()["url"] == "https://token-bookmark.com"


def test_invalid_bearer_token_rejected(client):
    headers = {"Authorization": "Bearer cbk_invalid_and_nonexistent"}
    resp = client.get("/auth/me", headers=headers)
    assert resp.status_code == 401


def test_tokens_api_crud(authed_client, user):
    create_resp = authed_client.post(
        "/api/tokens",
        json={"name": "CLI Token"},
    )
    assert create_resp.status_code == 201
    token_data = create_resp.json()
    assert token_data["name"] == "CLI Token"
    assert "token" in token_data
    token_id = token_data["id"]

    list_resp = authed_client.get("/api/tokens")
    assert list_resp.status_code == 200
    assert any(t["id"] == token_id for t in list_resp.json())

    delete_resp = authed_client.delete(f"/api/tokens/{token_id}")
    assert delete_resp.status_code == 200

    list_resp_after = authed_client.get("/api/tokens")
    token_after = next(t for t in list_resp_after.json() if t["id"] == token_id)
    assert token_after["revoked_at"] is not None


def test_tokens_web_ui(authed_client, user):
    get_resp = authed_client.get("/tokens")
    assert get_resp.status_code == 200
    assert "Personal Access Tokens" in get_resp.text

    post_resp = authed_client.post(
        "/tokens",
        data={"name": "Mac Shortcut"},
    )
    assert post_resp.status_code == 200
    assert "Copia subito questo token" in post_resp.text
    assert "Mac Shortcut" in post_resp.text
    assert "cbk_" in post_resp.text
