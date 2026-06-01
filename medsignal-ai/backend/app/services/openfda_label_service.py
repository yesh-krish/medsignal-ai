from typing import Any

import httpx
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.drug_label import DrugLabel


class OpenFDALabelUpstreamError(Exception):
    pass


class OpenFDALabelTimeoutError(Exception):
    pass


def fetch_and_save_drug_label(
    normalized_drug_name: str,
    drug_id: int,
    db: Session,
) -> DrugLabel | None:
    cleaned_name = normalized_drug_name.strip()
    if not cleaned_name:
        raise ValueError("Normalized drug name must not be empty")

    results = _query_openfda_label(cleaned_name)
    label_json = _choose_best_label(results, cleaned_name)
    if label_json is None:
        db.execute(delete(DrugLabel).where(DrugLabel.drug_id == drug_id))
        db.commit()
        return None

    db.execute(delete(DrugLabel).where(DrugLabel.drug_id == drug_id))
    label = DrugLabel(
        drug_id=drug_id,
        set_id=_clean_string(label_json.get("set_id")),
        brand_name=_string_list(label_json.get("openfda", {}).get("brand_name")),
        generic_name=_string_list(label_json.get("openfda", {}).get("generic_name")),
        warnings=_string_list(label_json.get("warnings")),
        adverse_reactions=_string_list(label_json.get("adverse_reactions")),
        contraindications=_string_list(label_json.get("contraindications")),
        indications_and_usage=_string_list(label_json.get("indications_and_usage")),
        boxed_warning=_string_list(label_json.get("boxed_warning")),
        raw_label_json=label_json,
    )
    db.add(label)
    db.commit()
    db.refresh(label)
    return label


def get_saved_drug_label(drug_id: int, db: Session) -> DrugLabel | None:
    return db.scalar(select(DrugLabel).where(DrugLabel.drug_id == drug_id))


def _query_openfda_label(normalized_drug_name: str) -> list[dict[str, Any]]:
    settings = get_settings()
    try:
        with httpx.Client(timeout=settings.openfda_timeout_seconds) as client:
            response = client.get(
                f"{settings.openfda_base_url}/drug/label.json",
                params={
                    "search": (
                        f'openfda.brand_name:"{normalized_drug_name}" '
                        f'openfda.generic_name:"{normalized_drug_name}"'
                    ),
                    "limit": "10",
                },
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException as exc:
        raise OpenFDALabelTimeoutError("openFDA label request timed out") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise OpenFDALabelUpstreamError("openFDA label request failed") from exc

    return data.get("results", [])


def _choose_best_label(
    results: list[dict[str, Any]], normalized_drug_name: str
) -> dict[str, Any] | None:
    if not results:
        return None

    normalized = normalized_drug_name.casefold()

    def score(label: dict[str, Any]) -> int:
        openfda = label.get("openfda") or {}
        names = _string_list(openfda.get("brand_name")) or []
        names.extend(_string_list(openfda.get("generic_name")) or [])
        name_score = 20 if any(name.casefold() == normalized for name in names) else 0
        section_score = sum(
            1
            for field in (
                "boxed_warning",
                "warnings",
                "adverse_reactions",
                "contraindications",
                "indications_and_usage",
            )
            if _string_list(label.get(field))
        )
        return name_score + section_score

    return max(results, key=score)


def _string_list(value: Any) -> list[str] | None:
    if value is None:
        return None
    values = value if isinstance(value, list) else [value]
    cleaned_values = [_clean_string(item) for item in values]
    result = [item for item in cleaned_values if item is not None]
    return result or None


def _clean_string(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None
