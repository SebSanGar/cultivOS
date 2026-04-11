"""Service: farmer feedback trend.

Groups FarmerFeedback by month for the last 6 months, computes avg rating
and entry count per month. Returns overall trend direction based on
the last 2 months vs the prior 2 months.
"""

from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from cultivos.db.models import Farm, FarmerFeedback, Field
from cultivos.models.feedback_trend import FeedbackMonthItem, FeedbackTrendOut


def compute_feedback_trend(farm: Farm, db: Session) -> FeedbackTrendOut:
    """Return monthly feedback trend for a farm over the last 6 months."""
    cutoff = datetime.utcnow() - timedelta(days=183)  # ~6 months

    # Get all field IDs for this farm
    field_ids = [
        row[0]
        for row in db.query(Field.id).filter(Field.farm_id == farm.id).all()
    ]

    if not field_ids:
        return FeedbackTrendOut(
            farm_id=farm.id, months=[], overall_trend="stable"
        )

    # Fetch feedback in last 6 months for this farm's fields
    records = (
        db.query(FarmerFeedback)
        .filter(
            FarmerFeedback.field_id.in_(field_ids),
            FarmerFeedback.created_at >= cutoff,
        )
        .all()
    )

    if not records:
        return FeedbackTrendOut(
            farm_id=farm.id, months=[], overall_trend="stable"
        )

    # Group by YYYY-MM
    groups: dict[str, list[int]] = defaultdict(list)
    for fb in records:
        label = fb.created_at.strftime("%Y-%m")
        groups[label].append(fb.rating)

    # Build sorted month items
    months = [
        FeedbackMonthItem(
            month_label=label,
            avg_rating=round(sum(ratings) / len(ratings), 2),
            entry_count=len(ratings),
        )
        for label, ratings in sorted(groups.items())
    ]

    overall_trend = _compute_trend(months)

    return FeedbackTrendOut(
        farm_id=farm.id,
        months=months,
        overall_trend=overall_trend,
    )


def _compute_trend(months: list[FeedbackMonthItem]) -> str:
    """Compare last 2 months avg vs prior 2 months avg. Threshold: 0.2."""
    if len(months) < 4:
        return "stable"

    recent = months[-2:]
    prior = months[-4:-2]

    recent_avg = sum(m.avg_rating for m in recent) / len(recent)
    prior_avg = sum(m.avg_rating for m in prior) / len(prior)

    delta = recent_avg - prior_avg
    if delta > 0.2:
        return "improving"
    if delta < -0.2:
        return "declining"
    return "stable"
