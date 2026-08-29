import json


def _create_bookmark(api_client, url, **kwargs):
    payload = {"url": url, **kwargs}
    return api_client.post("/bookmarks", json=payload).json()


def test_organize_page_shows_most_used_tags(authed_client):
    _create_bookmark(authed_client, "https://a.example.com", tags=["python"])
    _create_bookmark(authed_client, "https://b.example.com", tags=["python"])
    created = _create_bookmark(authed_client, "https://c.example.com", tags=["rare"])

    response = authed_client.get(f"/bookmarks/{created['id']}/organize")

    assert 'data-tag="python"' in response.text
    assert "Più usati" in response.text


def test_organize_page_shows_recent_tags(authed_client):
    _create_bookmark(authed_client, "https://a.example.com", tags=["freshtag"])
    created = _create_bookmark(authed_client, "https://b.example.com")

    response = authed_client.get(f"/bookmarks/{created['id']}/organize")

    assert 'data-tag="freshtag"' in response.text
    assert "Recenti" in response.text


def test_organize_page_embeds_all_tags_as_json(authed_client):
    _create_bookmark(authed_client, "https://a.example.com", tags=["python", "webdev"])
    created = _create_bookmark(authed_client, "https://b.example.com")

    response = authed_client.get(f"/bookmarks/{created['id']}/organize")

    start = response.text.index('id="all-tags-data">') + len('id="all-tags-data">')
    end = response.text.index("</script>", start)
    payload = json.loads(response.text[start:end])
    assert set(payload) == {"python", "webdev"}


def test_tag_names_with_special_characters_are_not_escaped_oddly(authed_client):
    created = _create_bookmark(authed_client, "https://a.example.com", tags=["c++"])

    response = authed_client.get(f"/bookmarks/{created['id']}/organize")

    start = response.text.index('id="all-tags-data">') + len('id="all-tags-data">')
    end = response.text.index("</script>", start)
    payload = json.loads(response.text[start:end])
    assert "c++" in payload
