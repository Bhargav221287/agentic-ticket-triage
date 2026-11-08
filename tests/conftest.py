"""Test configuration and fixtures with SQLite in-memory DB and mocked LLM."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

import app.db as db_module
from app.db import Base, get_db
from app.main import app
from app.llm import MockLLMClient, set_llm_client

# In-memory SQLite database for test isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Ensure all components use the in-memory database during tests."""
    monkeypatch.setattr(db_module, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(db_module, "engine", engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Yield a database session connected to the test database."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def mock_llm():
    """Provide a fresh MockLLMClient and register it globally."""
    client = MockLLMClient()
    set_llm_client(client)
    yield client
    set_llm_client(MockLLMClient())


@pytest.fixture
def client(db_session):
    """Provide a FastAPI TestClient with database session overridden."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
