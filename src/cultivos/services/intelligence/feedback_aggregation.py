"""Aggregate farmer feedback into per-treatment trust scores."""

from collections import defaultdict
from typing import Optional

from sqlalchemy.orm import Session

from cultivos.db.models import FarmerFeedback, Field, TreatmentRecord


def aggregate_treatment_trust(
    db: Session,
    crop_type: Optional[str] = None,
    field_id: Optional[int] = None,
) -> list[dict]:
    """Aggregate all farmer feedback grouped by treatment name.

    Returns a list of dicts sorted by trust_score descending, each with:
    - treatment_name, total_feedback, positive_count, negative_count,
      average_rating, trust_score, top_farmer_note
    """
    query = (
        db.query(FarmerFeedback, TreatmentRecord)
        .join(TreatmentRecord, FarmerFeedback.treatment_id == TreatmentRecord.id)
    )

    if crop_type:
        query = query.join(Field, FarmerFeedback.field_id == Field.id).filter(
            Field.crop_type == crop_type
        )

    if field_id:
        query = query.filter(FarmerFeedback.field_id == field_id)

    rows = query.all()
    if not rows:
        return []

    # Group by treatment name
    groups: dict[str, list[FarmerFeedback]] = defaultdict(list)
    for feedback, treatment in rows:
        groups[treatment.tratamiento].append(feedback)

    results = []
    for treatment_name, feedbacks in groups.items():
        total = len(feedbacks)
        positive = sum(1 for f in feedbacks if f.worked)
        negative = total - positive
        avg_rating = sum(f.rating for f in feedbacks) / total

        # Trust score: worked ratio (60%) + normalized rating (40%)
        positive_ratio = positive / total
        rating_normalized = (avg_rating - 1) / 4  # 1-5 -> 0-1
        trust_score = round((positive_ratio * 0.6 + rating_normalized * 0.4) * 100, 1)

        # Pick the most descriptive farmer note
        notes = [f.farmer_notes for f in feedbacks if f.farmer_notes]
        top_note = max(notes, key=len) if notes else None

        results.append({
            "treatment_name": treatment_name,
            "total_feedback": total,
            "positive_count": positive,
            "negative_count": negative,
            "average_rating": round(avg_rating, 2),
            "trust_score": trust_score,
            "top_farmer_note": top_note,
        })

    results.sort(key=lambda t: t["trust_score"], reverse=True)
    return results
