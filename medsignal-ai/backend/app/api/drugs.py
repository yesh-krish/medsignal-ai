from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.drug import Drug
from app.schemas.adverse_event import AdverseEventRead, EventTrends
from app.schemas.drug import DrugSearchResult
from app.schemas.drug_label import DrugLabelRead
from app.schemas.safety_summary import SafetySummaryRead
from app.services import openfda_event_service
from app.services import openfda_label_service
from app.services import rxnorm_service
from app.services import summarizer_service

router = APIRouter(prefix="/api/drugs", tags=["drugs"])


@router.get("/search", response_model=DrugSearchResult)
def search_drugs(
    query: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
) -> DrugSearchResult:
    if not query.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query must not be empty",
        )

    try:
        return rxnorm_service.search_and_save_drug(query, db)
    except rxnorm_service.RxNormNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No drug match found",
        ) from exc
    except rxnorm_service.RxNormTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="RxNorm request timed out",
        ) from exc
    except rxnorm_service.RxNormUpstreamError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="RxNorm request failed",
        ) from exc


@router.get("/{drug_id}", response_model=DrugSearchResult)
def get_drug(
    drug_id: int,
    db: Session = Depends(get_db),
) -> DrugSearchResult:
    return _get_drug_or_404(drug_id, db)


@router.get("/{drug_id}/events", response_model=list[AdverseEventRead])
def get_reported_adverse_events(
    drug_id: int,
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[AdverseEventRead]:
    drug = _get_drug_or_404(drug_id, db)
    if not drug.normalized_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Drug does not have a normalized name",
        )

    try:
        return openfda_event_service.fetch_and_save_reported_adverse_events(
            drug.normalized_name, drug.id, db, limit=limit
        )
    except openfda_event_service.OpenFDATimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="openFDA request timed out",
        ) from exc
    except openfda_event_service.OpenFDAUpstreamError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="openFDA request failed",
        ) from exc


@router.get("/{drug_id}/event-trends", response_model=EventTrends)
def get_reported_adverse_event_trends(
    drug_id: int,
    db: Session = Depends(get_db),
) -> EventTrends:
    _get_drug_or_404(drug_id, db)
    events = openfda_event_service.get_saved_reported_adverse_events(drug_id, db)
    return openfda_event_service.build_reported_adverse_event_trends(events)


@router.get("/{drug_id}/label", response_model=DrugLabelRead | None)
def get_drug_label(
    drug_id: int,
    db: Session = Depends(get_db),
) -> DrugLabelRead | None:
    drug = _get_drug_or_404(drug_id, db)
    if not drug.normalized_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Drug does not have a normalized name",
        )

    try:
        return openfda_label_service.fetch_and_save_drug_label(
            drug.normalized_name, drug.id, db
        )
    except openfda_label_service.OpenFDALabelTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="openFDA label request timed out",
        ) from exc
    except openfda_label_service.OpenFDALabelUpstreamError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="openFDA label request failed",
        ) from exc


@router.post("/{drug_id}/summarize-label", response_model=SafetySummaryRead)
def summarize_drug_label(
    drug_id: int,
    db: Session = Depends(get_db),
) -> SafetySummaryRead:
    drug = _get_drug_or_404(drug_id, db)
    if not drug.normalized_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Drug does not have a normalized name",
        )

    label = openfda_label_service.get_saved_drug_label(drug.id, db)
    if label is None:
        try:
            label = openfda_label_service.fetch_and_save_drug_label(
                drug.normalized_name, drug.id, db
            )
        except openfda_label_service.OpenFDALabelTimeoutError as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="openFDA label request timed out",
            ) from exc
        except openfda_label_service.OpenFDALabelUpstreamError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="openFDA label request failed",
            ) from exc

    if label is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FDA label not found",
        )

    try:
        summary, disclaimer = summarizer_service.generate_and_save_safety_summary(
            drug.id, drug.normalized_name, label, db
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No label safety sections are available to summarize",
        ) from exc
    except summarizer_service.SummarizerUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI summarizer failed",
        ) from exc

    return {
        "id": summary.id,
        "drug_id": summary.drug_id,
        "summary_text": summary.summary_text,
        "model_name": summary.model_name,
        "input_length": summary.input_length,
        "output_length": summary.output_length,
        "latency_ms": summary.latency_ms,
        "mlflow_run_id": summary.mlflow_run_id,
        "disclaimer": disclaimer,
        "created_at": summary.created_at,
    }


def _get_drug_or_404(drug_id: int, db: Session) -> Drug:
    drug = db.scalar(select(Drug).where(Drug.id == drug_id))
    if drug is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drug not found",
        )
    return drug
