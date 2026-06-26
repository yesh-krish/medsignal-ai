from prefect import flow, get_run_logger, task
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.drug import Drug
from app.services import signal_analysis_service


@task
def load_signal_analysis_drug_ids() -> list[int]:
    with SessionLocal() as db:
        return list(db.scalars(select(Drug.id).order_by(Drug.id)))


@task
def analyze_signals_for_drug(
    drug_id: int,
    reaction_limit: int,
    minimum_reports: int,
    prr_threshold: float,
    ror_ci_lower_threshold: float,
) -> dict[str, object]:
    logger = get_run_logger()
    with SessionLocal() as db:
        drug = db.get(Drug, drug_id)
        if drug is None or not drug.normalized_name:
            return {"drug_id": drug_id, "success": False, "result_count": 0}
        try:
            run, results = signal_analysis_service.analyze_and_save_signals(
                drug_id=drug.id,
                normalized_drug_name=drug.normalized_name,
                db=db,
                reaction_limit=reaction_limit,
                minimum_reports=minimum_reports,
                prr_threshold=prr_threshold,
                ror_ci_lower_threshold=ror_ci_lower_threshold,
            )
            potential_count = sum(
                1 for result in results if result.is_potential_signal
            )
            logger.info(
                "Signal analysis run %s completed for drug %s: %s potential signals.",
                run.id,
                drug.id,
                potential_count,
            )
            return {
                "drug_id": drug.id,
                "success": True,
                "run_id": run.id,
                "result_count": len(results),
                "potential_signal_count": potential_count,
            }
        except Exception as exc:
            logger.exception("Signal analysis failed for drug %s", drug_id)
            return {
                "drug_id": drug_id,
                "success": False,
                "result_count": 0,
                "message": str(exc),
            }


@flow(name="analyze-safety-signals")
def analyze_safety_signals(
    reaction_limit: int = 10,
    minimum_reports: int = 3,
    prr_threshold: float = 2.0,
    ror_ci_lower_threshold: float = 1.0,
) -> list[dict[str, object]]:
    logger = get_run_logger()
    drug_ids = load_signal_analysis_drug_ids()
    logger.info("Running PRR/ROR analysis for %s saved drugs.", len(drug_ids))
    return [
        analyze_signals_for_drug(
            drug_id,
            reaction_limit,
            minimum_reports,
            prr_threshold,
            ror_ci_lower_threshold,
        )
        for drug_id in drug_ids
    ]


if __name__ == "__main__":
    analyze_safety_signals()
