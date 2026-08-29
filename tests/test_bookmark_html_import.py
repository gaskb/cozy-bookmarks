from app.integrations.bookmark_html_import import parse_netscape_bookmarks

SAMPLE_EXPORT = """
<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3>Lavoro</H3>
    <DL><p>
        <DT><A HREF="https://example.com/one" ADD_DATE="1">Example One</A>
        <DT><A HREF="https://example.com/two" ADD_DATE="2">Example Two</A>
    </DL><p>
    <DT><A HREF="https://example.com/three">Example Three</A>
    <DT><A HREF="javascript:void(0)">A bookmarklet</A>
    <DT><A HREF="place:sort=1">Firefox internal</A>
</DL><p>
"""


def test_parses_all_http_links():
    links = parse_netscape_bookmarks(SAMPLE_EXPORT)
    urls = [link.url for link in links]

    assert "https://example.com/one" in urls
    assert "https://example.com/two" in urls
    assert "https://example.com/three" in urls


def test_extracts_titles():
    links = parse_netscape_bookmarks(SAMPLE_EXPORT)
    by_url = {link.url: link.title for link in links}

    assert by_url["https://example.com/one"] == "Example One"


def test_skips_non_http_links():
    links = parse_netscape_bookmarks(SAMPLE_EXPORT)
    urls = [link.url for link in links]

    assert not any(u.startswith("javascript:") for u in urls)
    assert not any(u.startswith("place:") for u in urls)


def test_empty_document_returns_empty_list():
    assert parse_netscape_bookmarks("<html><body>no links here</body></html>") == []
