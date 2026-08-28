import re

URL_PATTERN = re.compile(r"https?://\S+")


def resolve_shared_url(url: str | None, text: str | None) -> str | None:
    if url and url.strip():
        return url.strip()
    if text:
        match = URL_PATTERN.search(text)
        if match:
            return match.group(0)
    return None
