from __future__ import annotations

from urllib.parse import urlsplit

MAX_URL_LENGTH = 2048
MAX_TITLE_LENGTH = 500
MAX_NOTE_LENGTH = 10_000
MAX_TAG_LENGTH = 50
MAX_TOKEN_NAME_LENGTH = 100


class ValidationError(ValueError):
    pass


def validate_url(url: str | None) -> str:
    if not url or not isinstance(url, str) or not url.strip():
        raise ValidationError("Inserisci un URL")

    cleaned = url.strip()
    if len(cleaned) > MAX_URL_LENGTH:
        raise ValidationError(f"URL troppo lungo (massimo {MAX_URL_LENGTH} caratteri)")

    try:
        parsed = urlsplit(cleaned)
    except Exception as exc:
        raise ValidationError(f"Sintassi URL non valida: {exc}") from exc

    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        raise ValidationError("L'URL deve iniziare con http:// o https://")

    if not parsed.netloc or not parsed.hostname:
        raise ValidationError("L'URL deve contenere un nome host valido")

    return cleaned


def validate_title(title: str | None) -> str | None:
    if not title:
        return None
    cleaned = title.strip()
    if len(cleaned) > MAX_TITLE_LENGTH:
        raise ValidationError(f"Il titolo supera la lunghezza massima ({MAX_TITLE_LENGTH} caratteri)")
    return cleaned or None


def validate_note(note: str | None) -> str | None:
    if not note:
        return None
    cleaned = note.strip()
    if len(cleaned) > MAX_NOTE_LENGTH:
        raise ValidationError(f"La nota supera la lunghezza massima ({MAX_NOTE_LENGTH} caratteri)")
    return cleaned or None


def validate_tag_name(name: str | None) -> str:
    if not name or not name.strip():
        raise ValidationError("Il nome del tag non può essere vuoto")
    cleaned = name.strip().lower()
    if len(cleaned) > MAX_TAG_LENGTH:
        raise ValidationError(f"Il tag '{cleaned}' supera la lunghezza massima ({MAX_TAG_LENGTH} caratteri)")
    return cleaned


def validate_token_name(name: str | None) -> str:
    if not name or not name.strip():
        raise ValidationError("Il nome del token non può essere vuoto")
    cleaned = name.strip()
    if len(cleaned) > MAX_TOKEN_NAME_LENGTH:
        raise ValidationError(f"Il nome del token supera la lunghezza massima ({MAX_TOKEN_NAME_LENGTH} caratteri)")
    return cleaned
