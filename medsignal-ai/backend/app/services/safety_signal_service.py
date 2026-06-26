from collections import Counter
from datetime import date, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.adverse_event import AdverseEvent
from app.models.safety_alert import SafetyAlert

POTENTIAL_SIGNAL_ALERT_TYPE = "potential_safety_signal"


def get_safety_alerts(drug_id: int, db: Session) -> list[SafetyAlert]:
    return list(
        db.scalars(
            select(SafetyAlert)
            .where(SafetyAlert.drug_id == drug_id)
            .order_by(SafetyAlert.created_at.desc(), SafetyAlert.id.desc())
        )
    )


def detect_and_save_potential_safety_signals(
    drug_id: int,
    db: Session,
    recent_window_days: int = 90,
    percent_increase_threshold: float = 100.0,
    min_current_count: int = 3,
) -> list[SafetyAlert]:
    events = list(
        db.scalars(
            select(AdverseEvent).where(
                AdverseEvent.drug_id == drug_id,
                AdverseEvent.reaction.is_not(None),
                AdverseEvent.report_date.is_not(None),
            )
        )
    )
    alerts = detect_potential_safety_signals(
        drug_id=drug_id,
        events=events,
        recent_window_days=recent_window_days,
        percent_increase_threshold=percent_increase_threshold,
        min_current_count=min_current_count,
    )

    db.execute(delete(SafetyAlert).where(SafetyAlert.drug_id == drug_id))
    db.add_all(alerts)
    db.commit()
    for alert in alerts:
        db.refresh(alert)
    return alerts


def detect_potential_safety_signals(
    drug_id: int,
    events: list[AdverseEvent],
    recent_window_days: int = 90,
    percent_increase_threshold: float = 100.0,
    min_current_count: int = 3,
) -> list[SafetyAlert]:
    dated_events = [event for event in events if event.report_date is not None]
    if not dated_events:
        return []

    anchor_date = max(event.report_date for event in dated_events)
    if anchor_date is None:
        return []
    recent_start = anchor_date - timedelta(days=recent_window_days)

    recent_counts = _reaction_counts(
        event for event in dated_events if event.report_date >= recent_start
    )
    baseline_counts = _reaction_counts(
        event for event in dated_events if event.report_date < recent_start
    )

    alerts: list[SafetyAlert] = []
    for reaction, current_count in recent_counts.items():
        if current_count < min_current_count:
            continue

        baseline_count = baseline_counts.get(reaction, 0)
        percent_change = _percent_change(baseline_count, current_count)
        if percent_change < percent_increase_threshold:
            continue

        alerts.append(
            SafetyAlert(
                drug_id=drug_id,
                alert_type=POTENTIAL_SIGNAL_ALERT_TYPE,
                reaction=reaction,
                baseline_count=baseline_count,
                current_count=current_count,
                percent_change=percent_change,
                message=_build_potential_signal_message(
                    reaction, baseline_count, current_count, percent_change
                ),
            )
        )

    return sorted(alerts, key=lambda alert: alert.percent_change, reverse=True)


def _reaction_counts(events) -> Counter[str]:
    return Counter(event.reaction for event in events if event.reaction)


def _percent_change(baseline_count: int, current_count: int) -> float:
    if baseline_count == 0:
        return 100.0
    return round(((current_count - baseline_count) / baseline_count) * 100.0, 2)


def _build_potential_signal_message(
    reaction: str,
    baseline_count: int,
    current_count: int,
    percent_change: float,
) -> str:
    return (
        f"Potential safety signal: reports mentioning this medication and "
        f"{reaction} increased from {baseline_count} baseline reports to "
        f"{current_count} recent reports ({percent_change:.2f}% change). "
        "This is a reporting signal for review, not a confirmed drug risk."
    )
