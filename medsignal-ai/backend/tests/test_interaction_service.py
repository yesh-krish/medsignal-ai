import httpx
import pytest

from app.models.drug import Drug
from app.models.medication_list import MedicationList, MedicationListItem
from app.services import interaction_service
from app.services.interaction_service import screen_medication_list_interactions


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("GET", "https://api.fda.gov")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError(
                "openFDA failed", request=request, response=response
            )

    def json(self):
        return self.payload


class FakeClient:
    def __init__(self, responses=None, exception=None, timeout=None):
        self.responses = responses if responses is not None else []
        self.exception = exception
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def get(self, url, params=None):
        if self.exception is not None:
            raise self.exception
        if not self.responses:
            return FakeResponse({}, status_code=404)
        return self.responses.pop(0)


def test_screen_medication_list_interactions_matches_openfda_label_text(
    monkeypatch,
):
    medication_list = MedicationList(id=1, name="My medications")
    medication_list.items = [
        make_item(1, "11289", "warfarin"),
        make_item(2, "5640", "ibuprofen"),
    ]
    payload = {
        "results": [
            {
                "drug_interactions": [
                    (
                        "Use caution with NSAIDs and other nonsteroidal "
                        "anti-inflammatory drugs in patients taking warfarin."
                    )
                ]
            }
        ]
    }
    rxclass_payload = {
        "rxclassDrugInfoList": {
            "rxclassDrugInfo": [
                    {
                        "rxclassMinConceptItem": {
                            "classType": "VA",
                            "className": "Nonsteroidal Anti-inflammatory Agents"
                        }
                    }
            ]
        }
    }
    responses = [
        FakeResponse({}),
        FakeResponse(rxclass_payload),
        FakeResponse(payload),
        FakeResponse({}, status_code=404),
        FakeResponse({}, status_code=404),
        FakeResponse({}, status_code=404),
    ]
    monkeypatch.setattr(
        interaction_service.httpx,
        "Client",
        lambda timeout: FakeClient(responses),
    )

    result = screen_medication_list_interactions(medication_list)

    assert result["checked_rxcuis"] == ["11289", "5640"]
    assert len(result["interactions"]) == 1
    interaction = result["interactions"][0]
    assert interaction["source"] == "openFDA drug label"
    assert interaction["severity"] == "Tier 1: Critical pharmacodynamic risk"
    assert interaction["severity_tier"] == "tier_1_contraindicated_critical"
    assert interaction["mechanism"] == "pharmacodynamic"
    assert interaction["risk_category"] == "severe_gastrointestinal_hemorrhage"
    assert "Pharmacodynamic risk takes priority" in interaction["assessment_reason"]
    assert "FDA label drug interaction guidance was found" in interaction["description"]
    assert "RxClass terminology" in interaction["explanation"]
    assert "anti-inflammatory" in interaction["evidence"][0]["excerpt"]
    assert interaction["evidence"][0]["source_drug_name"] == "warfarin"
    assert interaction["evidence"][0]["matched_drug_name"] == "ibuprofen"
    assert interaction["evidence"][0]["matched_term"] in {
        "anti-inflammatory",
        "nonsteroidal",
    }
    assert interaction["evidence"][0]["match_type"] == "RxClass class match"
    assert interaction["evidence"][0]["risk_statement"] is None
    assert {drug["name"] for drug in interaction["drugs"]} == {
        "warfarin",
        "ibuprofen",
    }
    assert "doctor or pharmacist" in result["disclaimer"]


def test_screen_medication_list_interactions_returns_label_guidance_without_pair_match(
    monkeypatch,
):
    medication_list = MedicationList(id=1, name="My medications")
    medication_list.items = [
        make_item(1, "11289", "warfarin"),
        make_item(2, "5640", "ibuprofen"),
    ]
    payload = {
        "results": [
            {
                "drug_interactions": [
                    (
                        "Review all prescription and over-the-counter medicines "
                        "with a healthcare professional before use."
                    )
                ]
            }
        ]
    }
    responses = [
        FakeResponse({}),
        FakeResponse({}),
        FakeResponse(payload),
        FakeResponse({}, status_code=404),
        FakeResponse({}, status_code=404),
        FakeResponse({}, status_code=404),
    ]
    monkeypatch.setattr(
        interaction_service.httpx,
        "Client",
        lambda timeout: FakeClient(responses),
    )

    result = screen_medication_list_interactions(medication_list)

    assert len(result["interactions"]) == 1
    interaction = result["interactions"][0]
    assert interaction["mechanism"] == "unknown"
    assert interaction["severity_tier"] == "tier_3_moderate_adjust"
    assert interaction["drugs"] == [{"rxcui": "11289", "name": "warfarin"}]
    assert "did not explicitly name another medication" in interaction["description"]
    assert interaction["evidence"][0]["match_type"] == "general label guidance"
    assert "Review all prescription" in interaction["evidence"][0]["excerpt"]


