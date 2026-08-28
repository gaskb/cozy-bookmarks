def test_login_success_sets_cookie(client, user):
    response = client.post("/auth/login", json={"email": user.email, "password": "secret123"})

    assert response.status_code == 200
    assert response.json()["email"] == user.email
    assert "session" in response.cookies


def test_login_wrong_password(client, user):
    response = client.post("/auth/login", json={"email": user.email, "password": "wrong"})

    assert response.status_code == 401


def test_login_unknown_email(client):
    response = client.post("/auth/login", json={"email": "nobody@example.com", "password": "whatever"})

    assert response.status_code == 401


def test_me_requires_auth(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_returns_current_user(authed_client, user):
    response = authed_client.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["email"] == user.email


def test_logout_invalidates_session(authed_client):
    logout_response = authed_client.post("/auth/logout")
    assert logout_response.status_code == 200

    me_response = authed_client.get("/auth/me")
    assert me_response.status_code == 401
