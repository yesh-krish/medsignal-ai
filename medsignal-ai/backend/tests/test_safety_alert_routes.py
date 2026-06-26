from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.drug import Drug
from app.models.safety_alert import SafetyAlert


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


def create_drug_with_alert() -> int:
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
    db.refresh(drug)

    db.add(
        SafetyAlert(
            drug_id=drug.id,
            alert_type="potential_safety_signal",
            reaction="Nausea",
            baseline_count=1,
            current_count=4,
            percent_change=300.0,
            message=(
                "Potential safety signal: reports mentioning this medication and "
                "Nausea increased. This is a reporting signal for review, not a "
                "confirmed drug risk."
            ),
        )
    )
    db.commit()
    drug_id = drug.id
    db.close()
    return drug_id


def test_get_drug_safety_alerts():
    drug_id = create_drug_with_alert()
    client = TestClient(app)

    response = client.get(f"/api/drugs/{drug_id}/alerts")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["alert_type"] == "potential_safety_signal"
    assert body[0]["reaction"] == "Nausea"
    assert body[0]["baseline_count"] == 1
    assert body[0]["current_count"] == 4
    assert "not a confirmed drug risk" in body[0]["message"]


def test_get_drug_safety_alerts_drug_not_found():
    client = TestClient(app)

    response = client.get("/api/drugs/999/alerts")

    assert response.status_code == 404
