from __future__ import annotations

import datetime as dt
import logging

from sqlalchemy.orm import Session as OrmSession

from app.config import settings
from app.domain.bookmark import Bookmark, BookmarkStatus
from app.domain.user import User
from app.integrations import mailer
from app.time_utils import utcnow
from app.web.templating import templates

logger = logging.getLogger(__name__)


def get_unsent_digest_bookmarks(db: OrmSession, user_id: int) -> list[Bookmark]:
    """Retrieve bookmarks that have not yet been included in any digest."""
    return (
        db.query(Bookmark)
        .filter(Bookmark.user_id == user_id, Bookmark.digest_sent_at.is_(None))
        .order_by(Bookmark.created_at.desc())
        .all()
    )


def send_daily_digest_for_user(
    db: OrmSession,
    user: User,
    now: dt.datetime | None = None,
) -> int:
    """Send daily digest email for a single user. Returns number of bookmarks included, or 0 if none."""
    unsent_bookmarks = get_unsent_digest_bookmarks(db, user.id)
    if not unsent_bookmarks:
        logger.debug("Zero new bookmarks for user %s (%s); skipping digest email.", user.id, user.email)
        return 0

    pending_count = (
        db.query(Bookmark)
        .filter(Bookmark.user_id == user.id, Bookmark.status == BookmarkStatus.DA_ORGANIZZARE)
        .count()
    )

    send_time = now or utcnow()
    date_str = send_time.strftime("%d/%m/%Y")
    base_url = settings.base_url.rstrip("/")

    context = {
        "bookmarks": unsent_bookmarks,
        "date_str": date_str,
        "base_url": base_url,
        "pending_count": pending_count,
        "user": user,
    }

    try:
        html_content = templates.get_template("emails/daily_digest.html").render(context)
        text_content = templates.get_template("emails/daily_digest.txt").render(context)
    except Exception:
        logger.exception("Failed to render daily digest email template for user %s", user.email)
        return 0

    subject = f"Cozy Bookmarks — {len(unsent_bookmarks)} {'nuovo segnalibro' if len(unsent_bookmarks) == 1 else 'nuovi segnalibri'}"
    delivered = mailer.send_email(
        to_email=user.email,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
    )

    if delivered:
        for b in unsent_bookmarks:
            b.digest_sent_at = send_time
        db.commit()
        logger.info(
            "Successfully sent daily digest with %d bookmarks to %s",
            len(unsent_bookmarks),
            user.email,
        )
        return len(unsent_bookmarks)
    else:
        logger.warning("Daily digest email delivery failed for user %s; skipping DB update", user.email)
        return 0


def send_daily_digest_all(db: OrmSession) -> dict[int, int]:
    """Execute the daily digest process for all registered users."""
    users = db.query(User).all()
    results = {}
    for u in users:
        count = send_daily_digest_for_user(db, u)
        results[u.id] = count
    return results


def get_test_digest_bookmarks(
    db: OrmSession,
    user_id: int,
    now: dt.datetime | None = None,
) -> list[Bookmark]:
    """Retrieve bookmarks from yesterday, or fallback to the latest 10 bookmarks."""
    current_time = now or utcnow()
    yesterday = (current_time - dt.timedelta(days=1)).date()
    yesterday_start = dt.datetime.combine(yesterday, dt.time.min)
    yesterday_end = dt.datetime.combine(yesterday, dt.time.max)

    yesterday_bookmarks = (
        db.query(Bookmark)
        .filter(
            Bookmark.user_id == user_id,
            Bookmark.created_at >= yesterday_start,
            Bookmark.created_at <= yesterday_end,
        )
        .order_by(Bookmark.created_at.desc())
        .all()
    )
    if yesterday_bookmarks:
        return yesterday_bookmarks

    return (
        db.query(Bookmark)
        .filter(Bookmark.user_id == user_id)
        .order_by(Bookmark.created_at.desc())
        .limit(10)
        .all()
    )


def send_test_daily_digest(
    db: OrmSession,
    user: User,
    now: dt.datetime | None = None,
) -> tuple[int, str | None]:
    """Send a test digest email to the user with yesterday's bookmarks or the latest 10 bookmarks."""
    bookmarks = get_test_digest_bookmarks(db, user.id, now=now)
    if not bookmarks:
        return 0, "Nessun bookmark presente nel tuo account."

    pending_count = (
        db.query(Bookmark)
        .filter(Bookmark.user_id == user.id, Bookmark.status == BookmarkStatus.DA_ORGANIZZARE)
        .count()
    )

    send_time = now or utcnow()
    date_str = send_time.strftime("%d/%m/%Y")
    base_url = settings.base_url.rstrip("/")

    context = {
        "bookmarks": bookmarks,
        "date_str": f"{date_str} (Test)",
        "base_url": base_url,
        "pending_count": pending_count,
        "user": user,
    }

    try:
        html_content = templates.get_template("emails/daily_digest.html").render(context)
        text_content = templates.get_template("emails/daily_digest.txt").render(context)
    except Exception as exc:
        logger.exception("Failed to render test daily digest email template for user %s", user.email)
        return 0, f"Errore nel rendering del template: {exc}"

    subject = f"[Test] Cozy Bookmarks — Riassunto di prova ({len(bookmarks)} segnalibri)"
    delivered = mailer.send_email(
        to_email=user.email,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
    )

    if delivered:
        logger.info("Successfully sent test daily digest with %d bookmarks to %s", len(bookmarks), user.email)
        return len(bookmarks), None
    else:
        logger.warning("Test daily digest email delivery failed for user %s", user.email)
        return 0, "Errore durante l'invio dell'email via server SMTP."

