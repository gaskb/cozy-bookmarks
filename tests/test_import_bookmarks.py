SAMPLE_EXPORT = """
<!DOCTYPE NETSCAPE-Bookmark-file-1>
<DL><p>
    <DT><A HREF="https://example.com/one">Example One</A>
    <DT><A HREF="https://example.com/two">Example Two</A>
    <DT><A HREF="javascript:void(0)">A bookmarklet</A>
</DL><p>
"""


def _upload(client, content: str, filename: str = "bookmarks.html"):
    return client.post(
        "/bookmarks/import",
        files={"file": (filename, content, "text/html")},
        follow_redirects=False,
    )


def test_import_form_requires_auth(client):
    response = client.get("/bookmarks/import", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_import_form_renders(authed_client):
    response = authed_client.get("/bookmarks/import")

    assert response.status_code == 200
    assert 'type="file"' in response.text


def test_import_creates_bookmarks_and_skips_non_http_links(authed_client):
    response = _upload(authed_client, SAMPLE_EXPORT)

    assert response.status_code == 303
    assert response.headers["location"] == "/?imported=2&skipped=0"

    list_response = authed_client.get("/?status=da_organizzare")
    assert "example.com/one" in list_response.text
    assert "example.com/two" in list_response.text


def test_import_skips_duplicate_urls_on_second_import(authed_client):
    _upload(authed_client, SAMPLE_EXPORT)

    response = _upload(authed_client, SAMPLE_EXPORT)

    assert response.headers["location"] == "/?imported=0&skipped=2"


def test_import_confirmation_banner_shown(authed_client):
    response = authed_client.get("/?imported=3&skipped=1")

    assert "Importati 3 bookmark" in response.text
    assert "1 già presenti saltati" in response.text


def test_import_requires_auth_on_post(client):
    response = _upload(client, SAMPLE_EXPORT)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"
