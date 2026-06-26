from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.drug import Drug
from app.services import openfda_event_service
from app.services.openfda_event_service import ReactionSignalCount, SignalCountData


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
        rxcui="161",
        input_name="acetaminophen",
        normalized_name="Acetaminophen",
        synonym="Paracetamol",
        tty="IN",
    )
    db.add(drug)
    db.commit()
    db.refresh(drug)
    drug_id = drug.id
    db.close()
    return drug_id


def test_signal_analysis_routes(monkeypatch):
    drug_id = create_drug()
    counts = SignalCountData(
        target_total=1000,
        all_reports_total=100000,
        reactions=[
            ReactionSignalCount(
                reaction="Nausea", target_count=40, all_reaction_count=1040
            )
        ],
    )
    monkeypatch.setattr(
        openfda_event_service,
        "fetch_signal_count_data",
        lambda normalized_drug_name, reaction_limit=10: counts,
    )
    client = TestClient(app)

    analyze_response = client.post(f"/api/drugs/{drug_id}/signals/analyze")
    latest_response = client.get(f"/api/drugs/{drug_id}/signals/latest")
    history_response = client.get(f"/api/drugs/{drug_id}/signals/history")
    timeline_response = client.get(f"/api/drugs/{drug_id}/signals/timeline")

    assert analyze_response.status_code == 200
    assert analyze_response.json()["results"][0]["is_potential_signal"] is True
    assert latest_response.status_code == 200
    assert latest_response.json()["run"]["target_total_reports"] == 1000
    assert history_response.status_code == 200
    assert len(history_response.json()) == 1
    assert timeline_response.status_code == 200
    assert timeline_response.json()["reactions"][0]["status"] == "new"


def test_latest_signal_analysis_returns_null_without_run():
    drug_id = create_drug()
    client = TestClient(app)

    response = client.get(f"/api/drugs/{drug_id}/signals/latest")

    assert response.status_code == 200
    assert response.json() is None
