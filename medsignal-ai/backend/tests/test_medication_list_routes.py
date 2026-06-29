from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.drug import Drug
from app.services import interaction_service


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


def create_drug(
    name: str = "Tylenol",
    rxcui: str = "202433",
    synonym: str = "acetaminophen",
) -> int:
    db = TestingSessionLocal()
    drug = Drug(
        rxcui=rxcui,
        input_name=name,
        normalized_name=name,
        synonym=synonym,
        tty="BN",
    )
    db.add(drug)
    db.commit()
    drug_id = drug.id
    db.close()
    return drug_id


def test_get_default_medication_list_creates_empty_list():
    client = TestClient(app)

    response = client.get("/api/medication-lists/default")

    assert response.status_code == 200
    assert response.json()["name"] == "My medications"
    assert response.json()["items"] == []


def test_add_and_remove_medication_list_item():
    drug_id = create_drug()
    client = TestClient(app)

    add_response = client.post(
        "/api/medication-lists/default/items",
        json={"drug_id": drug_id},
    )

    assert add_response.status_code == 201
    items = add_response.json()["items"]
    assert len(items) == 1
    assert items[0]["drug"]["normalized_name"] == "Tylenol"

    remove_response = client.delete(
        f"/api/medication-lists/default/items/{items[0]['id']}"
    )

    assert remove_response.status_code == 200
    assert remove_response.json()["items"] == []


def test_add_medication_list_item_is_idempotent_for_same_drug():
    drug_id = create_drug()
    client = TestClient(app)

    first_response = client.post(
        "/api/medication-lists/default/items",
        json={"drug_id": drug_id},
    )
    second_response = client.post(
        "/api/medication-lists/default/items",
        json={"drug_id": drug_id},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert len(second_response.json()["items"]) == 1


def test_add_medication_list_item_rejects_unknown_drug():
    client = TestClient(app)

    response = client.post(
        "/api/medication-lists/default/items",
        json={"drug_id": 999},
    )

    assert response.status_code == 404


def test_screen_default_medication_list_interactions(monkeypatch):
    drug_id = create_drug()
    client = TestClient(app)
    client.post("/api/medication-lists/default/items", json={"drug_id": drug_id})

    def fake_screen(medication_list):
        return {
            "medication_list_id": medication_list.id,
            "checked_rxcuis": ["202433"],
            "interactions": [],
            "disclaimer": "Ask a doctor or pharmacist.",
        }

    monkeypatch.setattr(
        interaction_service, "screen_medication_list_interactions", fake_screen
    )

    response = client.get("/api/medication-lists/default/interactions")

    assert response.status_code == 200
    assert response.json()["checked_rxcuis"] == ["202433"]
    assert "pharmacist" in response.json()["disclaimer"]


def test_get_default_medication_risk_profile_creates_empty_profile():
    client = TestClient(app)

    response = client.get("/api/medication-lists/default/risk-profile")

    assert response.status_code == 200
    body = response.json()
    assert body["medication_list_id"] == 1
    assert len(body["factors"]) == 12
    assert body["factors_to_discuss"] == []
    assert "does not diagnose" in body["disclaimer"]


def test_save_and_load_default_medication_risk_profile():
    create_drug(name="ibuprofen", synonym="nonsteroidal anti-inflammatory")
    client = TestClient(app)
    search_response = client.get("/api/medication-lists/default")
    assert search_response.status_code == 200

    response = client.put(
        "/api/medication-lists/default/risk-profile",
        json={
            "factors": [
                {"factor_key": "kidney_disease", "is_present": True},
                {
                    "factor_key": "allergies",
                    "is_present": False,
                    "note": "Penicillin",
                },
                {"factor_key": "unknown_factor", "is_present": True},
            ]
        },
    )

    assert response.status_code == 200
    body = response.json()
    saved_factors = {factor["factor_key"]: factor for factor in body["factors"]}
    assert saved_factors["kidney_disease"]["is_present"] is True
    assert saved_factors["allergies"]["note"] == "Penicillin"
    assert "unknown_factor" not in saved_factors

    loaded_response = client.get("/api/medication-lists/default/risk-profile")

    assert loaded_response.status_code == 200
    loaded_factors = {
        factor["factor_key"]: factor for factor in loaded_response.json()["factors"]
    }
    assert loaded_factors["kidney_disease"]["is_present"] is True
    assert loaded_factors["allergies"]["note"] == "Penicillin"
