"""Alert response effectiveness service.

For each alert sent on the farm's fields, checks whether a HealthScore was
recorded on the same field within 30 days after the alert's sent_at timestamp.
Compares the score before the alert (most recent HealthScore before sent_at)
to the score after (first HealthScore within 30 days after sent_at).

Returns:
    alerts_analyzed       — total alert count for the farm
    alerts_with_followup  — alerts that have a HealthScore within 30 days after
    improvement_rate_pct  — % of alerts_with_followup where score improved
    avg_improvement_pts   — mean (after - before) across alerts with both data points
"""

from __future__ import annotations

from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from cultivos.db.models import Alert, Farm, HealthScore


_FOLLOWUP_WINDOW_DAYS = 30


def compute_alert_effectiveness(farm: Farm, db: Session) -> dict:
    """Compute alert response effectiveness metrics for the farm."""
    alerts = (
        db.query(Alert)
        .filter(Alert.farm_id == farm.id)
        .all()
    )

    alerts_analyzed = len(alerts)
    alerts_with_followup = 0
    improved_count = 0
    deltas: list[float] = []

    for alert in alerts:
        if alert.sent_at is None:
            continue

        window_end = alert.sent_at + timedelta(days=_FOLLOWUP_WINDOW_DAYS)

        # First HealthScore within 30 days after sent_at (follow-up)
        after_row = (
            db.query(HealthScore)
            .filter(
                HealthScore.field_id == alert.field_id,
                HealthScore.scored_at > alert.sent_at,
                HealthScore.scored_at <= window_end,
            )
            .order_by(HealthScore.scored_at.asc())
            .first()
        )

        if after_row is None:
            continue

        alerts_with_followup += 1

        # Most recent HealthScore before sent_at (baseline)
        before_row = (
            db.query(HealthScore)
            .filter(
                HealthScore.field_id == alert.field_id,
                HealthScore.scored_at < alert.sent_at,
            )
            .order_by(HealthScore.scored_at.desc())
            .first()
        )

        if before_row is not None:
            delta = after_row.score - before_row.score
            deltas.append(delta)
            if delta > 0:
                improved_count += 1

    improvement_rate_pct = (
        round(improved_count / alerts_with_followup * 100, 1)
        if alerts_with_followup > 0
        else 0.0
    )
    avg_improvement_pts = (
        round(sum(deltas) / len(deltas), 2)
        if deltas
        else 0.0
    )

    return {
        "farm_id": farm.id,
        "alerts_analyzed": alerts_analyzed,
        "alerts_with_followup": alerts_with_followup,
        "improvement_rate_pct": improvement_rate_pct,
        "avg_improvement_pts": avg_improvement_pts,
    }
