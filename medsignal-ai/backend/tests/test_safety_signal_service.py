from datetime import date

from app.models.adverse_event import AdverseEvent
from app.services.safety_signal_service import detect_potential_safety_signals


def make_event(reaction: str, report_date: date) -> AdverseEvent:
    return AdverseEvent(
        drug_id=1,
        reaction=reaction,
        serious=False,
        outcome=None,
        report_date=report_date,
        patient_age=None,
        patient_sex=None,
        raw_event_json={},
    )


def test_detects_potential_safety_signal_from_recent_increase():
    events = [
        make_event("Nausea", date(2024, 1, 1)),
        make_event("Nausea", date(2024, 10, 1)),
        make_event("Nausea", date(2024, 10, 2)),
        make_event("Nausea", date(2024, 10, 3)),
    ]

    alerts = detect_potential_safety_signals(
        drug_id=1,
        events=events,
        recent_window_days=90,
        percent_increase_threshold=100.0,
        min_current_count=3,
    )

    assert len(alerts) == 1
    assert alerts[0].reaction == "Nausea"
    assert alerts[0].baseline_count == 1
    assert alerts[0].current_count == 3
    assert alerts[0].percent_change == 200.0
    assert alerts[0].alert_type == "potential_safety_signal"
    assert "Potential safety signal" in alerts[0].message
    assert "not a confirmed drug risk" in alerts[0].message


def test_ignores_small_recent_counts():
    events = [
        make_event("Headache", date(2024, 1, 1)),
        make_event("Headache", date(2024, 10, 1)),
        make_event("Headache", date(2024, 10, 2)),
    ]

    alerts = detect_potential_safety_signals(
        drug_id=1,
        events=events,
        recent_window_days=90,
        percent_increase_threshold=100.0,
        min_current_count=3,
    )

    assert alerts == []


def test_returns_no_alerts_without_dated_events():
    alerts = detect_potential_safety_signals(drug_id=1, events=[])

    assert alerts == []
