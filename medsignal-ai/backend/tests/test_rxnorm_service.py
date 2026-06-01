import httpx
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.drug import Drug
from app.services import rxnorm_service
from app.services.rxnorm_service import (
    RxNormNotFoundError,
    RxNormTimeoutError,
    RxNormUpstreamError,
    search_and_save_drug,
)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("GET", "https://rxnav.nlm.nih.gov")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError(
                "RxNorm failed", request=request, response=response
            )

    def json(self):
        return self.payload


class FakeClient:
    def __init__(self, responses=None, exception=None, timeout=None):
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
        return self.responses.pop(0)


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


def test_search_and_save_drug_creates_drug(monkeypatch, db_session):
    responses = [
        FakeResponse({"idGroup": {"rxnormId": ["202433"]}}),
        FakeResponse(
            {
                "properties": {
                    "rxcui": "202433",
                    "name": "Tylenol",
                    "synonym": "acetaminophen",
                    "tty": "BN",
                }
            }
        ),
    ]
    monkeypatch.setattr(rxnorm_service.httpx, "Client", lambda timeout: FakeClient(responses))

    drug = search_and_save_drug(" Tylenol ", db_session)

    assert drug.id is not None
    assert drug.rxcui == "202433"
    assert drug.input_name == "Tylenol"
    assert drug.normalized_name == "Tylenol"
    assert drug.synonym == "acetaminophen"
    assert drug.tty == "BN"


def test_search_and_save_drug_updates_existing_drug(monkeypatch, db_session):
    existing_drug = Drug(
        rxcui="202433",
        input_name="old",
        normalized_name="old",
        synonym=None,
        tty=None,
    )
    db_session.add(existing_drug)
    db_session.commit()

    responses = [
        FakeResponse({"idGroup": {"rxnormId": ["202433"]}}),
        FakeResponse(
            {
                "properties": {
                    "rxcui": "202433",
                    "name": "Tylenol",
                    "synonym": "acetaminophen",
                    "tty": "BN",
                }
            }
        ),
    ]
    monkeypatch.setattr(rxnorm_service.httpx, "Client", lambda timeout: FakeClient(responses))

    drug = search_and_save_drug("Tylenol", db_session)
    drugs = db_session.scalars(select(Drug)).all()

    assert drug.id == existing_drug.id
    assert len(drugs) == 1
    assert drug.normalized_name == "Tylenol"


def test_search_and_save_drug_raises_not_found(monkeypatch, db_session):
    responses = [FakeResponse({"idGroup": {}})]
    monkeypatch.setattr(rxnorm_service.httpx, "Client", lambda timeout: FakeClient(responses))

    with pytest.raises(RxNormNotFoundError):
        search_and_save_drug("not-a-drug", db_session)


def test_search_and_save_drug_raises_upstream_error(monkeypatch, db_session):
    responses = [FakeResponse({}, status_code=500)]
    monkeypatch.setattr(rxnorm_service.httpx, "Client", lambda timeout: FakeClient(responses))

    with pytest.raises(RxNormUpstreamError):
        search_and_save_drug("Tylenol", db_session)


def test_search_and_save_drug_raises_timeout(monkeypatch, db_session):
    monkeypatch.setattr(
        rxnorm_service.httpx,
        "Client",
        lambda timeout: FakeClient(exception=httpx.TimeoutException("timeout")),
    )

    with pytest.raises(RxNormTimeoutError):
        search_and_save_drug("Tylenol", db_session)
