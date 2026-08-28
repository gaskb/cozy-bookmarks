def test_quick_save_requires_auth(client):
    response = client.post("/save", data={"url": "https://example.com"})

    assert response.status_code == 401


def test_quick_save_with_explicit_url(authed_client):
    response = authed_client.post(
        "/save", data={"url": "https://example.com/video", "title": "A video"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "saved"
    assert "bookmark_id" in body

    saved = authed_client.get(f"/bookmarks/{body['bookmark_id']}").json()
    assert saved["url"] == "https://example.com/video"
    assert saved["title"] == "A video"


def test_quick_save_extracts_url_from_shared_text(authed_client):
    shared_text = "Guarda questo https://vm.tiktok.com/abc123 assurdo"

    response = authed_client.post("/save", data={"text": shared_text})

    assert response.status_code == 201
    body = response.json()

    saved = authed_client.get(f"/bookmarks/{body['bookmark_id']}").json()
    assert saved["url"] == "https://vm.tiktok.com/abc123"
    assert saved["note"] == shared_text


def test_quick_save_returns_400_when_no_url_found(authed_client):
    response = authed_client.post("/save", data={"text": "nessun link qui dentro"})

    assert response.status_code == 400


def test_quick_save_prefers_explicit_url_over_text(authed_client):
    response = authed_client.post(
        "/save",
        data={"url": "https://example.com/real", "text": "mentions https://example.com/decoy too"},
    )

    body = response.json()
    saved = authed_client.get(f"/bookmarks/{body['bookmark_id']}").json()
    assert saved["url"] == "https://example.com/real"
