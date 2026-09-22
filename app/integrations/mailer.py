from __future__ import annotations

from email.message import EmailMessage
import logging
import smtplib

from app.config import settings

logger = logging.getLogger(__name__)


def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str | None = None,
) -> bool:
    """Send an email using standard SMTP. If smtp_enabled is False, log and return True."""
    if not settings.smtp_enabled:
        logger.info(
            "SMTP disabled; skipping actual email delivery to %s with subject: %s",
            to_email,
            subject,
        )
        return True

    if not settings.smtp_host:
        logger.warning("SMTP enabled but SMTP_HOST is empty; cannot send email to %s", to_email)
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to_email

    fallback_text = text_content or "Visualizza questo messaggio in un client email compatibile con HTML."
    msg.set_content(fallback_text)
    msg.add_alternative(html_content, subtype="html")

    try:
        if settings.smtp_ssl:
            smtp_cls = smtplib.SMTP_SSL
        else:
            smtp_cls = smtplib.SMTP

        with smtp_cls(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            if not settings.smtp_ssl and settings.smtp_tls:
                server.starttls()
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)

        logger.info("Successfully sent email to %s (subject: %s)", to_email, subject)
        return True
    except Exception:
        logger.exception("Failed to send email to %s via %s:%s", to_email, settings.smtp_host, settings.smtp_port)
        return False
