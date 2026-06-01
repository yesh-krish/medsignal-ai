import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.services import openfda_label_service
from app.services.openfda_label_service import (
    OpenFDALabelTimeoutError,
    OpenFDALabelUpstreamError,
    fetch_and_save_drug_label,
)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("GET", "https://api.fda.gov/drug/label.json")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError(
                "openFDA label failed", request=request, response=response
            )

    def json(self):
        return self.payload


class FakeClient:
    def __init__(self, response=None, exception=None, timeout=None):
        self.response = response
        self.exception = exception
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def get(self, url, params=None):
        if self.exception is not None:
            raise self.exception
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


def test_fetch_and_save_drug_label(monkeypatch, db_session):
    label_result = {
        "set_id": "label-set-id",
        "openfda": {
            "brand_name": ["Tylenol"],
            "generic_name": ["Acetaminophen"],
        },
        "warnings": ["Liver warning"],
        "boxed_warning": ["Serious warning"],
        "adverse_reactions": ["Rash"],
        "contraindications": ["Known allergy"],
        "indications_and_usage": ["Pain relief"],
    }
    response = FakeResponse({"results": [label_result]})
    monkeypatch.setattr(
        openfda_label_service.httpx,
        "Client",
        lambda timeout: FakeClient(response=response),
    )

    label = fetch_and_save_drug_label("Tylenol", 1, db_session)

    assert label is not None
    assert label.drug_id == 1
    assert label.set_id == "label-set-id"
    assert label.brand_name == ["Tylenol"]
    assert label.generic_name == ["Acetaminophen"]
    assert label.warnings == ["Liver warning"]
    assert label.boxed_warning == ["Serious warning"]
    assert label.adverse_reactions == ["Rash"]
    assert label.contraindications == ["Known allergy"]
    assert label.indications_and_usage == ["Pain relief"]
    assert label.raw_label_json["set_id"] == "label-set-id"


def test_fetch_and_save_drug_label_handles_missing_sections(monkeypatch, db_session):
    response = FakeResponse(
        {
            "results": [
                {
                    "set_id": "partial-label",
                    "openfda": {"brand_name": ["Tylenol"]},
                }
            ]
        }
    )
    monkeypatch.setattr(
        openfda_label_service.httpx,
        "Client",
        lambda timeout: FakeClient(response=response),
    )

    label = fetch_and_save_drug_label("Tylenol", 1, db_session)

    assert label is not None
    assert label.brand_name == ["Tylenol"]
    assert label.generic_name is None
    assert label.warnings is None
    assert label.boxed_warning is None
    assert label.adverse_reactions is None
    assert label.contraindications is None
    assert label.indications_and_usage is None


def test_fetch_and_save_drug_label_empty_results(monkeypatch, db_session):
    response = FakeResponse({"results": []})
    monkeypatch.setattr(
        openfda_label_service.httpx,
        "Client",
        lambda timeout: FakeClient(response=response),
    )

    label = fetch_and_save_drug_label("Tylenol", 1, db_session)

    assert label is None


def test_fetch_and_save_drug_label_handles_openfda_404(monkeypatch, db_session):
    response = FakeResponse({}, status_code=404)
    monkeypatch.setattr(
        openfda_label_service.httpx,
        "Client",
        lambda timeout: FakeClient(response=response),
    )

    label = fetch_and_save_drug_label("Tylenol", 1, db_session)

    assert label is None


def test_fetch_and_save_drug_label_upstream_failure(monkeypatch, db_session):
    response = FakeResponse({}, status_code=500)
    monkeypatch.setattr(
        openfda_label_service.httpx,
        "Client",
        lambda timeout: FakeClient(response=response),
    )

    with pytest.raises(OpenFDALabelUpstreamError):
        fetch_and_save_drug_label("Tylenol", 1, db_session)


def test_fetch_and_save_drug_label_timeout(monkeypatch, db_session):
    monkeypatch.setattr(
        openfda_label_service.httpx,
        "Client",
        lambda timeout: FakeClient(exception=httpx.TimeoutException("timeout")),
    )

    with pytest.raises(OpenFDALabelTimeoutError):
        fetch_and_save_drug_label("Tylenol", 1, db_session)
