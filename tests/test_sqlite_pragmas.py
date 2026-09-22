import sqlite3
from pathlib import Path
import tempfile

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.db import Base, SessionLocal, engine
from app.domain.bookmark import Bookmark
from app.domain.user import User, hash_password


def test_sqlite_pragmas_on_db_engine():
    """Verify engine event listener enables foreign_keys."""
    from app.db import set_sqlite_pragma

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_engine.db"
        test_engine = create_engine(f"sqlite:///{db_path}")
        event.listen(test_engine, "connect", set_sqlite_pragma)

        with test_engine.connect() as conn:
            fk_result = conn.execute(text("PRAGMA foreign_keys")).scalar()
            assert fk_result == 1



def test_sqlite_foreign_key_violation_raises_error():
    """Verify inserting a record referencing a non-existent parent raises IntegrityError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_fk.db"
        test_engine = create_engine(f"sqlite:///{db_path}")

        @event.listens_for(test_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

        Base.metadata.create_all(test_engine)
        test_session_local = sessionmaker(bind=test_engine)
        session = test_session_local()

        # Non-existent user_id 99999
        invalid_bookmark = Bookmark(
            user_id=99999,
            url="https://example.com",
            position=1000.0,
        )
        session.add(invalid_bookmark)

        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()
        session.close()


def test_sqlite_wal_mode_on_file_db():
    """Verify WAL mode is enabled on file-based SQLite databases."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_wal.db"
        test_engine = create_engine(f"sqlite:///{db_path}")

        @event.listens_for(test_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

        with test_engine.connect() as conn:
            mode = conn.execute(text("PRAGMA journal_mode")).scalar()
            assert str(mode).lower() == "wal"
