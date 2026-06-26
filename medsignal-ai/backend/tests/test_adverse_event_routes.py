from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.adverse_event import AdverseEvent
from app.models.drug import Drug
from app.models.ingestion_run import IngestionRun
from app.services import openfda_event_service
from app.services.openfda_event_service import OpenFDATimeoutError, OpenFDAUpstreamError


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


def test_get_reported_adverse_events(monkeypatch):
    drug_id = create_drug()

    def fake_fetch(normalized_drug_name, drug_id, db, limit=25):
        event = AdverseEvent(
            drug_id=drug_id,
            reaction="Nausea",
            serious=True,
            outcome="Recovered",
            report_date=date(2024, 1, 15),
            patient_age=45,
            patient_sex="female",
            raw_event_json={"safetyreportid": "10000001"},
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return [event]

    monkeypatch.setattr(
        openfda_event_service, "fetch_and_save_reported_adverse_events", fake_fetch
    )
    client = TestClient(app)

    response = client.get(f"/api/drugs/{drug_id}/events")

    assert response.status_code == 200
    assert response.json()[0]["reaction"] == "Nausea"
    assert response.json()[0]["serious"] is True
    assert response.json()[0]["patient_sex"] == "female"


def test_get_reported_adverse_events_drug_not_found():
    client = TestClient(app)

    response = client.get("/api/drugs/999/events")

    assert response.status_code == 404


def test_get_reported_adverse_events_openfda_failure(monkeypatch):
    drug_id = create_drug()

    def raise_upstream(normalized_drug_name, drug_id, db, limit=25):
        raise OpenFDAUpstreamError()

    monkeypatch.setattr(
        openfda_event_service, "fetch_and_save_reported_adverse_events", raise_upstream
    )
    client = TestClient(app)

    response = client.get(f"/api/drugs/{drug_id}/events")

    assert response.status_code == 502


def test_get_reported_adverse_events_openfda_timeout(monkeypatch):
    drug_id = create_drug()

    def raise_timeout(normalized_drug_name, drug_id, db, limit=25):
        raise OpenFDATimeoutError()

    monkeypatch.setattr(
        openfda_event_service, "fetch_and_save_reported_adverse_events", raise_timeout
    )
    client = TestClient(app)

    response = client.get(f"/api/drugs/{drug_id}/events")

    assert response.status_code == 504


def test_get_reported_adverse_event_trends(monkeypatch):
    drug_id = create_drug()

    def fake_fetch_trends(normalized_drug_name):
        return {
            "top_reported_reactions": [{"reaction": "Nausea", "count": 2}],
            "reports_by_year": {"2014": 1, "2024": 2},
            "seriousness_breakdown": {"serious": 1, "not_serious": 2},
            "sex_breakdown": {"female": 2, "unknown": 1},
            "total_reports": 3,
        }

    monkeypatch.setattr(
        openfda_event_service,
        "fetch_reported_adverse_event_trends",
        fake_fetch_trends,
    )
    client = TestClient(app)

    response = client.get(f"/api/drugs/{drug_id}/event-trends")

    assert response.status_code == 200
    assert response.json()["total_reports"] == 3
    assert response.json()["reports_by_year"] == {"2014": 1, "2024": 2}
    assert response.json()["seriousness_breakdown"] == {
        "serious": 1,
        "not_serious": 2,
    }


def test_get_latest_event_ingestion_run():
    drug_id = create_drug()
    db = TestingSessionLocal()
    db.add(
        IngestionRun(
            drug_id=drug_id,
            source="openFDA FAERS",
            status="succeeded",
            query='patient.drug.medicinalproduct:"Tylenol"',
            requested_reports=100,
            fetched_reports=100,
            saved_reaction_rows=250,
            duplicate_reports_skipped=4,
            source_last_updated="2026-06-01",
        )
    )
    db.commit()
    db.close()
    client = TestClient(app)

    response = client.get(f"/api/drugs/{drug_id}/ingestion-runs/latest")

    assert response.status_code == 200
    assert response.json()["source"] == "openFDA FAERS"
    assert response.json()["fetched_reports"] == 100
    assert response.json()["duplicate_reports_skipped"] == 4
