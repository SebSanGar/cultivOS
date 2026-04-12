"""Cooperative annual report aggregate service.

Composes per-farm compute_annual_report across every farm in a cooperative.
Adds farm-level health_delta (mean of per-field last-first delta in the year),
then aggregates: avg_health_change, total_co2e_sequestered_t, total_treatments,
best_farm by health_delta, and farms_improved_count.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, HealthScore
from cultivos.services.intelligence.annual_report import compute_annual_report


def _farm_health_delta(farm_id: int, year: int, db: Session) -> Optional[float]:
    """Mean of per-field (last - first) HealthScore delta within the year.

    Returns None when no field has at least two scores in the year.
    """
    year_start = datetime(year, 1, 1)
    year_end = datetime(year, 12, 31, 23, 59, 59)
    fields = db.query(Field).filter(Field.farm_id == farm_id).all()
    deltas: list[float] = []
    for field in fields:
        rows = (
            db.query(HealthScore.score)
            .filter(
                HealthScore.field_id == field.id,
                HealthScore.scored_at >= year_start,
                HealthScore.scored_at <= year_end,
            )
            .order_by(HealthScore.scored_at.asc())
            .all()
        )
        if len(rows) >= 2:
            deltas.append(rows[-1].score - rows[0].score)
    if not deltas:
        return None
    return sum(deltas) / len(deltas)


def compute_coop_annual_report(coop_id: int, year: int, db: Session) -> dict:
    farms = (
        db.query(Farm)
        .filter(Farm.cooperative_id == coop_id)
        .order_by(Farm.id)
        .all()
    )

    total_fields = 0
    total_co2e = 0.0
    total_treatments = 0
    deltas_for_avg: list[float] = []
    farms_improved = 0
    best_farm: Optional[dict] = None
    best_delta: Optional[float] = None

    for farm in farms:
        report = compute_annual_report(farm, year, db)
        # total_fields counts every field in the coop's farms
        field_count = db.query(Field).filter(Field.farm_id == farm.id).count()
        total_fields += field_count
        total_co2e += float(report.get("total_co2e_sequestered_t") or 0.0)
        total_treatments += int(report.get("treatments_applied_total") or 0)

        delta = _farm_health_delta(farm.id, year, db)
        if delta is not None:
            deltas_for_avg.append(delta)
            if delta > 0:
                farms_improved += 1
            if best_delta is None or delta > best_delta:
                best_delta = delta
                best_farm = {
                    "farm_id": farm.id,
                    "farm_name": farm.name,
                    "health_delta": round(delta, 2),
                }

    avg_health_change = (
        round(sum(deltas_for_avg) / len(deltas_for_avg), 2) if deltas_for_avg else 0.0
    )

    return {
        "cooperative_id": coop_id,
        "year": year,
        "total_farms": len(farms),
        "total_fields": total_fields,
        "avg_health_change": avg_health_change,
        "total_co2e_sequestered_t": round(total_co2e, 2),
        "total_treatments_applied": total_treatments,
        "best_farm": best_farm,
        "farms_improved_count": farms_improved,
        "farms_total": len(farms),
    }
