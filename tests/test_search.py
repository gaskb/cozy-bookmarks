def _create_bookmark(api_client, url, **kwargs):
    payload = {"url": url, **kwargs}
    return api_client.post("/bookmarks", json=payload).json()


def test_search_matches_title(authed_client):
    _create_bookmark(authed_client, "https://a.example.com", title="Ricetta torta di mele")
    _create_bookmark(authed_client, "https://b.example.com", title="Articolo tech")

    response = authed_client.get("/?status=da_organizzare&q=torta")

    assert "a.example.com" in response.text or "Ricetta torta" in response.text
    assert "Articolo tech" not in response.text


def test_search_matches_note(authed_client):
    created = _create_bookmark(authed_client, "https://a.example.com")
    authed_client.patch(f"/bookmarks/{created['id']}", json={"note": "contiene una parola rara xyzzy"})
    _create_bookmark(authed_client, "https://b.example.com")

    response = authed_client.get("/?status=da_organizzare&q=xyzzy")

    assert "a.example.com" in response.text
    assert "b.example.com" not in response.text


def test_search_matches_url(authed_client):
    _create_bookmark(authed_client, "https://uniquehost123.example.com")
    _create_bookmark(authed_client, "https://other.example.com")

    response = authed_client.get("/?status=da_organizzare&q=uniquehost123")

    assert "uniquehost123.example.com" in response.text
    assert "other.example.com" not in response.text


def test_search_matches_tag_name(authed_client):
    _create_bookmark(authed_client, "https://a.example.com", tags=["raretagname"])
    _create_bookmark(authed_client, "https://b.example.com", tags=["other"])

    response = authed_client.get("/?status=da_organizzare&q=raretagname")

    assert "a.example.com" in response.text
    assert "b.example.com" not in response.text


def test_search_is_case_insensitive(authed_client):
    _create_bookmark(authed_client, "https://a.example.com", title="UPPERCASE Title")

    response = authed_client.get("/?status=da_organizzare&q=uppercase")

    assert "UPPERCASE Title" in response.text


def test_search_combines_with_status_filter(authed_client):
    created = _create_bookmark(authed_client, "https://a.example.com", title="Cercami")
    authed_client.patch(f"/bookmarks/{created['id']}", json={"status": "organizzato"})

    todo_response = authed_client.get("/?status=da_organizzare&q=Cercami")
    done_response = authed_client.get("/?status=organizzato&q=Cercami")

    assert "a.example.com" not in todo_response.text
    assert "a.example.com" in done_response.text


def test_empty_search_returns_everything(authed_client):
    _create_bookmark(authed_client, "https://a.example.com")
    _create_bookmark(authed_client, "https://b.example.com")

    response = authed_client.get("/?status=da_organizzare&q=")

    assert "a.example.com" in response.text
    assert "b.example.com" in response.text


def test_search_box_preserves_query_value(authed_client):
    response = authed_client.get("/?status=da_organizzare&q=hello")

    assert 'value="hello"' in response.text
