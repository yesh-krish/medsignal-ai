from pydantic import BaseModel

from app.schemas.adverse_event import EventTrends, ReactionCount
from app.schemas.drug import DrugSearchResult
from app.schemas.drug_label import DrugLabelRead


class ComparedDrug(BaseModel):
    drug: DrugSearchResult
    trends: EventTrends
    label: DrugLabelRead | None


class SharedReaction(BaseModel):
    reaction: str
    left_count: int
    right_count: int
    absolute_difference: int


class LabelSectionComparison(BaseModel):
    section: str
    left_available: bool
    right_available: bool
    left_count: int
    right_count: int


class DrugComparisonResponse(BaseModel):
    left: ComparedDrug
    right: ComparedDrug
    shared_top_reported_reactions: list[SharedReaction]
    label_section_comparison: list[LabelSectionComparison]
    disclaimer: str
