from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.drug import Drug
from app.schemas.adverse_event import AdverseEventRead, EventTrends
from app.schemas.drug import DrugSearchResult
from app.schemas.drug_comparison import DrugComparisonResponse
from app.schemas.drug_label import DrugLabelRead
from app.schemas.ingestion_run import IngestionRunRead
from app.schemas.safety_alert import SafetyAlertRead
from app.schemas.safety_summary import SafetySummaryRead
from app.schemas.signal_analysis import SignalAnalysisResponse, SignalAnalysisRunRead
from app.services import openfda_event_service
from app.services import openfda_label_service
from app.services import drug_comparison_service
from app.services import rxnorm_service
from app.services import safety_signal_service
from app.services import summarizer_service
from app.services import signal_analysis_service

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


@router.get("/compare", response_model=DrugComparisonResponse)
def compare_drugs(
    left_id: int = Query(..., gt=0),
    right_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
) -> DrugComparisonResponse:
    if left_id == right_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Choose two different medications to compare",
        )

    left_drug = _get_drug_or_404(left_id, db)
    right_drug = _get_drug_or_404(right_id, db)
    try:
        return drug_comparison_service.build_drug_comparison(
            left_drug, right_drug, db
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except (
        openfda_event_service.OpenFDATimeoutError,
        openfda_label_service.OpenFDALabelTimeoutError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="openFDA comparison request timed out",
        ) from exc
    except (
        openfda_event_service.OpenFDAUpstreamError,
        openfda_label_service.OpenFDALabelUpstreamError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="openFDA comparison request failed",
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
    limit: int = Query(100, ge=1, le=500),
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


@router.get(
    "/{drug_id}/ingestion-runs/latest",
    response_model=IngestionRunRead | None,
)
def get_latest_event_ingestion_run(
    drug_id: int,
    db: Session = Depends(get_db),
) -> IngestionRunRead | None:
    _get_drug_or_404(drug_id, db)
    return openfda_event_service.get_latest_ingestion_run(drug_id, db)


@router.get("/{drug_id}/event-trends", response_model=EventTrends)
def get_reported_adverse_event_trends(
    drug_id: int,
    db: Session = Depends(get_db),
) -> EventTrends:
    drug = _get_drug_or_404(drug_id, db)
    if not drug.normalized_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Drug does not have a normalized name",
        )

    try:
        return openfda_event_service.fetch_reported_adverse_event_trends(
            drug.normalized_name
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


@router.get("/{drug_id}/alerts", response_model=list[SafetyAlertRead])
def get_drug_safety_alerts(
    drug_id: int,
    db: Session = Depends(get_db),
) -> list[SafetyAlertRead]:
    _get_drug_or_404(drug_id, db)
    return safety_signal_service.get_safety_alerts(drug_id, db)


@router.post("/{drug_id}/signals/analyze", response_model=SignalAnalysisResponse)
def analyze_drug_signals(
    drug_id: int,
    reaction_limit: int = Query(10, ge=1, le=25),
    minimum_reports: int = Query(3, ge=1, le=100),
    prr_threshold: float = Query(2.0, gt=0),
    ror_ci_lower_threshold: float = Query(1.0, gt=0),
    db: Session = Depends(get_db),
) -> SignalAnalysisResponse:
    drug = _get_drug_or_404(drug_id, db)
    if not drug.normalized_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Drug does not have a normalized name",
        )
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
        return {"run": run, "results": results}
    except openfda_event_service.OpenFDATimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="openFDA signal analysis timed out",
        ) from exc
    except openfda_event_service.OpenFDAUpstreamError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="openFDA signal analysis failed",
        ) from exc


@router.get(
    "/{drug_id}/signals/latest",
    response_model=SignalAnalysisResponse | None,
)
def get_latest_drug_signal_analysis(
    drug_id: int,
    db: Session = Depends(get_db),
) -> SignalAnalysisResponse | None:
    _get_drug_or_404(drug_id, db)
    analysis = signal_analysis_service.get_latest_signal_analysis(drug_id, db)
    if analysis is None:
        return None
    run, results = analysis
    return {"run": run, "results": results}


@router.get(
    "/{drug_id}/signals/history",
    response_model=list[SignalAnalysisRunRead],
)
def get_drug_signal_analysis_history(
    drug_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[SignalAnalysisRunRead]:
    _get_drug_or_404(drug_id, db)
    return signal_analysis_service.get_signal_analysis_history(drug_id, db, limit)


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
