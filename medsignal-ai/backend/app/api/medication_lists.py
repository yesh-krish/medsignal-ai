from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.drug import Drug
from app.models.medication_list import MedicationList, MedicationListItem
from app.schemas.interaction import InteractionScreeningResponse
from app.schemas.medication_list import MedicationListItemCreate, MedicationListRead
from app.services import interaction_service

router = APIRouter(prefix="/api/medication-lists", tags=["medication lists"])

DEFAULT_LIST_NAME = "My medications"


@router.get("/default", response_model=MedicationListRead)
def get_default_medication_list(db: Session = Depends(get_db)) -> MedicationList:
    return _get_or_create_default_list(db)


@router.post(
    "/default/items",
    response_model=MedicationListRead,
    status_code=status.HTTP_201_CREATED,
)
def add_default_medication_list_item(
    item: MedicationListItemCreate,
    db: Session = Depends(get_db),
) -> MedicationList:
    medication_list = _get_or_create_default_list(db)
    drug = db.get(Drug, item.drug_id)
    if drug is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drug not found",
        )

    db.add(
        MedicationListItem(
            medication_list_id=medication_list.id,
            drug_id=drug.id,
        )
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()

    return _load_list(medication_list.id, db)


@router.delete("/default/items/{item_id}", response_model=MedicationListRead)
def remove_default_medication_list_item(
    item_id: int,
    db: Session = Depends(get_db),
) -> MedicationList:
    medication_list = _get_or_create_default_list(db)
    list_item = db.scalar(
        select(MedicationListItem).where(
            MedicationListItem.id == item_id,
            MedicationListItem.medication_list_id == medication_list.id,
        )
    )
    if list_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication list item not found",
        )

    db.delete(list_item)
    db.commit()
    return _load_list(medication_list.id, db)


@router.get(
    "/default/interactions",
    response_model=InteractionScreeningResponse,
)
def screen_default_medication_list_interactions(
    db: Session = Depends(get_db),
) -> InteractionScreeningResponse:
    medication_list = _get_or_create_default_list(db)
    try:
        return interaction_service.screen_medication_list_interactions(
            medication_list
        )
    except interaction_service.InteractionTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="openFDA label interaction request timed out",
        ) from exc
    except interaction_service.InteractionUpstreamError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="openFDA label interaction request failed",
        ) from exc


def _get_or_create_default_list(db: Session) -> MedicationList:
    medication_list = db.scalar(
        select(MedicationList).where(MedicationList.name == DEFAULT_LIST_NAME)
    )
    if medication_list is None:
        medication_list = MedicationList(name=DEFAULT_LIST_NAME)
        db.add(medication_list)
        db.commit()
        db.refresh(medication_list)
    return _load_list(medication_list.id, db)


def _load_list(medication_list_id: int, db: Session) -> MedicationList:
    medication_list = db.scalar(
        select(MedicationList)
        .options(selectinload(MedicationList.items).selectinload(MedicationListItem.drug))
        .where(MedicationList.id == medication_list_id)
    )
    if medication_list is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication list not found",
        )
    medication_list.items.sort(key=lambda item: item.created_at)
    return medication_list
