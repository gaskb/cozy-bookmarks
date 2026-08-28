import httpx

from app.integrations.metadata_extractor import fetch_metadata

HTML_WITH_OG_TAGS = """
<html>
<head>
  <title>Fallback title</title>
  <meta property="og:title" content="Real Title" />
  <meta property="og:description" content="A nice description" />
  <meta property="og:image" content="/images/cover.png" />
  <link rel="icon" href="/static/favicon.png" />
</head>
<body></body>
</html>
"""

HTML_WITHOUT_META = """
<html><head><title>Plain Title</title></head><body></body></html>
"""


def _client_for(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_fetch_metadata_parses_og_tags_and_resolves_relative_urls():
    def handler(request):
        return httpx.Response(200, headers={"content-type": "text/html"}, text=HTML_WITH_OG_TAGS)

    metadata = fetch_metadata("https://example.com/article", client=_client_for(handler))

    assert metadata.title == "Real Title"
    assert metadata.description == "A nice description"
    assert metadata.image_url == "https://example.com/images/cover.png"
    assert metadata.favicon_url == "https://example.com/static/favicon.png"


def test_fetch_metadata_falls_back_to_plain_title_and_default_favicon():
    def handler(request):
        return httpx.Response(200, headers={"content-type": "text/html"}, text=HTML_WITHOUT_META)

    metadata = fetch_metadata("https://example.com/page", client=_client_for(handler))

    assert metadata.title == "Plain Title"
    assert metadata.description is None
    assert metadata.image_url is None
    assert metadata.favicon_url == "https://example.com/favicon.ico"


def test_fetch_metadata_returns_empty_on_non_html_content_type():
    def handler(request):
        return httpx.Response(200, headers={"content-type": "application/pdf"}, content=b"%PDF")

    metadata = fetch_metadata("https://example.com/file.pdf", client=_client_for(handler))

    assert metadata.title is None
    assert metadata.favicon_url is None


def test_fetch_metadata_returns_empty_on_http_error_status():
    def handler(request):
        return httpx.Response(404, headers={"content-type": "text/html"}, text="not found")

    metadata = fetch_metadata("https://example.com/missing", client=_client_for(handler))

    assert metadata.title is None


def test_fetch_metadata_returns_empty_on_timeout():
    def handler(request):
        raise httpx.TimeoutException("timed out", request=request)

    metadata = fetch_metadata("https://example.com/slow", client=_client_for(handler))

    assert metadata.title is None


def test_fetch_metadata_returns_empty_on_connection_error():
    def handler(request):
        raise httpx.ConnectError("connection failed", request=request)

    metadata = fetch_metadata("https://example.com/down", client=_client_for(handler))

    assert metadata.title is None
