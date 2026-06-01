from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.drug import Drug
from app.models.drug_label import DrugLabel
from app.services import openfda_label_service
from app.services.openfda_label_service import (
    OpenFDALabelTimeoutError,
    OpenFDALabelUpstreamError,
)


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


def create_drug() -> int:
    db = TestingSessionLocal()
    drug = Drug(
        rxcui="202433",
        input_name="Tylenol",
        normalized_name="Tylenol",
        synonym="acetaminophen",
        tty="BN",
    )
    db.add(drug)
    db.commit()
    drug_id = drug.id
    db.close()
    return drug_id


def test_get_drug_identity():
    drug_id = create_drug()
    client = TestClient(app)

    response = client.get(f"/api/drugs/{drug_id}")

    assert response.status_code == 200
    assert response.json()["normalized_name"] == "Tylenol"


def test_get_drug_label(monkeypatch):
    drug_id = create_drug()

    def fake_fetch(normalized_drug_name, drug_id, db):
        label = DrugLabel(
            drug_id=drug_id,
            set_id="label-set-id",
            brand_name=["Tylenol"],
            generic_name=["Acetaminophen"],
            warnings=["Liver warning"],
            adverse_reactions=None,
            contraindications=None,
            indications_and_usage=["Pain relief"],
            boxed_warning=None,
            raw_label_json={"set_id": "label-set-id"},
        )
        db.add(label)
        db.commit()
        db.refresh(label)
        return label

    monkeypatch.setattr(openfda_label_service, "fetch_and_save_drug_label", fake_fetch)
    client = TestClient(app)

    response = client.get(f"/api/drugs/{drug_id}/label")

    assert response.status_code == 200
    assert response.json()["set_id"] == "label-set-id"
    assert response.json()["warnings"] == ["Liver warning"]
    assert response.json()["adverse_reactions"] is None


def test_get_drug_label_empty_result(monkeypatch):
    drug_id = create_drug()
    monkeypatch.setattr(
        openfda_label_service,
        "fetch_and_save_drug_label",
        lambda normalized_drug_name, drug_id, db: None,
    )
    client = TestClient(app)

    response = client.get(f"/api/drugs/{drug_id}/label")

    assert response.status_code == 200
    assert response.json() is None


def test_get_drug_label_openfda_failure(monkeypatch):
    drug_id = create_drug()

    def raise_upstream(normalized_drug_name, drug_id, db):
        raise OpenFDALabelUpstreamError()

    monkeypatch.setattr(openfda_label_service, "fetch_and_save_drug_label", raise_upstream)
    client = TestClient(app)

    response = client.get(f"/api/drugs/{drug_id}/label")

    assert response.status_code == 502


def test_get_drug_label_openfda_timeout(monkeypatch):
    drug_id = create_drug()

    def raise_timeout(normalized_drug_name, drug_id, db):
        raise OpenFDALabelTimeoutError()

    monkeypatch.setattr(openfda_label_service, "fetch_and_save_drug_label", raise_timeout)
    client = TestClient(app)

    response = client.get(f"/api/drugs/{drug_id}/label")

    assert response.status_code == 504
