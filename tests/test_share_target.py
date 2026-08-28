def test_share_target_requires_auth_redirects_to_login(client):
    response = client.post(
        "/share-target", data={"url": "https://example.com"}, follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_share_target_with_explicit_url_saves_and_redirects(authed_client):
    response = authed_client.post(
        "/share-target",
        data={"url": "https://example.com/video", "title": "A video"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/?status=da_organizzare&shared=1"

    list_response = authed_client.get("/")
    assert "example.com/video" in list_response.text


def test_share_target_extracts_url_from_shared_text(authed_client):
    response = authed_client.post(
        "/share-target",
        data={"text": "guarda questo https://vm.tiktok.com/xyz assurdo"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "shared=1" in response.headers["location"]

    list_response = authed_client.get("/")
    assert "vm.tiktok.com/xyz" in list_response.text


def test_share_target_without_resolvable_url_redirects_with_error(authed_client):
    response = authed_client.post(
        "/share-target", data={"text": "nessun link qui"}, follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/?share_error=no_url"

    list_response = authed_client.get(response.headers["location"])
    assert "Nessun link trovato" in list_response.text


def test_share_confirmation_banner_shown_after_redirect(authed_client):
    response = authed_client.get("/?shared=1")

    assert "Bookmark salvato" in response.text
