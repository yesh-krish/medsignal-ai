from datetime import date

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.adverse_event import AdverseEvent
from app.models.ingestion_run import IngestionRun
from app.services import openfda_event_service
from app.services.openfda_event_service import (
    OpenFDATimeoutError,
    OpenFDAUpstreamError,
    build_reported_adverse_event_trends,
    extract_reported_adverse_events,
    fetch_and_save_reported_adverse_events,
    fetch_reported_adverse_event_trends,
)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("GET", "https://api.fda.gov/drug/event.json")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError(
                "openFDA failed", request=request, response=response
            )

    def json(self):
        return self.payload


class FakeClient:
    def __init__(self, response=None, responses=None, exception=None, timeout=None):
        self.response = response
        self.responses = responses or []
        self.exception = exception
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def get(self, url, params=None):
        if self.exception is not None:
            raise self.exception
        if self.responses:
            return self.responses.pop(0)
        return self.response


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def sample_openfda_event():
    return {
        "safetyreportid": "10000001",
        "safetyreportversion": "2",
        "receivedate": "20240115",
        "serious": "1",
        "patient": {
            "patientsex": "2",
            "patientonsetage": "45",
            "drug": [{"medicinalproduct": "TYLENOL"}],
            "reaction": [
                {"reactionmeddrapt": "Nausea", "reactionoutcome": "Recovered"},
                {"reactionmeddrapt": "Headache"},
            ],
        },
    }


def test_extract_reported_adverse_events():
    extracted = extract_reported_adverse_events(sample_openfda_event())

    assert len(extracted) == 2
    assert extracted[0].reaction == "Nausea"
    assert extracted[0].outcome == "Recovered"
    assert extracted[0].report_date == date(2024, 1, 15)
    assert extracted[0].serious is True
    assert extracted[0].patient_age == 45
    assert extracted[0].patient_sex == "female"
    assert extracted[0].raw_event_json["safetyreportid"] == "10000001"
    assert extracted[1].reaction == "Headache"


def test_fetch_and_save_reported_adverse_events(monkeypatch, db_session):
    response = FakeResponse({"results": [sample_openfda_event()]})
    monkeypatch.setattr(
        openfda_event_service.httpx,
        "Client",
        lambda timeout: FakeClient(response=response),
    )

    events = fetch_and_save_reported_adverse_events("Tylenol", 1, db_session)

    assert len(events) == 2
    assert events[0].reaction == "Nausea"
    assert events[0].drug_id == 1
    assert events[0].safety_report_id == "10000001"
    assert events[0].case_version == 2
    assert events[0].reaction_index == 0
    assert events[0].raw_event_json["safetyreportid"] == "10000001"

    run = db_session.query(IngestionRun).one()
    assert run.status == "succeeded"
    assert run.fetched_reports == 1
    assert run.saved_reaction_rows == 2


def test_fetch_and_save_reported_adverse_events_empty_results(monkeypatch, db_session):
    response = FakeResponse({"results": []})
    monkeypatch.setattr(
        openfda_event_service.httpx,
        "Client",
        lambda timeout: FakeClient(response=response),
    )

    events = fetch_and_save_reported_adverse_events("Tylenol", 1, db_session)

    assert events == []


def test_fetch_and_save_reported_adverse_events_handles_openfda_404(
    monkeypatch, db_session
):
    response = FakeResponse({}, status_code=404)
    monkeypatch.setattr(
        openfda_event_service.httpx,
        "Client",
        lambda timeout: FakeClient(response=response),
    )

    events = fetch_and_save_reported_adverse_events("Tylenol", 1, db_session)

    assert events == []


def test_fetch_and_save_reported_adverse_events_upstream_failure(
    monkeypatch, db_session
):
    response = FakeResponse({}, status_code=500)
    monkeypatch.setattr(
        openfda_event_service.httpx,
        "Client",
        lambda timeout: FakeClient(response=response),
    )

    with pytest.raises(OpenFDAUpstreamError):
        fetch_and_save_reported_adverse_events("Tylenol", 1, db_session)


def test_fetch_and_save_reported_adverse_events_timeout(monkeypatch, db_session):
    monkeypatch.setattr(
        openfda_event_service.httpx,
        "Client",
        lambda timeout: FakeClient(exception=httpx.TimeoutException("timeout")),
    )

    with pytest.raises(OpenFDATimeoutError):
        fetch_and_save_reported_adverse_events("Tylenol", 1, db_session)

    run = db_session.query(IngestionRun).one()
    assert run.status == "failed"
    assert run.completed_at is not None


