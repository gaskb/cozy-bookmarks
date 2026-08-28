def _create_bookmark(api_client, url, **kwargs):
    payload = {"url": url, **kwargs}
    return api_client.post("/bookmarks", json=payload).json()


def test_list_page_shows_only_matching_status(authed_client):
    _create_bookmark(authed_client, "https://a.example.com")
    organized = _create_bookmark(authed_client, "https://b.example.com")
    authed_client.patch(f"/bookmarks/{organized['id']}", json={"status": "organizzato"})

    todo_response = authed_client.get("/?status=da_organizzare")
    assert "a.example.com" in todo_response.text
    assert "b.example.com" not in todo_response.text

    done_response = authed_client.get("/?status=organizzato")
    assert "b.example.com" in done_response.text
    assert "a.example.com" not in done_response.text


def test_list_page_filters_by_tag(authed_client):
    _create_bookmark(authed_client, "https://python.example.com", tags=["python"])
    _create_bookmark(authed_client, "https://web.example.com", tags=["web"])

    response = authed_client.get("/?status=da_organizzare&tag=python")

    assert "python.example.com" in response.text
    assert "web.example.com" not in response.text


def test_list_page_renders_tag_names_not_object_repr(authed_client):
    _create_bookmark(authed_client, "https://example.com", tags=["python"])

    response = authed_client.get("/?status=da_organizzare")

    assert '<span class="tag">python</span>' in response.text
    assert "Tag object at" not in response.text


def test_list_page_shows_empty_state(authed_client):
    response = authed_client.get("/?status=organizzato")

    assert "Nessun bookmark" in response.text


def test_delete_row_via_htmx_removes_bookmark(authed_client):
    created = _create_bookmark(authed_client, "https://example.com")

    response = authed_client.delete(f"/bookmarks/{created['id']}/delete")
    assert response.status_code == 200
    assert response.text == ""

    get_response = authed_client.get(f"/bookmarks/{created['id']}")
    assert get_response.status_code == 404
