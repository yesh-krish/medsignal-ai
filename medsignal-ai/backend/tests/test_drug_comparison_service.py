from app.models.drug import Drug
from app.models.drug_label import DrugLabel
from app.services import drug_comparison_service
from app.services import openfda_event_service, openfda_label_service


def make_drug(drug_id: int, normalized_name: str) -> Drug:
    return Drug(
        id=drug_id,
        rxcui=str(drug_id),
        input_name=normalized_name,
        normalized_name=normalized_name,
        synonym=None,
        tty="IN",
    )


def test_build_drug_comparison(monkeypatch):
    left = make_drug(1, "Acetaminophen")
    right = make_drug(2, "Ibuprofen")

    def fake_trends(normalized_drug_name, start_year=2004, end_year=None):
        assert start_year >= 2004
        if normalized_drug_name == "Acetaminophen":
            return {
                "top_reported_reactions": [
                    {"reaction": "Nausea", "count": 100},
                    {"reaction": "Headache", "count": 50},
                ],
                "reports_by_year": {"2024": 10},
                "seriousness_breakdown": {"serious": 3, "not_serious": 7},
                "sex_breakdown": {"female": 6, "male": 4},
                "total_reports": 10,
            }
        return {
            "top_reported_reactions": [
                {"reaction": "Nausea", "count": 40},
                {"reaction": "Rash", "count": 30},
            ],
            "reports_by_year": {"2024": 8},
            "seriousness_breakdown": {"serious": 2, "not_serious": 6},
            "sex_breakdown": {"female": 5, "male": 3},
            "total_reports": 8,
        }

    def fake_label(normalized_drug_name, drug_id, db):
        return DrugLabel(
            id=drug_id,
            drug_id=drug_id,
            set_id=f"label-{drug_id}",
            brand_name=[normalized_drug_name],
            generic_name=[normalized_drug_name],
            warnings=["Warning"],
            adverse_reactions=None if drug_id == 2 else ["Reaction"],
            contraindications=[],
            indications_and_usage=None,
            boxed_warning=None,
            raw_label_json={},
        )

    monkeypatch.setattr(
        openfda_event_service, "fetch_reported_adverse_event_trends", fake_trends
    )
    monkeypatch.setattr(openfda_label_service, "get_saved_drug_label", lambda *_: None)
    monkeypatch.setattr(openfda_label_service, "fetch_and_save_drug_label", fake_label)

    comparison = drug_comparison_service.build_drug_comparison(left, right, db=None)

    assert comparison["left"]["trends"]["total_reports"] == 10
    assert comparison["right"]["trends"]["total_reports"] == 8
    assert comparison["shared_top_reported_reactions"] == [
        {
            "reaction": "Nausea",
            "left_count": 100,
            "right_count": 40,
            "absolute_difference": 60,
        }
    ]
    label_sections = comparison["label_section_comparison"]
    assert label_sections[0]["section"] == "FDA label warnings"
    assert label_sections[0]["left_available"] is True
    assert label_sections[0]["right_available"] is True
    assert label_sections[1]["left_available"] is True
    assert label_sections[1]["right_available"] is False
    assert "cannot establish which medication is safer" in comparison["disclaimer"]