def test_build_reported_adverse_event_trends():
    events = [
        AdverseEvent(
            drug_id=1,
            reaction="Nausea",
            serious=True,
            outcome="Recovered",
            report_date=date(2024, 1, 15),
            patient_age=45,
            patient_sex="female",
            raw_event_json={},
        ),
        AdverseEvent(
            drug_id=1,
            reaction="Nausea",
            serious=False,
            outcome=None,
            report_date=date(2023, 3, 1),
            patient_age=None,
            patient_sex="male",
            raw_event_json={},
        ),
    ]

    trends = build_reported_adverse_event_trends(events)

    assert trends["top_reported_reactions"] == [{"reaction": "Nausea", "count": 2}]
    assert trends["reports_by_year"] == {"2023": 1, "2024": 1}
    assert trends["seriousness_breakdown"] == {"serious": 1, "not_serious": 1}
    assert trends["sex_breakdown"] == {"female": 1, "male": 1}
    assert trends["total_reports"] == 2


def test_build_reported_adverse_event_trends_counts_unique_reports():
    events = [
        AdverseEvent(
            drug_id=1,
            reaction="Nausea",
            serious=True,
            outcome="Recovered",
            report_date=date(2024, 1, 15),
            patient_age=45,
            patient_sex="female",
            raw_event_json={"safetyreportid": "10000001"},
        ),
        AdverseEvent(
            drug_id=1,
            reaction="Headache",
            serious=True,
            outcome="Recovered",
            report_date=date(2024, 1, 15),
            patient_age=45,
            patient_sex="female",
            raw_event_json={"safetyreportid": "10000001"},
        ),
    ]

    trends = build_reported_adverse_event_trends(events)

    assert trends["top_reported_reactions"] == [
        {"reaction": "Nausea", "count": 1},
        {"reaction": "Headache", "count": 1},
    ]
    assert trends["reports_by_year"] == {"2024": 1}
    assert trends["seriousness_breakdown"] == {"serious": 1}
    assert trends["sex_breakdown"] == {"female": 1}
    assert trends["total_reports"] == 1


def test_fetch_reported_adverse_event_trends_uses_openfda_counts(monkeypatch):
    responses = [
        FakeResponse({"meta": {"results": {"total": 2}}, "results": [{}]}),
        FakeResponse({"meta": {"results": {"total": 7}}, "results": [{}]}),
        FakeResponse(
            {
                "results": [
                    {"term": "NAUSEA", "count": 5},
                    {"term": "HEADACHE", "count": 2},
                ]
            }
        ),
        FakeResponse(
            {"results": [{"term": "1", "count": 3}, {"term": "2", "count": 4}]}
        ),
        FakeResponse(
            {"results": [{"term": "2", "count": 5}, {"term": "1", "count": 2}]}
        ),
        FakeResponse({"meta": {"results": {"total": 7}}, "results": [{}]}),
    ]
    monkeypatch.setattr(
        openfda_event_service.httpx,
        "Client",
        lambda timeout: FakeClient(responses=responses),
    )

    trends = fetch_reported_adverse_event_trends(
        "Tylenol", start_year=2023, end_year=2024
    )

    assert trends["reports_by_year"] == {"2023": 2, "2024": 7}
    assert trends["top_reported_reactions"] == [
        {"reaction": "NAUSEA", "count": 5},
        {"reaction": "HEADACHE", "count": 2},
    ]
    assert trends["seriousness_breakdown"] == {"serious": 3, "not_serious": 4}
    assert trends["sex_breakdown"] == {"female": 5, "male": 2}
    assert trends["total_reports"] == 7


def test_query_openfda_paginated(monkeypatch):
    responses = [
        FakeResponse(
            {
                "meta": {"last_updated": "2026-06-01"},
                "results": [
                    {"safetyreportid": "1"},
                    {"safetyreportid": "2"},
                ],
            }
        ),
        FakeResponse({"results": [{"safetyreportid": "3"}]}),
    ]
    monkeypatch.setattr(
        openfda_event_service.httpx,
        "Client",
        lambda timeout: FakeClient(responses=responses),
    )

    results, source_last_updated = openfda_event_service._query_openfda_paginated(
        "Tylenol", limit=3, page_size=2
    )

    assert [event["safetyreportid"] for event in results] == ["1", "2", "3"]
    assert source_last_updated == "2026-06-01"


def test_deduplicate_latest_case_versions():
    events = [
        {"safetyreportid": "1", "safetyreportversion": "1"},
        {"safetyreportid": "1", "safetyreportversion": "3"},
        {"safetyreportid": "2", "safetyreportversion": "1"},
    ]

    deduplicated, skipped = openfda_event_service._deduplicate_latest_case_versions(
        events
    )

    assert skipped == 1
    assert len(deduplicated) == 2
    assert deduplicated[0]["safetyreportversion"] == "3"
