import httpx

from app.integrations.tiktok_oembed import fetch_tiktok_caption


def _client_for(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_returns_caption_from_title_field():
    def handler(request):
        assert request.url.path == "/oembed"
        return httpx.Response(200, json={"title": "Something big just landed on TikTok."})

    caption = fetch_tiktok_caption("https://www.tiktok.com/@nasa/video/123", client=_client_for(handler))

    assert caption == "Something big just landed on TikTok."


def test_returns_none_on_missing_title():
    def handler(request):
        return httpx.Response(200, json={"author_name": "NASA"})

    caption = fetch_tiktok_caption("https://www.tiktok.com/@nasa/video/123", client=_client_for(handler))

    assert caption is None


def test_returns_none_on_http_error():
    def handler(request):
        return httpx.Response(404, text="not found")

    caption = fetch_tiktok_caption("https://www.tiktok.com/@nasa/video/999", client=_client_for(handler))

    assert caption is None


def test_returns_none_on_invalid_json():
    def handler(request):
        return httpx.Response(200, text="not json")

    caption = fetch_tiktok_caption("https://www.tiktok.com/@nasa/video/123", client=_client_for(handler))

    assert caption is None


def test_returns_none_on_timeout():
    def handler(request):
        raise httpx.TimeoutException("timed out", request=request)

    caption = fetch_tiktok_caption("https://www.tiktok.com/@nasa/video/123", client=_client_for(handler))

    assert caption is None
