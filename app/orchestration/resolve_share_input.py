import re

from app.validation import ValidationError, validate_url

URL_PATTERN = re.compile(r"https?://\S+")


def resolve_shared_url(url: str | None, text: str | None) -> str | None:
    if url and url.strip():
        try:
            return validate_url(url)
        except ValidationError:
            pass
    if text:
        match = URL_PATTERN.search(text)
        if match:
            try:
                return validate_url(match.group(0))
            except ValidationError:
                pass
    return None
