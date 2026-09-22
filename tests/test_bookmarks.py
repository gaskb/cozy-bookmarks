from app.domain.user import User, hash_password
from app.integrations.metadata_extractor import PageMetadata
from app.orchestration import save_bookmark


def _create_second_user(db_session) -> User:
    other = User(email="other@example.com", password_hash=hash_password("secret456"))
    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)
    return other


def test_create_bookmark_requires_auth(client):
    response = client.post("/bookmarks", json={"url": "https://example.com"})

    assert response.status_code == 401


def test_create_and_get_bookmark(authed_client):
    create_response = authed_client.post(
        "/bookmarks",
        json={"url": "https://example.com", "title": "Example", "tags": ["Python", "python", " web "]},
    )

    assert create_response.status_code == 201
    body = create_response.json()
    assert body["url"] == "https://example.com"
    assert body["title"] == "Example"
    assert body["status"] == "da_organizzare"
    assert body["tags"] == ["python", "web"]

    get_response = authed_client.get(f"/bookmarks/{body['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == body["id"]


def test_list_bookmarks_filters_by_status(authed_client):
    authed_client.post("/bookmarks", json={"url": "https://a.example.com"})
    second = authed_client.post("/bookmarks", json={"url": "https://b.example.com"}).json()
    authed_client.patch(f"/bookmarks/{second['id']}", json={"status": "organizzato"})

    all_response = authed_client.get("/bookmarks")
    assert len(all_response.json()) == 2

    filtered_response = authed_client.get("/bookmarks", params={"status_filter": "organizzato"})
    filtered = filtered_response.json()
    assert len(filtered) == 1
    assert filtered[0]["id"] == second["id"]


def test_update_bookmark(authed_client):
    created = authed_client.post("/bookmarks", json={"url": "https://example.com"}).json()

    response = authed_client.patch(
        f"/bookmarks/{created['id']}",
        json={"note": "da guardare", "tags": ["idea"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["note"] == "da guardare"
    assert body["tags"] == ["idea"]


def test_delete_bookmark(authed_client):
    created = authed_client.post("/bookmarks", json={"url": "https://example.com"}).json()

    delete_response = authed_client.delete(f"/bookmarks/{created['id']}")
    assert delete_response.status_code == 204

    get_response = authed_client.get(f"/bookmarks/{created['id']}")
    assert get_response.status_code == 404


def test_create_bookmark_populates_metadata_via_api(authed_client, monkeypatch):
    monkeypatch.setattr(
        save_bookmark,
        "fetch_metadata",
        lambda url: PageMetadata(title="From the page", description="Nice read"),
    )

    response = authed_client.post("/bookmarks", json={"url": "https://example.com"})

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "From the page"
    assert body["description"] == "Nice read"


def test_bookmarks_are_isolated_per_user(client, db_session, user):
    other_user = _create_second_user(db_session)

    login_as_user = client.post("/auth/login", json={"email": user.email, "password": "secret123"})
    assert login_as_user.status_code == 200
    created = client.post("/bookmarks", json={"url": "https://mine.example.com"}).json()

    client.post("/auth/logout")
    login_as_other = client.post(
        "/auth/login", json={"email": other_user.email, "password": "secret456"}
    )
    assert login_as_other.status_code == 200

    list_response = client.get("/bookmarks")
    assert list_response.json() == []

    get_response = client.get(f"/bookmarks/{created['id']}")
    assert get_response.status_code == 404

    delete_response = client.delete(f"/bookmarks/{created['id']}")
    assert delete_response.status_code == 404


def test_archive_and_unarchive_bookmark(db_session, user):
    from app.domain import bookmark as bookmark_domain
    from app.domain.bookmark import BookmarkStatus

    bm = bookmark_domain.create_bookmark(db_session, user.id, "https://example.com/arch")
    assert bm.status == BookmarkStatus.DA_ORGANIZZARE

    assert bookmark_domain.archive_bookmark(db_session, user.id, bm.id) is True
    assert bm.status == BookmarkStatus.ARCHIVIATO

    assert bookmark_domain.unarchive_bookmark(db_session, user.id, bm.id) is True
    assert bm.status == BookmarkStatus.ORGANIZZATO

