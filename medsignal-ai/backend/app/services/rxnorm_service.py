from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.drug import Drug


class RxNormNotFoundError(Exception):
    pass


class RxNormUpstreamError(Exception):
    pass


class RxNormTimeoutError(Exception):
    pass


@dataclass(frozen=True)
class RxNormConcept:
    rxcui: str
    name: str
    synonym: str | None
    tty: str | None


def search_and_save_drug(query: str, db: Session) -> Drug:
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("Query must not be empty")

    cached_drug = _find_cached_drug(cleaned_query, db)
    if cached_drug is not None:
        return cached_drug

    rxcui = _find_best_rxcui(cleaned_query)
    concept = _get_concept_properties(rxcui)

    existing_drug = db.scalar(select(Drug).where(Drug.rxcui == concept.rxcui))
    if existing_drug is None:
        drug = Drug(
            rxcui=concept.rxcui,
            input_name=cleaned_query,
            normalized_name=concept.name,
            synonym=concept.synonym,
            tty=concept.tty,
        )
        db.add(drug)
    else:
        drug = existing_drug
        drug.input_name = cleaned_query
        drug.normalized_name = concept.name
        drug.synonym = concept.synonym
        drug.tty = concept.tty

    db.commit()
    db.refresh(drug)
    return drug


def _find_cached_drug(query: str, db: Session) -> Drug | None:
    normalized_query = query.casefold()
    return db.scalar(
        select(Drug)
        .where(
            or_(
                func.lower(Drug.input_name) == normalized_query,
                func.lower(Drug.normalized_name) == normalized_query,
                func.lower(Drug.synonym) == normalized_query,
            )
        )
        .order_by(Drug.updated_at.desc(), Drug.id.desc())
        .limit(1)
    )


def _find_best_rxcui(query: str) -> str:
    settings = get_settings()
    data = _rxnorm_get_json(
        f"{settings.rxnorm_base_url}/REST/rxcui.json",
        params={"name": query, "search": "2"},
    )
    rxcuis = data.get("idGroup", {}).get("rxnormId", [])
    if not rxcuis:
        raise RxNormNotFoundError("No RxNorm concept found")
    return str(rxcuis[0])


def _get_concept_properties(rxcui: str) -> RxNormConcept:
    settings = get_settings()
    data = _rxnorm_get_json(
        f"{settings.rxnorm_base_url}/REST/rxcui/{rxcui}/properties.json"
    )
    properties = data.get("properties")
    if not properties:
        raise RxNormUpstreamError("RxNorm concept properties were missing")

    normalized_name = properties.get("name")
    if not normalized_name:
        raise RxNormUpstreamError("RxNorm concept name was missing")

    return RxNormConcept(
        rxcui=str(properties.get("rxcui") or rxcui),
        name=normalized_name,
        synonym=properties.get("synonym"),
        tty=properties.get("tty"),
    )


def _rxnorm_get_json(url: str, params: dict[str, str] | None = None) -> dict[str, Any]:
    settings = get_settings()
    try:
        with httpx.Client(timeout=settings.rxnorm_timeout_seconds) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as exc:
        raise RxNormTimeoutError("RxNorm request timed out") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise RxNormUpstreamError("RxNorm request failed") from exc
