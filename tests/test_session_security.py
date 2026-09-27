import datetime as dt
import hashlib

from app.config import settings
from app.domain.session import Session, create_session, delete_session, get_valid_session
from app.time_utils import utcnow


def test_session_token_is_hashed_in_database(db_session, user):
    session = create_session(db_session, user.id)
    raw_token = session.token

    assert raw_token is not None
    assert len(raw_token) > 20

    # Read row directly from database to verify only SHA-256 hash is stored
    expected_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    db_row = db_session.query(Session).filter(Session.token_hash == expected_hash).first()

    assert db_row is not None
    assert db_row.token_hash == expected_hash
    assert db_row.token_hash != raw_token
    assert db_row.user_id == user.id


def test_get_valid_session_authenticates_with_raw_token(db_session, user):
    session = create_session(db_session, user.id)
    raw_token = session.token

    valid_session = get_valid_session(db_session, raw_token)
    assert valid_session is not None
    assert valid_session.user_id == user.id

    # Wrong token fails
    assert get_valid_session(db_session, "invalid_raw_token") is None
    assert get_valid_session(db_session, "") is None


def test_expired_session_is_purged_on_lookup(db_session, user):
    session = create_session(db_session, user.id)
    raw_token = session.token

    # Make session expired
    session.expires_at = utcnow() - dt.timedelta(hours=1)
    db_session.commit()

    assert get_valid_session(db_session, raw_token) is None

    # Verify deleted from DB
    expected_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    assert db_session.get(Session, expected_hash) is None


def test_delete_session_removes_session_by_token(db_session, user):
    session = create_session(db_session, user.id)
    raw_token = session.token

    delete_session(db_session, raw_token)
    assert get_valid_session(db_session, raw_token) is None


def test_session_cookie_secure_respects_settings(client, user, monkeypatch):
    # When session_cookie_secure is True
    monkeypatch.setattr(settings, "session_cookie_secure", True)
    resp_true = client.post(
        "/login", data={"email": user.email, "password": "secret123"}, follow_redirects=False
    )
    cookie_header_true = resp_true.headers.get("set-cookie", "")
    assert "secure" in cookie_header_true.lower()

    # When session_cookie_secure is False
    monkeypatch.setattr(settings, "session_cookie_secure", False)
    resp_false = client.post(
        "/login", data={"email": user.email, "password": "secret123"}, follow_redirects=False
    )
    cookie_header_false = resp_false.headers.get("set-cookie", "")
    assert "secure" not in cookie_header_false.lower()
