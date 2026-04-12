"""Field crop calendar event log service.

Composes HealthScore + TreatmentRecord + FarmerObservation + AncestralMethod
into a 12-month timeline of event counts for a single field in a given year.
TEK practices are counted per month when the field's crop_type appears in the
method's `crops` list AND the month is listed in `applicable_months`.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import extract
from sqlalchemy.orm import Session

from cultivos.db.models import (
    AncestralMethod,
    FarmerObservation,
    Field,
    HealthScore,
    TreatmentRecord,
)


_MONTH_NAMES_ES = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]


def _count_by_month(db: Session, model, timestamp_col, field_id: int, year: int) -> dict[int, int]:
    rows = (
        db.query(extract("month", timestamp_col), timestamp_col)
        .filter(model.field_id == field_id)
        .filter(timestamp_col != None)  # noqa: E711
        .filter(extract("year", timestamp_col) == year)
        .all()
    )
    counts: dict[int, int] = {m: 0 for m in range(1, 13)}
    for month_val, _ in rows:
        if month_val is None:
            continue
        m = int(month_val)
        if 1 <= m <= 12:
            counts[m] += 1
    return counts


def _tek_counts(db: Session, crop_type: str | None) -> dict[int, int]:
    counts: dict[int, int] = {m: 0 for m in range(1, 13)}
    if not crop_type:
        return counts
    methods = (
        db.query(AncestralMethod)
        .filter(AncestralMethod.applicable_months != None)  # noqa: E711
        .all()
    )
    for method in methods:
        crops = method.crops or []
        if crop_type not in crops:
            continue
        months = method.applicable_months or []
        for m in months:
            try:
                mi = int(m)
            except (TypeError, ValueError):
                continue
            if 1 <= mi <= 12:
                counts[mi] += 1
    return counts


def compute_field_calendar(field: Field, db: Session, year: int) -> dict:
    health_counts = _count_by_month(db, HealthScore, HealthScore.scored_at, field.id, year)
    treat_counts = _count_by_month(db, TreatmentRecord, TreatmentRecord.applied_at, field.id, year)
    obs_counts = _count_by_month(db, FarmerObservation, FarmerObservation.created_at, field.id, year)
    tek_counts = _tek_counts(db, field.crop_type)

    months: list[dict] = []
    total_events = 0
    busiest_month: int | None = None
    busiest_total = 0

    for m in range(1, 13):
        hs = health_counts[m]
        tr = treat_counts[m]
        ob = obs_counts[m]
        tk = tek_counts[m]
        month_total = hs + tr + ob + tk
        total_events += month_total
        if month_total > busiest_total:
            busiest_total = month_total
            busiest_month = m
        months.append(
            {
                "month": m,
                "month_name_es": _MONTH_NAMES_ES[m - 1],
                "health_scores": hs,
                "treatments": tr,
                "observations": ob,
                "tek_practices": tk,
                "total_events": month_total,
            }
        )

    return {
        "farm_id": field.farm_id,
        "field_id": field.id,
        "year": year,
        "crop_type": field.crop_type,
        "months": months,
        "total_events": total_events,
        "busiest_month": busiest_month if busiest_total > 0 else None,
    }
