from app.orchestration import save_bookmark


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


def test_bookmark_row_card_links_to_organize_instead_of_a_visible_link(authed_client):
    created = _create_bookmark(authed_client, "https://example.com", title="Example")

    response = authed_client.get("/?status=da_organizzare")

    assert f'href="/bookmarks/{created["id"]}/organize"' in response.text
    assert ">Organizza<" not in response.text


def test_bookmark_row_title_still_links_to_the_real_url(authed_client):
    _create_bookmark(authed_client, "https://example.com", title="Example")

    response = authed_client.get("/?status=da_organizzare")

    assert 'class="bookmark-title" href="https://example.com"' in response.text


def test_bookmark_row_shows_created_at_timestamp(authed_client):
    created = _create_bookmark(authed_client, "https://example.com")
    created_at = created["created_at"]
    expected = created_at[:16].replace("T", " ")

    response = authed_client.get("/?status=da_organizzare")

    assert f'<p class="created-at">{expected}</p>' in response.text


def test_delete_row_via_htmx_removes_bookmark(authed_client):
    created = _create_bookmark(authed_client, "https://example.com")

    response = authed_client.delete(f"/bookmarks/{created['id']}/delete")
    assert response.status_code == 200
    assert response.text == ""

    get_response = authed_client.get(f"/bookmarks/{created['id']}")
    assert get_response.status_code == 404


def test_organize_form_renders_bookmark_fields(authed_client):
    created = _create_bookmark(
        authed_client, "https://example.com", title="Hello", tags=["idea", "python"]
    )

    response = authed_client.get(f"/bookmarks/{created['id']}/organize")

    assert response.status_code == 200
    assert 'value="Hello"' in response.text
    assert 'value="idea, python"' in response.text
    assert "Tag object at" not in response.text


def test_organize_form_prefills_ai_suggestion_when_no_real_tags(authed_client, monkeypatch):
    monkeypatch.setattr(
        save_bookmark, "suggest_tags_safely", lambda *args, **kwargs: ["python", "homelab"]
    )
    created = _create_bookmark(authed_client, "https://example.com")

    response = authed_client.get(f"/bookmarks/{created['id']}/organize")

    assert 'value="python, homelab"' in response.text
    assert "suggerimento AI" in response.text


def test_organize_form_does_not_apply_ai_suggestion_as_real_tags(authed_client, monkeypatch):
    monkeypatch.setattr(save_bookmark, "suggest_tags_safely", lambda *args, **kwargs: ["python"])
    created = _create_bookmark(authed_client, "https://example.com")

    saved = authed_client.get(f"/bookmarks/{created['id']}").json()

    assert saved["tags"] == []


def test_organize_form_hides_ai_hint_when_real_tags_already_exist(authed_client):
    created = _create_bookmark(authed_client, "https://example.com", tags=["manual"])

    response = authed_client.get(f"/bookmarks/{created['id']}/organize")

    assert "suggerimento AI" not in response.text


def test_organize_form_redirects_when_bookmark_missing(authed_client):
    response = authed_client.get("/bookmarks/999/organize", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/"


def test_organize_submit_updates_and_marks_organized(authed_client):
    created = _create_bookmark(authed_client, "https://example.com")

    response = authed_client.post(
        f"/bookmarks/{created['id']}/organize",
        data={"title": "New title", "note": "context", "tags": "idea, later"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/?status=organizzato"

    updated = authed_client.get(f"/bookmarks/{created['id']}").json()
    assert updated["title"] == "New title"
    assert updated["note"] == "context"
    assert updated["status"] == "organizzato"
    assert set(updated["tags"]) == {"idea", "later"}


def test_organize_submit_advances_to_next_bookmark(authed_client):
    first = _create_bookmark(authed_client, "https://first.example.com")
    second = _create_bookmark(authed_client, "https://second.example.com")

    response = authed_client.post(
        f"/bookmarks/{first['id']}/organize",
        data={"title": "", "note": "", "tags": ""},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == f"/bookmarks/{second['id']}/organize"


def test_organize_delete_advances_to_next_bookmark(authed_client):
    first = _create_bookmark(authed_client, "https://first.example.com")
    second = _create_bookmark(authed_client, "https://second.example.com")

    response = authed_client.post(f"/bookmarks/{first['id']}/organize/delete", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == f"/bookmarks/{second['id']}/organize"

    get_response = authed_client.get(f"/bookmarks/{first['id']}")
    assert get_response.status_code == 404


def test_bookmark_organize_page_requires_auth(client):
    response = client.get("/bookmarks/1/organize", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"
