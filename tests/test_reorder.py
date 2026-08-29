from app.domain.bookmark import reorder_bookmark


def _create_bookmark(api_client, url, **kwargs):
    payload = {"url": url, **kwargs}
    return api_client.post("/bookmarks", json=payload).json()


def test_new_bookmarks_default_to_newest_first(authed_client):
    first = _create_bookmark(authed_client, "https://a.example.com")
    second = _create_bookmark(authed_client, "https://b.example.com")

    response = authed_client.get("/?status=da_organizzare").text
    assert response.index("b.example.com") < response.index("a.example.com")
    assert first["id"] and second["id"]


def test_reorder_route_requires_auth(client):
    response = client.post(
        "/bookmarks/1/reorder", data={"above_id": "", "below_id": ""}, follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_reorder_moves_bookmark_between_two_others(authed_client):
    a = _create_bookmark(authed_client, "https://a.example.com")
    b = _create_bookmark(authed_client, "https://b.example.com")
    c = _create_bookmark(authed_client, "https://c.example.com")
    # default order (newest first): c, b, a

    # move a to between c and b -> new order: c, a, b
    authed_client.post(
        f"/bookmarks/{a['id']}/reorder",
        data={"above_id": str(c["id"]), "below_id": str(b["id"])},
    )

    text = authed_client.get("/?status=da_organizzare").text
    pos_c = text.index("c.example.com")
    pos_a = text.index("a.example.com")
    pos_b = text.index("b.example.com")
    assert pos_c < pos_a < pos_b


def test_reorder_to_the_very_top(authed_client):
    a = _create_bookmark(authed_client, "https://a.example.com")
    b = _create_bookmark(authed_client, "https://b.example.com")
    # default order: b, a

    authed_client.post(f"/bookmarks/{a['id']}/reorder", data={"above_id": "", "below_id": str(b["id"])})

    text = authed_client.get("/?status=da_organizzare").text
    assert text.index("a.example.com") < text.index("b.example.com")


def test_reorder_to_the_very_bottom(authed_client):
    a = _create_bookmark(authed_client, "https://a.example.com")
    b = _create_bookmark(authed_client, "https://b.example.com")
    # default order: b, a -> move b to the bottom

    authed_client.post(f"/bookmarks/{b['id']}/reorder", data={"above_id": str(a["id"]), "below_id": ""})

    text = authed_client.get("/?status=da_organizzare").text
    assert text.index("a.example.com") < text.index("b.example.com")


def test_reorder_nonexistent_bookmark_is_a_noop(authed_client, db_session, user):
    # should not raise even if the bookmark id doesn't exist for this user
    reorder_bookmark(db_session, user.id, 9999, above_id=None, below_id=None)


def test_bookmark_row_includes_drag_handle(authed_client):
    _create_bookmark(authed_client, "https://example.com")

    response = authed_client.get("/?status=da_organizzare")

    assert 'class="drag-handle"' in response.text
