from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.drug import Drug
from app.services import drug_comparison_service
from app.services import openfda_event_service


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


def create_drug(name: str) -> int:
    db = TestingSessionLocal()
    drug = Drug(
        rxcui=name,
        input_name=name,
        normalized_name=name,
        synonym=None,
        tty="IN",
    )
    db.add(drug)
    db.commit()
    drug_id = drug.id
    db.close()
    return drug_id


def test_compare_drugs_route(monkeypatch):
    left_id = create_drug("Acetaminophen")
    right_id = create_drug("Ibuprofen")

    def fake_comparison(left_drug, right_drug, db):
        return {
            "left": {
                "drug": left_drug,
                "trends": {
                    "top_reported_reactions": [{"reaction": "Nausea", "count": 2}],
                    "reports_by_year": {"2024": 2},
                    "seriousness_breakdown": {"serious": 1, "not_serious": 1},
                    "sex_breakdown": {"unknown": 2},
                    "total_reports": 2,
                },
                "label": None,
            },
            "right": {
                "drug": right_drug,
                "trends": {
                    "top_reported_reactions": [{"reaction": "Nausea", "count": 1}],
                    "reports_by_year": {"2024": 1},
                    "seriousness_breakdown": {"not_serious": 1},
                    "sex_breakdown": {"unknown": 1},
                    "total_reports": 1,
                },
                "label": None,
            },
            "shared_top_reported_reactions": [
                {
                    "reaction": "Nausea",
                    "left_count": 2,
                    "right_count": 1,
                    "absolute_difference": 1,
                }
            ],
            "label_section_comparison": [],
            "disclaimer": "Report counts cannot establish which medication is safer.",
        }

    monkeypatch.setattr(
        drug_comparison_service, "build_drug_comparison", fake_comparison
    )
    client = TestClient(app)

    response = client.get(f"/api/drugs/compare?left_id={left_id}&right_id={right_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["left"]["drug"]["normalized_name"] == "Acetaminophen"
    assert body["right"]["drug"]["normalized_name"] == "Ibuprofen"
    assert body["shared_top_reported_reactions"][0]["reaction"] == "Nausea"


def test_compare_drugs_rejects_same_drug():
    drug_id = create_drug("Acetaminophen")
    client = TestClient(app)

    response = client.get(f"/api/drugs/compare?left_id={drug_id}&right_id={drug_id}")

    assert response.status_code == 422


def test_compare_drugs_handles_openfda_timeout(monkeypatch):
    left_id = create_drug("Acetaminophen")
    right_id = create_drug("Ibuprofen")

    def raise_timeout(left_drug, right_drug, db):
        raise openfda_event_service.OpenFDATimeoutError()

    monkeypatch.setattr(
        drug_comparison_service, "build_drug_comparison", raise_timeout
    )
    client = TestClient(app)

    response = client.get(f"/api/drugs/compare?left_id={left_id}&right_id={right_id}")

    assert response.status_code == 504
