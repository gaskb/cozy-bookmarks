def test_login_page_renders(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert "form" in response.text.lower()


def test_list_page_redirects_to_login_when_unauthenticated(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_login_submit_success_redirects_to_list(client, user):
    response = client.post(
        "/login", data={"email": user.email, "password": "secret123"}, follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert "session" in response.cookies


def test_login_submit_wrong_password_shows_error(client, user):
    response = client.post("/login", data={"email": user.email, "password": "wrong"})

    assert response.status_code == 401
    assert "non corretti" in response.text


def test_logout_redirects_to_login_and_clears_session(authed_client):
    response = authed_client.post("/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"

    list_response = authed_client.get("/", follow_redirects=False)
    assert list_response.status_code == 303
