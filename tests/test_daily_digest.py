import datetime as dt

from app.domain import bookmark as bookmark_domain
from app.domain.user import User, hash_password
from app.integrations import mailer
from app.orchestration.daily_digest import (
    get_unsent_digest_bookmarks,
    send_daily_digest_all,
    send_daily_digest_for_user,
)
from app.scripts import send_daily_digest


def test_zero_spam_rule_when_no_new_bookmarks(db_session, user, monkeypatch):
    sent_emails = []
    monkeypatch.setattr(
        mailer,
        "send_email",
        lambda to_email, subject, html_content, text_content=None: sent_emails.append(
            {"to": to_email, "subject": subject, "html": html_content}
        ) or True,
    )

    count = send_daily_digest_for_user(db_session, user)

    assert count == 0
    assert len(sent_emails) == 0


def test_daily_digest_sends_email_and_marks_bookmarks(db_session, user, monkeypatch):
    sent_emails = []
    monkeypatch.setattr(
        mailer,
        "send_email",
        lambda to_email, subject, html_content, text_content=None: sent_emails.append(
            {"to": to_email, "subject": subject, "html": html_content, "text": text_content}
        ) or True,
    )

    b1 = bookmark_domain.create_bookmark(
        db_session,
        user_id=user.id,
        url="https://news.example.com/item1",
        title="Breaking Tech News",
        description="A great article about Python",
        tag_names=["tech"],
    )
    b2 = bookmark_domain.create_bookmark(
        db_session,
        user_id=user.id,
        url="https://tiktok.com/@creator/video/123",
        title="Cool TikTok Recipe",
        note="Pasta alla carbonara",
        tag_names=["cucina"],
    )

    count = send_daily_digest_for_user(db_session, user)

    assert count == 2
    assert len(sent_emails) == 1
    email = sent_emails[0]
    assert email["to"] == user.email
    assert "2 nuovi segnalibri" in email["subject"]
    assert "Breaking Tech News" in email["html"]
    assert "Cool TikTok Recipe" in email["html"]
    assert f"/bookmarks/{b1.id}/organize" in email["html"]
    assert f"/bookmarks/{b2.id}/organize" in email["html"]

    db_session.refresh(b1)
    db_session.refresh(b2)
    assert b1.digest_sent_at is not None
    assert b2.digest_sent_at is not None

    # Next invocation must return 0 (no spam, no duplicates)
    count_second = send_daily_digest_for_user(db_session, user)
    assert count_second == 0
    assert len(sent_emails) == 1


def test_daily_digest_all_users(db_session, user, monkeypatch):
    other = User(email="second@example.com", password_hash=hash_password("pwd"))
    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)

    bookmark_domain.create_bookmark(db_session, user_id=user.id, url="https://a.com")
    bookmark_domain.create_bookmark(db_session, user_id=other.id, url="https://b.com")

    monkeypatch.setattr(mailer, "send_email", lambda *args, **kwargs: True)

    results = send_daily_digest_all(db_session)
    assert results[user.id] == 1
    assert results[other.id] == 1


def test_send_daily_digest_cli(db_session, user, monkeypatch, capsys):
    bookmark_domain.create_bookmark(db_session, user_id=user.id, url="https://cli-test.com")
    monkeypatch.setattr("sys.argv", ["send_daily_digest.py"])
    monkeypatch.setattr(send_daily_digest, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(mailer, "send_email", lambda *args, **kwargs: True)

    send_daily_digest.main()

    captured = capsys.readouterr()
    assert "Daily digest completed" in captured.out
    assert "delivered 1 bookmarks" in captured.out

