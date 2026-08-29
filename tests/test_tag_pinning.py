def _create_bookmark(api_client, url, **kwargs):
    payload = {"url": url, **kwargs}
    return api_client.post("/bookmarks", json=payload).json()


def test_pin_tag_requires_auth(client):
    response = client.post("/tags/pin", data={"name": "ricette"}, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_pinning_a_new_name_creates_and_shows_it_as_a_primary_tab(authed_client):
    response = authed_client.post("/tags/pin", data={"name": "Ricette"}, follow_redirects=False)
    assert response.status_code == 303

    list_response = authed_client.get("/")
    assert '<a href="/?status=da_organizzare&tag=ricette"' in list_response.text


def test_pinning_an_existing_tag_removes_it_from_the_secondary_row(authed_client):
    _create_bookmark(authed_client, "https://example.com", tags=["python"])

    before = authed_client.get("/")
    assert 'class="tag-filter"' in before.text
    assert ">python</a>" in before.text

    authed_client.post("/tags/pin", data={"name": "python"})

    after = authed_client.get("/")
    assert '<a href="/?status=da_organizzare&tag=python"' in after.text
    # secondary tag-filter row should no longer list it since it's pinned now
    tag_filter_section = after.text.split('class="tag-filter"')[1] if 'class="tag-filter"' in after.text else ""
    assert ">python</a>" not in tag_filter_section


def test_pinned_tag_still_filters_bookmarks(authed_client):
    _create_bookmark(authed_client, "https://python.example.com", tags=["python"])
    _create_bookmark(authed_client, "https://other.example.com", tags=["other"])
    authed_client.post("/tags/pin", data={"name": "python"})

    response = authed_client.get("/?status=da_organizzare&tag=python")

    assert "python.example.com" in response.text
    assert "other.example.com" not in response.text


def test_unpin_tag_requires_auth(client):
    response = client.post("/tags/unpin", data={"name": "python"}, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_unpin_moves_tag_back_to_secondary_row(authed_client):
    authed_client.post("/tags/pin", data={"name": "python"})
    authed_client.post("/tags/unpin", data={"name": "python"})

    response = authed_client.get("/")

    assert "tab-pinned" not in response.text
    assert 'class="tag-filter"' in response.text
    assert ">python</a>" in response.text


def test_pin_tag_with_blank_name_is_a_noop(authed_client):
    response = authed_client.post("/tags/pin", data={"name": "   "}, follow_redirects=False)

    assert response.status_code == 303
    list_response = authed_client.get("/")
    assert "tab-pinned" not in list_response.text
