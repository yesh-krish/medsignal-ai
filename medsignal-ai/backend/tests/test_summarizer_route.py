from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.drug import Drug
from app.models.drug_label import DrugLabel
from app.models.safety_summary import SafetySummary
from app.services import summarizer_service


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


def create_drug_with_label() -> int:
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
    label = DrugLabel(
        drug_id=drug.id,
        set_id="label-set-id",
        brand_name=["Tylenol"],
        generic_name=["Acetaminophen"],
        warnings=["Talk with a clinician if you have liver disease."],
        boxed_warning=None,
        adverse_reactions=["Rash"],
        contraindications=["Known acetaminophen allergy"],
        indications_and_usage=["Pain relief"],
        raw_label_json={},
    )
    db.add(label)
    db.commit()
    drug_id = drug.id
    db.close()
    return drug_id


def test_summarize_label_route(monkeypatch):
    drug_id = create_drug_with_label()

    def fake_generate_and_save_safety_summary(
        drug_id, normalized_drug_name, label, db
    ):
        summary = SafetySummary(
            drug_id=drug_id,
            summary_text="Plain-English safety summary.",
            model_name="test-model",
            input_length=100,
            output_length=30,
            latency_ms=25,
            mlflow_run_id="run-123",
        )
        db.add(summary)
        db.commit()
        db.refresh(summary)
        return summary, "Educational disclaimer."

    monkeypatch.setattr(
        summarizer_service,
        "generate_and_save_safety_summary",
        fake_generate_and_save_safety_summary,
    )
    client = TestClient(app)

    response = client.post(f"/api/drugs/{drug_id}/summarize-label")

    assert response.status_code == 200
    assert response.json()["summary_text"] == "Plain-English safety summary."
    assert response.json()["model_name"] == "test-model"
    assert response.json()["mlflow_run_id"] == "run-123"
    assert response.json()["disclaimer"] == "Educational disclaimer."


def test_summarize_label_route_drug_not_found():
    client = TestClient(app)

    response = client.post("/api/drugs/999/summarize-label")

    assert response.status_code == 404


def test_summarize_label_route_ai_failure(monkeypatch):
    drug_id = create_drug_with_label()

    def raise_failure(drug_id, normalized_drug_name, label, db):
        raise summarizer_service.SummarizerUnavailableError()

    monkeypatch.setattr(
        summarizer_service,
        "generate_and_save_safety_summary",
        raise_failure,
    )
    client = TestClient(app)

    response = client.post(f"/api/drugs/{drug_id}/summarize-label")

    assert response.status_code == 502
