import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.domain  # noqa: F401 registers all models on Base.metadata
from app.db import Base, get_db
from app.domain.user import User, hash_password
from app.integrations.metadata_extractor import PageMetadata
from app.main import app as fastapi_app
from app.orchestration import save_bookmark


@pytest.fixture(autouse=True)
def _no_real_network_metadata_fetch(monkeypatch):
    # keeps tests hermetic; individual tests override this via their own monkeypatch
    monkeypatch.setattr(save_bookmark, "fetch_metadata", lambda url: PageMetadata())


@pytest.fixture(autouse=True)
def _no_real_network_ai_suggestion(monkeypatch):
    # keeps tests hermetic; individual tests override this via their own monkeypatch
    monkeypatch.setattr(save_bookmark, "suggest_tags_safely", lambda *args, **kwargs: [])


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def user(db_session):
    test_user = User(email="test@example.com", password_hash=hash_password("secret123"))
    db_session.add(test_user)
    db_session.commit()
    db_session.refresh(test_user)
    return test_user


@pytest.fixture()
def authed_client(client, user):
    response = client.post("/auth/login", json={"email": user.email, "password": "secret123"})
    assert response.status_code == 200
    return client
