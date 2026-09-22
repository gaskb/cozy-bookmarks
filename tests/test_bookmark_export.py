import json

from app.domain import bookmark as bookmark_domain
from app.domain.user import User, hash_password
from app.integrations.bookmark_export import export_json_data, export_netscape_html


def test_export_netscape_html_format(db_session, user):
    b1 = bookmark_domain.create_bookmark(
        db_session,
        user_id=user.id,
        url="https://example.com/test?a=1&b=2",
        title="Example <Title> & Co",
        note="A nice personal note",
        tag_names=["python", "web & dev"],
    )

    html_out = export_netscape_html([b1])

    assert "<!DOCTYPE NETSCAPE-Bookmark-file-1>" in html_out
    assert "<TITLE>Bookmarks</TITLE>" in html_out
    assert "https://example.com/test?a=1&amp;b=2" in html_out
    assert "Example &lt;Title&gt; &amp; Co" in html_out
    assert 'TAGS="python,web &amp; dev"' in html_out
    assert "<DD>A nice personal note" in html_out


def test_export_json_data_format(db_session, user):
    b1 = bookmark_domain.create_bookmark(
        db_session,
        user_id=user.id,
        url="https://example.com",
        title="Example",
        note="My note",
        description="OG Description",
        tag_names=["python"],
        ai_suggested_tags=["coding", "tools"],
    )

    data = export_json_data([b1])

    assert len(data) == 1
    item = data[0]
    assert item["id"] == b1.id
    assert item["url"] == "https://example.com"
    assert item["title"] == "Example"
    assert item["note"] == "My note"
    assert item["description"] == "OG Description"
    assert item["tags"] == ["python"]
    assert "coding" in item["ai_suggested_tags"]
    assert "tools" in item["ai_suggested_tags"]
    assert item["status"] == "da_organizzare"


def test_export_endpoints_http(authed_client, user):
    authed_client.post(
        "/bookmarks",
        json={"url": "https://export-test.com", "title": "Export Test", "tags": ["test"]},
    )

    html_res = authed_client.get("/bookmarks/export/html")
    assert html_res.status_code == 200
    assert "attachment; filename=\"cozy-bookmarks.html\"" in html_res.headers.get("content-disposition", "")
    assert "https://export-test.com" in html_res.text
    assert "Export Test" in html_res.text

    json_res = authed_client.get("/bookmarks/export/json")
    assert json_res.status_code == 200
    assert "attachment; filename=\"cozy-bookmarks.json\"" in json_res.headers.get("content-disposition", "")
    exported_data = json_res.json()
    assert isinstance(exported_data, list)
    assert any(b["url"] == "https://export-test.com" for b in exported_data)


def test_export_isolation_between_users(authed_client, db_session, user):
    # Create another user and bookmark
    other_user = User(email="other@example.com", password_hash=hash_password("pwd123"))
    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)

    bookmark_domain.create_bookmark(
        db_session,
        user_id=other_user.id,
        url="https://secret-other-user.com",
        title="Other Secret",
    )

    html_res = authed_client.get("/bookmarks/export/html")
    assert "https://secret-other-user.com" not in html_res.text

    json_res = authed_client.get("/bookmarks/export/json")
    assert not any(b["url"] == "https://secret-other-user.com" for b in json_res.json())
