from prefect import flow, get_run_logger, task
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.drug import Drug
from app.services import safety_signal_service


@task
def load_saved_drug_ids() -> list[int]:
    with SessionLocal() as db:
        return list(db.scalars(select(Drug.id).order_by(Drug.id)))


@task
def detect_signals_for_drug(
    drug_id: int,
    recent_window_days: int = 90,
    percent_increase_threshold: float = 100.0,
    min_current_count: int = 3,
) -> dict[str, object]:
    logger = get_run_logger()
    with SessionLocal() as db:
        drug = db.scalar(select(Drug).where(Drug.id == drug_id))
        if drug is None:
            message = f"Drug {drug_id} was not found."
            logger.error(message)
            return {"drug_id": drug_id, "success": False, "message": message}

        try:
            alerts = safety_signal_service.detect_and_save_potential_safety_signals(
                drug_id=drug.id,
                db=db,
                recent_window_days=recent_window_days,
                percent_increase_threshold=percent_increase_threshold,
                min_current_count=min_current_count,
            )
            logger.info(
                "Detected %s potential safety signals for drug %s (%s).",
                len(alerts),
                drug.id,
                drug.normalized_name,
            )
            return {
                "drug_id": drug.id,
                "normalized_name": drug.normalized_name,
                "success": True,
                "potential_safety_signal_count": len(alerts),
            }
        except Exception as exc:
            logger.exception(
                "Failed to detect potential safety signals for drug %s", drug.id
            )
            return {
                "drug_id": drug.id,
                "normalized_name": drug.normalized_name,
                "success": False,
                "message": str(exc),
            }


@flow(name="detect-safety-signals")
def detect_safety_signals(
    recent_window_days: int = 90,
    percent_increase_threshold: float = 100.0,
    min_current_count: int = 3,
) -> list[dict[str, object]]:
    logger = get_run_logger()
    drug_ids = load_saved_drug_ids()
    logger.info("Detecting potential safety signals for %s saved drugs.", len(drug_ids))
    results = [
        detect_signals_for_drug(
            drug_id,
            recent_window_days,
            percent_increase_threshold,
            min_current_count,
        )
        for drug_id in drug_ids
    ]
    success_count = sum(1 for result in results if result.get("success"))
    logger.info(
        "Potential safety signal detection complete: %s succeeded, %s failed.",
        success_count,
        len(results) - success_count,
    )
    return results


if __name__ == "__main__":
    detect_safety_signals()
