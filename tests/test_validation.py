import pytest
from app.validation import (
    ValidationError,
    validate_note,
    validate_tag_name,
    validate_title,
    validate_token_name,
    validate_url,
)


def test_validate_url_success():
    assert validate_url("https://example.com/test") == "https://example.com/test"
    assert validate_url("http://sub.domain.org/path?q=1#frag") == "http://sub.domain.org/path?q=1#frag"


def test_validate_url_rejects_empty_or_non_http():
    with pytest.raises(ValidationError):
        validate_url("")
    with pytest.raises(ValidationError):
        validate_url("   ")
    with pytest.raises(ValidationError):
        validate_url("ftp://example.com/file")
    with pytest.raises(ValidationError):
        validate_url("file:///etc/passwd")
    with pytest.raises(ValidationError):
        validate_url("javascript:alert(1)")
    with pytest.raises(ValidationError):
        validate_url("not-a-url")


def test_validate_url_rejects_overlong():
    long_url = "https://example.com/" + "a" * 2050
    with pytest.raises(ValidationError, match="troppo lungo"):
        validate_url(long_url)


def test_validate_title_and_note_limits():
    assert validate_title("Short Title") == "Short Title"
    assert validate_title(None) is None
    with pytest.raises(ValidationError, match="titolo"):
        validate_title("A" * 501)

    assert validate_note("Short note") == "Short note"
    assert validate_note(None) is None
    with pytest.raises(ValidationError, match="nota"):
        validate_note("A" * 10001)


def test_validate_tag_name_limits():
    assert validate_tag_name("Python") == "python"
    with pytest.raises(ValidationError):
        validate_tag_name("")
    with pytest.raises(ValidationError, match="tag"):
        validate_tag_name("t" * 51)


def test_validate_token_name_limits():
    assert validate_token_name("CLI Token") == "CLI Token"
    with pytest.raises(ValidationError):
        validate_token_name("")
    with pytest.raises(ValidationError, match="token"):
        validate_token_name("t" * 101)


def test_api_bookmark_create_validation(authed_client):
    # Invalid URL scheme
    resp = authed_client.post("/bookmarks", json={"url": "javascript:alert(1)"})
    assert resp.status_code == 422

    # Overlong title
    resp = authed_client.post(
        "/bookmarks", json={"url": "https://example.com", "title": "A" * 501}
    )
    assert resp.status_code == 422

    # Overlong tag
    resp = authed_client.post(
        "/bookmarks", json={"url": "https://example.com", "tags": ["t" * 51]}
    )
    assert resp.status_code == 422


def test_web_bookmark_create_validation(authed_client):
    # Invalid URL scheme in web form
    resp = authed_client.post(
        "/bookmarks/new", data={"url": "ftp://example.com/file"}
    )
    assert resp.status_code == 400
    assert "http://" in resp.text
