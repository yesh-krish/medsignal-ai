from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
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


def create_drug(name: str = "Tylenol") -> int:
    db = TestingSessionLocal()
    drug = Drug(
        rxcui="202433",
        input_name=name,
        normalized_name=name,
        synonym="acetaminophen",
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
