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


def test_send_test_daily_digest_yesterday_fallback_to_latest(db_session, user, monkeypatch):
    sent = []
    monkeypatch.setattr(
        mailer,
        "send_email",
        lambda to_email, subject, html_content, text_content=None: sent.append((to_email, subject, html_content)) or True,
    )

    for i in range(12):
        bookmark_domain.create_bookmark(db_session, user_id=user.id, url=f"https://example.com/{i}", title=f"Bookmark {i}")

    from app.orchestration import daily_digest
    count, err = daily_digest.send_test_daily_digest(db_session, user)
    assert count == 10
    assert err is None
    assert len(sent) == 1
    assert "[Test]" in sent[0][1]

    unsent = daily_digest.get_unsent_digest_bookmarks(db_session, user.id)
    assert len(unsent) == 12


def test_send_test_daily_digest_yesterday_match(db_session, user, monkeypatch):
    sent = []
    monkeypatch.setattr(
        mailer,
        "send_email",
        lambda to_email, subject, html_content, text_content=None: sent.append((to_email, subject, html_content)) or True,
    )

    now = dt.datetime(2026, 9, 22, 10, 0, 0)
    yesterday_time = dt.datetime(2026, 9, 21, 14, 0, 0)

    b_yesterday = bookmark_domain.create_bookmark(db_session, user_id=user.id, url="https://yesterday.com", title="Yesterday Item")
    b_yesterday.created_at = yesterday_time
    db_session.commit()

    b_today = bookmark_domain.create_bookmark(db_session, user_id=user.id, url="https://today.com", title="Today Item")
    b_today.created_at = now
    db_session.commit()

    from app.orchestration import daily_digest
    count, err = daily_digest.send_test_daily_digest(db_session, user, now=now)
    assert count == 1
    assert err is None
    assert "Yesterday Item" in sent[0][2]
    assert "Today Item" not in sent[0][2]


def test_web_send_test_digest_route(authed_client, user, monkeypatch):
    monkeypatch.setattr(mailer, "send_email", lambda *args, **kwargs: True)

    authed_client.post("/bookmarks", json={"url": "https://test-menu-send.com"})

    resp = authed_client.post("/digest/send-test", follow_redirects=True)
    assert resp.status_code == 200
    assert "Email di prova inviata con successo" in resp.text


