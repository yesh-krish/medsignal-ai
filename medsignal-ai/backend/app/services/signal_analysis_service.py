import math
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.signal_analysis import SignalAnalysisRun, SignalResult
from app.services import openfda_event_service


@dataclass(frozen=True)
class SignalMetrics:
    prr: float
    ror: float
    ror_ci_lower: float
    ror_ci_upper: float
    is_potential_signal: bool
    explanation: str


def calculate_signal_metrics(
    target_with_reaction: int,
    target_without_reaction: int,
    comparator_with_reaction: int,
    comparator_without_reaction: int,
    reaction: str,
    minimum_reports: int = 3,
    prr_threshold: float = 2.0,
    ror_ci_lower_threshold: float = 1.0,
) -> SignalMetrics:
    cells = (
        target_with_reaction,
        target_without_reaction,
        comparator_with_reaction,
        comparator_without_reaction,
    )
    if any(value < 0 for value in cells):
        raise ValueError("Signal contingency-table counts must not be negative")

    adjusted = tuple(value + 0.5 for value in cells) if 0 in cells else cells
    a, b, c, d = (float(value) for value in adjusted)
    target_rate = a / (a + b)
    comparator_rate = c / (c + d)
    prr = target_rate / comparator_rate
    ror = (a * d) / (b * c)
    standard_error = math.sqrt((1 / a) + (1 / b) + (1 / c) + (1 / d))
    ror_ci_lower = math.exp(math.log(ror) - (1.96 * standard_error))
    ror_ci_upper = math.exp(math.log(ror) + (1.96 * standard_error))

    is_potential_signal = (
        target_with_reaction >= minimum_reports
        and prr >= prr_threshold
        and ror_ci_lower > ror_ci_lower_threshold
    )
    explanation = _build_signal_explanation(
        reaction=reaction,
        target_with_reaction=target_with_reaction,
        target_rate=target_rate,
        comparator_rate=comparator_rate,
        prr=prr,
        ror=ror,
        ror_ci_lower=ror_ci_lower,
        ror_ci_upper=ror_ci_upper,
        is_potential_signal=is_potential_signal,
        minimum_reports=minimum_reports,
        prr_threshold=prr_threshold,
        ror_ci_lower_threshold=ror_ci_lower_threshold,
    )
    return SignalMetrics(
        prr=round(prr, 4),
        ror=round(ror, 4),
        ror_ci_lower=round(ror_ci_lower, 4),
        ror_ci_upper=round(ror_ci_upper, 4),
        is_potential_signal=is_potential_signal,
        explanation=explanation,
    )


