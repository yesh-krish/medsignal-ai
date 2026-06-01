from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.drug_label import DrugLabel
from app.services import summarizer_service
from app.services.summarizer_service import (
    SAFETY_SUMMARY_DISCLAIMER,
    generate_and_save_safety_summary,
)


def test_generate_and_save_safety_summary(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    label = DrugLabel(
        drug_id=1,
        set_id="label-set-id",
        brand_name=["Tylenol"],
        generic_name=["Acetaminophen"],
        warnings=["Talk with a clinician if you have liver disease."],
        boxed_warning=["Severe liver injury has been reported with overdose."],
        adverse_reactions=["Rash"],
        contraindications=["Known acetaminophen allergy"],
        indications_and_usage=["Pain relief"],
        raw_label_json={},
    )
    monkeypatch.setattr(
        summarizer_service,
        "_generate_summary",
        lambda prompt: "Plain-English safety summary.",
    )

    summary, disclaimer = generate_and_save_safety_summary(1, label, db)

    assert summary.id is not None
    assert summary.drug_id == 1
    assert summary.summary_text == "Plain-English safety summary."
    assert summary.model_name == "sshleifer/distilbart-cnn-6-6"
    assert summary.input_length > 0
    assert summary.output_length == len("Plain-English safety summary.")
    assert summary.latency_ms >= 0
    assert disclaimer == SAFETY_SUMMARY_DISCLAIMER
    db.close()


def test_generate_and_save_safety_summary_rejects_empty_label():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    label = DrugLabel(
        drug_id=1,
        set_id="label-set-id",
        brand_name=["Tylenol"],
        generic_name=["Acetaminophen"],
        warnings=None,
        boxed_warning=None,
        adverse_reactions=None,
        contraindications=None,
        indications_and_usage=None,
        raw_label_json={},
    )

    try:
        generate_and_save_safety_summary(1, label, db)
    except ValueError as exc:
        assert "No label safety sections" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
    finally:
        db.close()


def test_clean_summary_removes_causal_wording():
    cleaned = summarizer_service._clean_summary("This medication causes rash")

    assert "causes" not in cleaned.lower()
    assert cleaned.endswith(".")


def test_clean_summary_trims_incomplete_final_sentence():
    cleaned = summarizer_service._clean_summary(
        "Warnings are listed. Routine monitoring is"
    )

    assert cleaned == "Warnings are listed."
