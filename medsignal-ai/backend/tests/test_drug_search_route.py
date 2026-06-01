from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.services import rxnorm_service
from app.services.rxnorm_service import (
    RxNormNotFoundError,
    RxNormTimeoutError,
    RxNormUpstreamError,
)
from app.models.drug import Drug


engine = create_engine(
    "sqlite+pysqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db


def teardown_function():
    app.dependency_overrides.clear()


def test_search_drugs_returns_result(monkeypatch):
    def fake_search_and_save_drug(query, db):
        drug = Drug(
            id=1,
            rxcui="202433",
            input_name=query.strip(),
            normalized_name="Tylenol",
            synonym="acetaminophen",
            tty="BN",
        )
        return drug

    monkeypatch.setattr(
        rxnorm_service, "search_and_save_drug", fake_search_and_save_drug
    )
    client = TestClient(app)

    response = client.get("/api/drugs/search", params={"query": "Tylenol"})

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "rxcui": "202433",
        "input_name": "Tylenol",
        "normalized_name": "Tylenol",
        "synonym": "acetaminophen",
        "tty": "BN",
    }


def test_search_drugs_rejects_empty_query():
    client = TestClient(app)

    response = client.get("/api/drugs/search", params={"query": "   "})

    assert response.status_code == 422


def test_search_drugs_returns_404(monkeypatch):
    def raise_not_found(query, db):
        raise RxNormNotFoundError()

    monkeypatch.setattr(rxnorm_service, "search_and_save_drug", raise_not_found)
    client = TestClient(app)

    response = client.get("/api/drugs/search", params={"query": "unknown"})

    assert response.status_code == 404


def test_search_drugs_returns_502(monkeypatch):
    def raise_upstream(query, db):
        raise RxNormUpstreamError()

    monkeypatch.setattr(rxnorm_service, "search_and_save_drug", raise_upstream)
    client = TestClient(app)

    response = client.get("/api/drugs/search", params={"query": "Tylenol"})

    assert response.status_code == 502


def test_search_drugs_returns_504(monkeypatch):
    def raise_timeout(query, db):
        raise RxNormTimeoutError()

    monkeypatch.setattr(rxnorm_service, "search_and_save_drug", raise_timeout)
    client = TestClient(app)

    response = client.get("/api/drugs/search", params={"query": "Tylenol"})

    assert response.status_code == 504