def test_screen_medication_list_interactions_merges_bidirectional_pair_evidence(
    monkeypatch,
):
    medication_list = MedicationList(id=1, name="My medications")
    medication_list.items = [
        make_item(1, "5489", "hydrocodone"),
        make_item(2, "596", "alprazolam"),
    ]
    hydrocodone_label = {
        "results": [
            {
                "drug_interactions": [
                    "Concomitant use of benzodiazepines may cause profound sedation."
                ]
            }
        ]
    }
    alprazolam_label = {
        "results": [
            {
                "drug_interactions": [
                    "Use with opioids increases the risk of respiratory depression."
                ]
            }
        ]
    }
    hydrocodone_class = {
        "rxclassDrugInfoList": {
            "rxclassDrugInfo": [
                {
                    "rxclassMinConceptItem": {
                        "classType": "VA",
                        "className": "Opioid Analgesics",
                    }
                }
            ]
        }
    }
    alprazolam_class = {
        "rxclassDrugInfoList": {
            "rxclassDrugInfo": [
                {
                    "rxclassMinConceptItem": {
                        "classType": "VA",
                        "className": "Benzodiazepines",
                    }
                }
            ]
        }
    }
    responses = [
        FakeResponse(hydrocodone_class),
        FakeResponse(alprazolam_class),
        FakeResponse(hydrocodone_label),
        FakeResponse(alprazolam_label),
    ]
    monkeypatch.setattr(
        interaction_service.httpx,
        "Client",
        lambda timeout: FakeClient(responses),
    )

    result = screen_medication_list_interactions(medication_list)

    assert len(result["interactions"]) == 1
    interaction = result["interactions"][0]
    assert interaction["severity_tier"] == "tier_1_contraindicated_critical"
    assert interaction["mechanism"] == "pharmacodynamic"
    assert interaction["risk_category"] == "cns_respiratory_depression"
    assert {drug["name"] for drug in interaction["drugs"]} == {
        "hydrocodone",
        "alprazolam",
    }
    assert len(interaction["evidence"]) == 2
    assert {evidence["source_drug_name"] for evidence in interaction["evidence"]} == {
        "hydrocodone",
        "alprazolam",
    }
    matched_terms = {evidence["matched_term"] for evidence in interaction["evidence"]}
    assert matched_terms == {"opioid + benzodiazepine"}
    risk_statements = {
        evidence["risk_statement"] for evidence in interaction["evidence"]
    }
    assert any(
        statement and "profound sedation" in statement
        for statement in risk_statements
    )
    assert any(
        statement and "respiratory depression" in statement
        for statement in risk_statements
    )


def test_screen_medication_list_interactions_skips_upstream_with_fewer_than_two_rxcuis(
    monkeypatch,
):
    medication_list = MedicationList(id=1, name="My medications")
    medication_list.items = [make_item(1, "161", "Acetaminophen")]

    def fail_if_called(timeout):
        raise AssertionError("openFDA should not be called for fewer than two RxCUIs")

    monkeypatch.setattr(interaction_service.httpx, "Client", fail_if_called)

    result = screen_medication_list_interactions(medication_list)

    assert result["checked_rxcuis"] == ["161"]
    assert result["interactions"] == []


def test_screen_medication_list_interactions_timeout(monkeypatch):
    medication_list = MedicationList(id=1, name="My medications")
    medication_list.items = [
        make_item(1, "161", "Acetaminophen"),
        make_item(2, "5640", "Ibuprofen"),
    ]
    monkeypatch.setattr(
        interaction_service.httpx,
        "Client",
        lambda timeout: FakeClient(exception=httpx.TimeoutException("timeout")),
    )

    with pytest.raises(interaction_service.InteractionTimeoutError):
        screen_medication_list_interactions(medication_list)


def make_item(item_id: int, rxcui: str, name: str) -> MedicationListItem:
    return MedicationListItem(
        id=item_id,
        medication_list_id=1,
        drug_id=item_id,
        drug=Drug(
            id=item_id,
            rxcui=rxcui,
            input_name=name,
            normalized_name=name,
            synonym=None,
            tty="IN",
        ),
    )
