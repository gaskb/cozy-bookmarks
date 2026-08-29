def test_organize_page_has_back_icon_not_text_link(authed_client):
    created = authed_client.post("/bookmarks", json={"url": "https://example.com"}).json()

    response = authed_client.get(f"/bookmarks/{created['id']}/organize")

    assert 'class="back-icon"' in response.text
    assert "Torna alla lista</a>" not in response.text


def test_new_bookmark_page_has_back_icon(authed_client):
    response = authed_client.get("/bookmarks/new")

    assert 'class="back-icon"' in response.text


def test_import_page_has_back_icon(authed_client):
    response = authed_client.get("/bookmarks/import")

    assert 'class="back-icon"' in response.text
