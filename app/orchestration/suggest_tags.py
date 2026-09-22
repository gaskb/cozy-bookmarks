from __future__ import annotations

import logging

from app.integrations.ai_provider import AIProvider, AIProviderError, ChatMessage

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Suggerisci da 1 a 5 tag brevi (una o due parole, in italiano o inglese come piu' naturale) "
    "per organizzare questo bookmark. Rispondi SOLO con i tag separati da virgola, "
    "senza spiegazioni, senza numerazione, senza markdown."
)

MAX_TAG_LENGTH = 30
MAX_TAGS = 5


def suggest_tags(
    provider: AIProvider,
    url: str,
    title: str | None,
    description: str | None,
    existing_tags: list[str] | None = None,
) -> list[str]:
    system_prompt = SYSTEM_PROMPT
    if existing_tags:
        cleaned_tags = [t.strip() for t in existing_tags if t.strip()]
        if cleaned_tags:
            system_prompt += (
                f" Tag già usati dall'utente: {', '.join(cleaned_tags)}. "
                "Se pertinenti, preferisci riutilizzare questi tag; altrimenti suggeriscine di nuovi."
            )
    user_content = (
        f"URL: {url}\nTitolo: {title or '(nessuno)'}\nDescrizione: {description or '(nessuna)'}"
    )
    messages = [
        ChatMessage(role="system", content=system_prompt),
        ChatMessage(role="user", content=user_content),
    ]
    reply = provider.complete(messages)
    return _parse_tags(reply)


def _parse_tags(reply: str) -> list[str]:
    candidates = reply.replace("\n", ",").split(",")
    tags = []
    for candidate in candidates:
        cleaned = candidate.strip().strip("-*#").strip().lower()
        if cleaned and len(cleaned) <= MAX_TAG_LENGTH:
            tags.append(cleaned)
    return tags[:MAX_TAGS]


def suggest_tags_safely(
    provider: AIProvider,
    url: str,
    title: str | None,
    description: str | None,
    existing_tags: list[str] | None = None,
) -> list[str]:
    try:
        return suggest_tags(provider, url, title, description, existing_tags=existing_tags)
    except AIProviderError as exc:
        logger.warning("AI tag suggestion failed for %s: %s", url, exc)
        return []
    except Exception:
        logger.exception("unexpected error suggesting tags for %s", url)
        return []

