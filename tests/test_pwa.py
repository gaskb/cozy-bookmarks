def test_manifest_has_expected_shape(client):
    response = client.get("/manifest.json")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/manifest+json")

    body = response.json()
    assert body["name"] == "Cozy Bookmarks"
    assert body["display"] == "standalone"
    assert body["share_target"]["action"] == "/share-target"
    assert body["share_target"]["method"] == "POST"
    assert body["share_target"]["params"] == {"title": "title", "text": "text", "url": "url"}
    assert len(body["icons"]) >= 2


def test_service_worker_is_served_at_root_scope(client):
    response = client.get("/sw.js")

    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]
    assert "addEventListener" in response.text


def test_icons_are_served(client):
    response = client.get("/static/icons/icon-192.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
