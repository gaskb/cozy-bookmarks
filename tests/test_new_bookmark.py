def test_new_bookmark_form_requires_auth(client):
    response = client.get("/bookmarks/new", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_new_bookmark_form_renders(authed_client):
    response = authed_client.get("/bookmarks/new")

    assert response.status_code == 200
    assert 'name="url"' in response.text


def test_list_page_shows_fab(authed_client):
    response = authed_client.get("/")

    assert 'href="/bookmarks/new"' in response.text
    assert 'class="fab"' in response.text


def test_new_bookmark_submit_creates_and_redirects_to_organize(authed_client):
    response = authed_client.post(
        "/bookmarks/new",
        data={"url": "https://example.com", "title": "Example", "tags": "idea"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert location.startswith("/bookmarks/") and location.endswith("/organize")

    list_response = authed_client.get("/?status=da_organizzare")
    assert "example.com" in list_response.text


def test_new_bookmark_submit_without_url_shows_error(authed_client):
    response = authed_client.post("/bookmarks/new", data={"url": ""})

    assert response.status_code == 400
    assert "Inserisci un URL" in response.text

    list_response = authed_client.get("/?status=da_organizzare")
    assert "Nessun bookmark" in list_response.text
