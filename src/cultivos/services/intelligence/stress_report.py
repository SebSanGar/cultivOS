"""Field stress report — multi-sensor unified stress index.

Pure service: accepts field ORM object + DB session, queries latest data from
each source (health, NDVI, thermal, soil), computes a composite stress score.

Stress score formula:
  base      = 100 - health_score  (or 50 if no health data)
  +15       if thermal irrigation_deficit=True or stress_pct >= 40%
  +10       if NDVI mean < 0.4
  +10       if soil pH < 5.5 or pH > 7.5
  clamped to [0, 100]

Stress levels:
  0-25  → low      (priority 1)
  26-50 → medium   (priority 2-3)
  51-75 → high     (priority 4)
  76+   → critical (priority 5)
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from cultivos.db.models import Field, HealthScore, NDVIResult, ThermalResult, SoilAnalysis


def _latest(db: Session, model, field_id: int):
    """Return the most recent record for a given model and field."""
    return (
        db.query(model)
        .filter(model.field_id == field_id)
        .order_by(model.created_at.desc())
        .first()
    )


def compute_field_stress_report(field: Field, db: Session) -> dict:
    """Build a stress report for a single field.

    Returns a dict with keys:
        field_id, field_name, stress_score, stress_level, contributing_factors, recommended_priority
    """
    factors: list[dict] = []
    score: float = 0.0

    # --- Health score (base) ---
    health = _latest(db, HealthScore, field.id)
    if health is not None:
        base = 100.0 - health.score
        score += base
        factors.append({
            "source": "health",
            "metric": "health_score",
            "value": health.score,
            "impact": round(base),
        })
    else:
        score += 50.0  # unknown → assume medium

    # --- Thermal stress ---
    thermal = _latest(db, ThermalResult, field.id)
    if thermal is not None:
        thermal_stressed = thermal.irrigation_deficit or (thermal.stress_pct >= 40.0)
        if thermal_stressed:
            score += 15.0
            factors.append({
                "source": "thermal",
                "metric": "irrigation_deficit" if thermal.irrigation_deficit else "stress_pct",
                "value": float(thermal.irrigation_deficit) if thermal.irrigation_deficit else thermal.stress_pct,
                "impact": 15,
            })

    # --- NDVI ---
    ndvi = _latest(db, NDVIResult, field.id)
    if ndvi is not None and ndvi.ndvi_mean < 0.4:
        score += 10.0
        factors.append({
            "source": "ndvi",
            "metric": "ndvi_mean",
            "value": ndvi.ndvi_mean,
            "impact": 10,
        })

    # --- Soil pH ---
    soil = _latest(db, SoilAnalysis, field.id)
    if soil is not None and soil.ph is not None:
        if soil.ph < 5.5 or soil.ph > 7.5:
            score += 10.0
            factors.append({
                "source": "soil",
                "metric": "ph",
                "value": soil.ph,
                "impact": 10,
            })

    # Clamp score
    stress_score = min(score, 100.0)

    # Derive stress level and priority
    if stress_score <= 25:
        stress_level = "low"
        priority = 1
    elif stress_score <= 50:
        stress_level = "medium"
        priority = 3
    elif stress_score <= 75:
        stress_level = "high"
        priority = 4
    else:
        stress_level = "critical"
        priority = 5

    return {
        "field_id": field.id,
        "field_name": field.name,
        "stress_score": round(stress_score, 1),
        "stress_level": stress_level,
        "contributing_factors": factors,
        "recommended_priority": priority,
    }
