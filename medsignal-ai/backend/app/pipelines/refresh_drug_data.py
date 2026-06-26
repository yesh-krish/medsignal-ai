from prefect import flow, get_run_logger, task
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.drug import Drug
from app.services import openfda_event_service, openfda_label_service


@task
def load_saved_drug_ids() -> list[int]:
    with SessionLocal() as db:
        return list(db.scalars(select(Drug.id).order_by(Drug.id)))


@task
def refresh_single_drug(drug_id: int, event_limit: int = 25) -> dict[str, object]:
    logger = get_run_logger()
    with SessionLocal() as db:
        drug = db.scalar(select(Drug).where(Drug.id == drug_id))
        if drug is None:
            message = f"Drug {drug_id} was not found."
            logger.error(message)
            return {"drug_id": drug_id, "success": False, "message": message}

        if not drug.normalized_name:
            message = f"Drug {drug_id} has no normalized name."
            logger.error(message)
            return {"drug_id": drug_id, "success": False, "message": message}

        try:
            events = openfda_event_service.fetch_and_save_reported_adverse_events(
                drug.normalized_name, drug.id, db, limit=event_limit
            )
            label = openfda_label_service.fetch_and_save_drug_label(
                drug.normalized_name, drug.id, db
            )
            trends = openfda_event_service.build_reported_adverse_event_trends(events)
            logger.info(
                "Refreshed drug %s (%s): %s reported adverse event rows, "
                "%s total reports, label=%s",
                drug.id,
                drug.normalized_name,
                len(events),
                trends["total_reports"],
                bool(label),
            )
            return {
                "drug_id": drug.id,
                "normalized_name": drug.normalized_name,
                "success": True,
                "reported_adverse_event_rows": len(events),
                "total_reports": trends["total_reports"],
                "label_found": bool(label),
            }
        except Exception as exc:
            logger.exception("Failed to refresh drug %s", drug.id)
            return {
                "drug_id": drug.id,
                "normalized_name": drug.normalized_name,
                "success": False,
                "message": str(exc),
            }


@flow(name="refresh-drug-data")
def refresh_drug_data(event_limit: int = 25) -> list[dict[str, object]]:
    logger = get_run_logger()
    drug_ids = load_saved_drug_ids()
    logger.info("Refreshing openFDA data for %s saved drugs.", len(drug_ids))
    results = [refresh_single_drug(drug_id, event_limit) for drug_id in drug_ids]
    success_count = sum(1 for result in results if result.get("success"))
    logger.info(
        "Refresh complete: %s succeeded, %s failed.",
        success_count,
        len(results) - success_count,
    )
    return results


if __name__ == "__main__":
    refresh_drug_data()
