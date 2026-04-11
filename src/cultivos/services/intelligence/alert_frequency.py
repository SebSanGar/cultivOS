"""Alert frequency analysis service.

For each field on a farm, analyses the last 6 months of Alert records:
- monthly_avg: total alerts in window / 6
- dominant_type: most frequent alert_type in the window (None if no alerts)
- trend: compares last-2-month count vs prior-2-month count
    increasing  — last 2 months > prior 2 months
    decreasing  — last 2 months < prior 2 months
    stable      — equal (or no alerts in either window)

overall_alert_load: mean of per-field monthly_avg values.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from cultivos.db.models import Alert, Farm, Field


_WINDOW_MONTHS = 6
_WINDOW_DAYS = _WINDOW_MONTHS * 30  # 180 days


def compute_alert_frequency(farm: Farm, db: Session) -> dict:
    """Return alert frequency metrics for every field on the farm."""
    fields: list[Field] = (
        db.query(Field)
        .filter(Field.farm_id == farm.id)
        .order_by(Field.id)
        .all()
    )

    now = datetime.utcnow()
    window_start = now - timedelta(days=_WINDOW_DAYS)
    # Boundary between "last 2 months" and "prior 2 months"
    recent_boundary = now - timedelta(days=60)
    prior_boundary = now - timedelta(days=120)

    field_items: list[dict] = []

    for field in fields:
        alerts_in_window: list[Alert] = (
            db.query(Alert)
            .filter(
                Alert.field_id == field.id,
                Alert.sent_at >= window_start,
            )
            .all()
        )

        total = len(alerts_in_window)
        monthly_avg = round(total / _WINDOW_MONTHS, 2)

        # Dominant type
        if total == 0:
            dominant_type = None
        else:
            counter = Counter(a.alert_type for a in alerts_in_window)
            dominant_type = counter.most_common(1)[0][0]

        # Trend: last 2 months vs prior 2 months
        last_2m = sum(1 for a in alerts_in_window if a.sent_at >= recent_boundary)
        prior_2m = sum(
            1 for a in alerts_in_window
            if prior_boundary <= a.sent_at < recent_boundary
        )

        if last_2m > prior_2m:
            trend = "increasing"
        elif last_2m < prior_2m:
            trend = "decreasing"
        else:
            trend = "stable"

        field_items.append({
            "field_id": field.id,
            "field_name": field.name,
            "monthly_avg": monthly_avg,
            "dominant_type": dominant_type,
            "trend": trend,
        })

    overall_alert_load = (
        round(sum(f["monthly_avg"] for f in field_items) / len(field_items), 2)
        if field_items
        else 0.0
    )

    return {
        "farm_id": farm.id,
        "fields": field_items,
        "overall_alert_load": overall_alert_load,
    }