def analyze_and_save_signals(
    drug_id: int,
    normalized_drug_name: str,
    db: Session,
    reaction_limit: int = 10,
    minimum_reports: int = 3,
    prr_threshold: float = 2.0,
    ror_ci_lower_threshold: float = 1.0,
) -> tuple[SignalAnalysisRun, list[SignalResult]]:
    run = SignalAnalysisRun(
        drug_id=drug_id,
        status="running",
        source="openFDA FAERS",
        comparator_scope="All openFDA FAERS reports",
        minimum_reports=minimum_reports,
        prr_threshold=prr_threshold,
        ror_ci_lower_threshold=ror_ci_lower_threshold,
        target_total_reports=0,
        comparator_total_reports=0,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        counts = openfda_event_service.fetch_signal_count_data(
            normalized_drug_name, reaction_limit=reaction_limit
        )
        comparator_total = max(counts.all_reports_total - counts.target_total, 0)
        results: list[SignalResult] = []
        for reaction_count in counts.reactions:
            a = reaction_count.target_count
            b = max(counts.target_total - a, 0)
            c = max(reaction_count.all_reaction_count - a, 0)
            d = max(counts.all_reports_total - a - b - c, 0)
            metrics = calculate_signal_metrics(
                target_with_reaction=a,
                target_without_reaction=b,
                comparator_with_reaction=c,
                comparator_without_reaction=d,
                reaction=reaction_count.reaction,
                minimum_reports=minimum_reports,
                prr_threshold=prr_threshold,
                ror_ci_lower_threshold=ror_ci_lower_threshold,
            )
            results.append(
                SignalResult(
                    run_id=run.id,
                    drug_id=drug_id,
                    reaction=reaction_count.reaction,
                    target_with_reaction=a,
                    target_without_reaction=b,
                    comparator_with_reaction=c,
                    comparator_without_reaction=d,
                    prr=metrics.prr,
                    ror=metrics.ror,
                    ror_ci_lower=metrics.ror_ci_lower,
                    ror_ci_upper=metrics.ror_ci_upper,
                    is_potential_signal=metrics.is_potential_signal,
                    explanation=metrics.explanation,
                )
            )

        db.add_all(results)
        run.status = "succeeded"
        run.target_total_reports = counts.target_total
        run.comparator_total_reports = comparator_total
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(run)
        for result in results:
            db.refresh(result)
        return run, results
    except Exception as exc:
        db.rollback()
        failed_run = db.get(SignalAnalysisRun, run.id)
        if failed_run is not None:
            failed_run.status = "failed"
            failed_run.error_message = str(exc)[:2000]
            failed_run.completed_at = datetime.now(timezone.utc)
            db.commit()
        raise


def get_latest_signal_analysis(
    drug_id: int, db: Session
) -> tuple[SignalAnalysisRun, list[SignalResult]] | None:
    run = db.scalar(
        select(SignalAnalysisRun)
        .where(
            SignalAnalysisRun.drug_id == drug_id,
            SignalAnalysisRun.status == "succeeded",
        )
        .order_by(SignalAnalysisRun.completed_at.desc(), SignalAnalysisRun.id.desc())
        .limit(1)
    )
    if run is None:
        return None
    results = list(
        db.scalars(
            select(SignalResult)
            .where(SignalResult.run_id == run.id)
            .order_by(
                SignalResult.is_potential_signal.desc(),
                SignalResult.prr.desc(),
            )
        )
    )
    return run, results


def get_signal_analysis_history(
    drug_id: int, db: Session, limit: int = 20
) -> list[SignalAnalysisRun]:
    return list(
        db.scalars(
            select(SignalAnalysisRun)
            .where(SignalAnalysisRun.drug_id == drug_id)
            .order_by(SignalAnalysisRun.started_at.desc(), SignalAnalysisRun.id.desc())
            .limit(limit)
        )
    )


def _build_signal_explanation(
    *,
    reaction: str,
    target_with_reaction: int,
    target_rate: float,
    comparator_rate: float,
    prr: float,
    ror: float,
    ror_ci_lower: float,
    ror_ci_upper: float,
    is_potential_signal: bool,
    minimum_reports: int,
    prr_threshold: float,
    ror_ci_lower_threshold: float,
) -> str:
    comparison = (
        f"{reaction} appeared in {target_rate:.2%} of reports mentioning this "
        f"medication and {comparator_rate:.2%} of comparator reports. "
        f"PRR {prr:.2f}; ROR {ror:.2f} (95% CI {ror_ci_lower:.2f}-{ror_ci_upper:.2f})."
    )
    if is_potential_signal:
        return (
            f"Potential safety signal: {comparison} It met the minimum of "
            f"{minimum_reports} reports, PRR threshold of {prr_threshold:.2f}, "
            f"and ROR lower confidence-bound threshold of "
            f"{ror_ci_lower_threshold:.2f}. This is a reporting signal for "
            "review, not a confirmed drug risk."
        )

    unmet: list[str] = []
    if target_with_reaction < minimum_reports:
        unmet.append(f"fewer than {minimum_reports} target reports")
    if prr < prr_threshold:
        unmet.append(f"PRR below {prr_threshold:.2f}")
    if ror_ci_lower <= ror_ci_lower_threshold:
        unmet.append(
            f"ROR lower confidence bound not above {ror_ci_lower_threshold:.2f}"
        )
    return f"Not flagged as a potential safety signal: {comparison} " + "; ".join(
        unmet
    )
