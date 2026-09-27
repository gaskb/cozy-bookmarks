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


def test_ssrf_rejects_private_and_loopback_ips():
    unsafe_urls = [
        "http://127.0.0.1:8000/admin",
        "http://127.0.0.1/status",
        "http://localhost/secret",
        "http://10.0.0.1/internal",
        "http://192.168.1.1/router",
        "http://172.16.0.1/private",
        "http://169.254.169.254/latest/meta-data/",
        "http://0.0.0.0/",
        "http://[::1]/",
        "http://[fc00::1]/",
        "http://[fe80::1]/",
        "ftp://example.com/file",
        "file:///etc/passwd",
        "javascript:alert(1)",
    ]
    for url in unsafe_urls:
        metadata = fetch_metadata(url)
        assert metadata.title is None, f"Expected {url} to be blocked by SSRF check"


def test_ssrf_blocks_redirect_to_private_ip(monkeypatch):
    import socket

    def mock_getaddrinfo(host, port, **kwargs):
        if host == "public.example.com":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port))]

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    def handler(request):
        if str(request.url) == "https://public.example.com/safe":
            return httpx.Response(302, headers={"location": "http://127.0.0.1:8080/admin"})
        return httpx.Response(200, headers={"content-type": "text/html"}, text=HTML_WITH_OG_TAGS)

    metadata = fetch_metadata("https://public.example.com/safe", client=_client_for(handler))
    assert metadata.title is None


def test_ssrf_follows_safe_redirect(monkeypatch):
    import socket

    def mock_getaddrinfo(host, port, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    def handler(request):
        if str(request.url) == "https://example.com/old":
            return httpx.Response(301, headers={"location": "/new"})
        if str(request.url) == "https://example.com/new":
            return httpx.Response(200, headers={"content-type": "text/html"}, text=HTML_WITH_OG_TAGS)
        return httpx.Response(404)

    metadata = fetch_metadata("https://example.com/old", client=_client_for(handler))
    assert metadata.title == "Real Title"


def test_ssrf_blocks_too_many_redirects(monkeypatch):
    import socket

    def mock_getaddrinfo(host, port, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    redirect_count = 0

    def handler(request):
        nonlocal redirect_count
        redirect_count += 1
        return httpx.Response(302, headers={"location": f"https://example.com/redirect_{redirect_count}"})

    metadata = fetch_metadata("https://example.com/redirect_0", client=_client_for(handler))
    assert metadata.title is None
    assert redirect_count == 4  # 1 initial + 3 redirects max allowed, 4th triggers limit

