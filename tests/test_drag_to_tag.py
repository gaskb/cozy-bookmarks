def _create_bookmark(api_client, url, **kwargs):
    payload = {"url": url, **kwargs}
    return api_client.post("/bookmarks", json=payload).json()


def test_add_tag_route_requires_auth(client):
    response = client.post(
        "/bookmarks/1/tags/add", data={"name": "apps"}, follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_add_tag_adds_without_replacing_existing_tags(authed_client):
    created = _create_bookmark(authed_client, "https://example.com", tags=["python"])

    authed_client.post(f"/bookmarks/{created['id']}/tags/add", data={"name": "apps"})

    updated = authed_client.get(f"/bookmarks/{created['id']}").json()
    assert set(updated["tags"]) == {"python", "apps"}


def test_add_tag_is_idempotent(authed_client):
    created = _create_bookmark(authed_client, "https://example.com", tags=["apps"])

    authed_client.post(f"/bookmarks/{created['id']}/tags/add", data={"name": "apps"})

    updated = authed_client.get(f"/bookmarks/{created['id']}").json()
    assert updated["tags"] == ["apps"]


def test_add_tag_creates_the_tag_if_it_does_not_exist_yet(authed_client):
    created = _create_bookmark(authed_client, "https://example.com")

    authed_client.post(f"/bookmarks/{created['id']}/tags/add", data={"name": "brand-new"})

    updated = authed_client.get(f"/bookmarks/{created['id']}").json()
    assert updated["tags"] == ["brand-new"]


def test_add_tag_moves_bookmark_out_of_da_organizzare(authed_client):
    created = _create_bookmark(authed_client, "https://example.com")
    assert created["status"] == "da_organizzare"

    authed_client.post(f"/bookmarks/{created['id']}/tags/add", data={"name": "apps"})

    updated = authed_client.get(f"/bookmarks/{created['id']}").json()
    assert updated["status"] == "organizzato"


def test_list_page_shows_drop_bar_only_when_pinned_tags_exist(authed_client):
    without_pins = authed_client.get("/")
    assert 'id="tag-drop-bar"' not in without_pins.text

    authed_client.post("/tags/pin", data={"name": "apps"})

    with_pins = authed_client.get("/")
    assert 'id="tag-drop-bar"' in with_pins.text
    assert 'data-tag-name="apps"' in with_pins.text
