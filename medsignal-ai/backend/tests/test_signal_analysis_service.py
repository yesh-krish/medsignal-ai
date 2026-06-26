import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.drug import Drug
from app.models.signal_analysis import SignalAnalysisRun, SignalResult
from app.services import openfda_event_service, signal_analysis_service
from app.services.openfda_event_service import ReactionSignalCount, SignalCountData


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_calculate_signal_metrics_flags_disproportionate_reporting():
    metrics = signal_analysis_service.calculate_signal_metrics(
        target_with_reaction=40,
        target_without_reaction=960,
        comparator_with_reaction=1000,
        comparator_without_reaction=98000,
        reaction="Nausea",
    )

    assert metrics.prr == pytest.approx(3.96, rel=0.001)
    assert metrics.ror == pytest.approx(4.0833, rel=0.001)
    assert metrics.ror_ci_lower > 1
    assert metrics.is_potential_signal is True
    assert "Potential safety signal" in metrics.explanation
    assert "not a confirmed drug risk" in metrics.explanation


def test_calculate_signal_metrics_requires_minimum_reports():
    metrics = signal_analysis_service.calculate_signal_metrics(
        target_with_reaction=2,
        target_without_reaction=98,
        comparator_with_reaction=100,
        comparator_without_reaction=9800,
        reaction="Rash",
        minimum_reports=3,
    )

    assert metrics.is_potential_signal is False
    assert "fewer than 3 target reports" in metrics.explanation


def test_calculate_signal_metrics_handles_zero_cells():
    metrics = signal_analysis_service.calculate_signal_metrics(
        target_with_reaction=3,
        target_without_reaction=97,
        comparator_with_reaction=0,
        comparator_without_reaction=10000,
        reaction="Rare reaction",
    )

    assert metrics.prr > 0
    assert metrics.ror > 0
    assert metrics.ror_ci_lower > 0


def test_analyze_and_save_signals_preserves_history(
    monkeypatch, db_session
):
    drug = Drug(
        rxcui="161",
        input_name="acetaminophen",
        normalized_name="Acetaminophen",
        synonym="Paracetamol",
        tty="IN",
    )
    db_session.add(drug)
    db_session.commit()
    db_session.refresh(drug)
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

    first_run, first_results = signal_analysis_service.analyze_and_save_signals(
        drug.id, drug.normalized_name, db_session
    )
    second_run, _ = signal_analysis_service.analyze_and_save_signals(
        drug.id, drug.normalized_name, db_session
    )
    history = signal_analysis_service.get_signal_analysis_history(drug.id, db_session)
    latest = signal_analysis_service.get_latest_signal_analysis(drug.id, db_session)

    assert first_run.status == "succeeded"
    assert first_results[0].is_potential_signal is True
    assert first_run.target_total_reports == 1000
    assert first_run.comparator_total_reports == 99000
    assert len(history) == 2
    assert second_run.id != first_run.id
    assert latest is not None
    assert latest[0].id == second_run.id


def test_get_signal_timeline_classifies_signal_statuses(db_session):
    runs = [
        SignalAnalysisRun(
            drug_id=1,
            status="succeeded",
            source="openFDA FAERS",
            comparator_scope="All openFDA FAERS reports",
            minimum_reports=3,
            prr_threshold=2,
            ror_ci_lower_threshold=1,
            target_total_reports=100,
            comparator_total_reports=1000,
        ),
        SignalAnalysisRun(
            drug_id=1,
            status="succeeded",
            source="openFDA FAERS",
            comparator_scope="All openFDA FAERS reports",
            minimum_reports=3,
            prr_threshold=2,
            ror_ci_lower_threshold=1,
            target_total_reports=100,
            comparator_total_reports=1000,
        ),
    ]
    db_session.add_all(runs)
    db_session.commit()
    for run in runs:
        db_session.refresh(run)

    db_session.add_all(
        [
            make_signal_result(runs[0].id, "Nausea", 2.4, True),
            make_signal_result(runs[1].id, "Nausea", 2.8, True),
            make_signal_result(runs[0].id, "Rash", 2.3, True),
            make_signal_result(runs[1].id, "Rash", 1.2, False),
            make_signal_result(runs[0].id, "Headache", 1.4, False),
            make_signal_result(runs[1].id, "Headache", 2.5, True),
        ]
    )
    db_session.commit()

    timeline = signal_analysis_service.get_signal_timeline(1, db_session)

    statuses = {item["reaction"]: item["status"] for item in timeline["reactions"]}
    assert timeline["run_count"] == 2
    assert statuses["Headache"] == "new"
    assert statuses["Nausea"] == "continuing"
    assert statuses["Rash"] == "resolved"
    assert len(timeline["reactions"][0]["points"]) == 2


def make_signal_result(
    run_id: int,
    reaction: str,
    prr: float,
    is_potential_signal: bool,
) -> SignalResult:
    return SignalResult(
        run_id=run_id,
        drug_id=1,
        reaction=reaction,
        target_with_reaction=10,
        target_without_reaction=90,
        comparator_with_reaction=50,
        comparator_without_reaction=950,
        prr=prr,
        ror=prr + 0.1,
        ror_ci_lower=1.2 if is_potential_signal else 0.8,
        ror_ci_upper=3.5,
        is_potential_signal=is_potential_signal,
        explanation="Test signal explanation",
    )
