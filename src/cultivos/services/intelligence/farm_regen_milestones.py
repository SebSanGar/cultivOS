"""Farm regenerative milestone tracker service.

Computes 8 milestones across a farm's history:
    1. first_organic_treatment       — first TreatmentRecord with organic=True
    2. first_compost_application     — first TreatmentRecord with 'compost' in tratamiento
    3. first_cover_crop              — first TEKAdoption or TreatmentRecord with cover-crop keyword
    4. first_carbon_baseline         — first CarbonBaseline recorded for any field
    5. reached_regen_score_60        — first month where monthly regen_score >= 60
    6. reached_regen_score_80        — first month where monthly regen_score >= 80
    7. maintained_regen_score_70_for_6_months — 6 consecutive months with regen_score >= 70
    8. (reserved for 8th slot below)

regen_score per month = organic_treatment_pct * 0.6 + avg_health_score * 0.4
(matches regen_trajectory service — single source of truth)

Returns ordered list so the "next" milestone is the first unachieved entry.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from cultivos.db.models import (
    CarbonBaseline,
    Farm,
    Field,
    HealthScore,
    TEKAdoption,
    TreatmentRecord,
)

_COMPOST_KEYWORDS = ("compost", "composta", "bocashi", "lombricomposta", "humus")
_COVER_CROP_KEYWORDS = ("cobertura", "cover crop", "cubierta vegetal", "abono verde")

# Canonical milestone order — defines the "next" suggestion sequence.
_MILESTONE_ORDER = [
    ("first_organic_treatment",
     "Primer tratamiento orgánico aplicado en la finca."),
    ("first_compost_application",
     "Primera aplicación de composta registrada."),
    ("first_cover_crop",
     "Primer cultivo de cobertura adoptado."),
    ("first_carbon_baseline",
     "Primera medición de carbono del suelo (línea base)."),
    ("reached_regen_score_60",
     "Mes con puntaje regenerativo de al menos 60 alcanzado."),
    ("reached_regen_score_80",
     "Mes con puntaje regenerativo de al menos 80 alcanzado."),
    ("maintained_regen_score_70_for_6_months",
     "Puntaje regenerativo >= 70 mantenido durante 6 meses consecutivos."),
]


def compute_farm_regen_milestones(farm_id: int, db: Session) -> Optional[dict]:
    farm = db.query(Farm).filter(Farm.id == farm_id).one_or_none()
    if farm is None:
        return None

    field_ids = [f.id for f in db.query(Field.id).filter(Field.farm_id == farm_id).all()]

    achieved: dict[str, Optional[datetime]] = {name: None for name, _ in _MILESTONE_ORDER}

    # ── Treatment-based milestones ────────────────────────────────────────────
    if field_ids:
        treatments = (
            db.query(TreatmentRecord)
            .filter(TreatmentRecord.field_id.in_(field_ids))
            .order_by(TreatmentRecord.created_at.asc())
            .all()
        )
    else:
        treatments = []

    for t in treatments:
        text = (t.tratamiento or "").lower()
        if achieved["first_organic_treatment"] is None and t.organic:
            achieved["first_organic_treatment"] = t.created_at
        if achieved["first_compost_application"] is None and any(k in text for k in _COMPOST_KEYWORDS):
            achieved["first_compost_application"] = t.created_at
        if achieved["first_cover_crop"] is None and any(k in text for k in _COVER_CROP_KEYWORDS):
            achieved["first_cover_crop"] = t.created_at

    # ── Cover crop from TEK adoptions (overrides or fills) ────────────────────
    tek = (
        db.query(TEKAdoption)
        .filter(TEKAdoption.farm_id == farm_id)
        .order_by(TEKAdoption.adopted_at.asc())
        .all()
    )
    for a in tek:
        mn = (a.method_name or "").lower()
        if any(k in mn for k in _COVER_CROP_KEYWORDS):
            if achieved["first_cover_crop"] is None or (
                a.adopted_at and achieved["first_cover_crop"] and a.adopted_at < achieved["first_cover_crop"]
            ):
                achieved["first_cover_crop"] = a.adopted_at
            break

    # ── Carbon baseline ───────────────────────────────────────────────────────
    if field_ids:
        cb = (
            db.query(CarbonBaseline)
            .filter(CarbonBaseline.field_id.in_(field_ids))
            .order_by(CarbonBaseline.recorded_at.asc())
            .first()
        )
        if cb is not None:
            achieved["first_carbon_baseline"] = cb.recorded_at

    # ── Monthly regen scores → threshold/maintenance milestones ───────────────
    monthly_scores = _compute_monthly_regen_scores(field_ids, db)

    first_60: Optional[datetime] = None
    first_80: Optional[datetime] = None
    first_70_sustained: Optional[datetime] = None

    for month_key, score in monthly_scores:
        if first_60 is None and score >= 60:
            first_60 = _month_key_to_dt(month_key)
        if first_80 is None and score >= 80:
            first_80 = _month_key_to_dt(month_key)

    # 6 consecutive months >= 70
    run_start: Optional[str] = None
    run_len = 0
    for month_key, score in monthly_scores:
        if score >= 70:
            if run_len == 0:
                run_start = month_key
            run_len += 1
            if run_len >= 6:
                first_70_sustained = _month_key_to_dt(month_key)
                break
        else:
            run_len = 0
            run_start = None

    achieved["reached_regen_score_60"] = first_60
    achieved["reached_regen_score_80"] = first_80
    achieved["maintained_regen_score_70_for_6_months"] = first_70_sustained

    # ── Build ordered milestone list ──────────────────────────────────────────
    milestones = []
    next_name: Optional[str] = None
    next_desc: Optional[str] = None
    achieved_count = 0
    for name, desc in _MILESTONE_ORDER:
        dt = achieved.get(name)
        is_done = dt is not None
        if is_done:
            achieved_count += 1
        if not is_done and next_name is None:
            next_name = name
            next_desc = desc
        milestones.append({
            "name": name,
            "achieved": is_done,
            "achieved_at": dt,
            "description_es": desc,
        })

    total = len(_MILESTONE_ORDER)
    progress_pct = round((achieved_count / total) * 100.0, 2) if total else 0.0
    next_es = next_desc if next_desc else "Todos los hitos alcanzados."

    return {
        "farm_id": farm_id,
        "milestones": milestones,
        "milestones_achieved_count": achieved_count,
        "next_milestone_es": next_es,
        "progress_to_next_pct": progress_pct,
    }


def _compute_monthly_regen_scores(field_ids: list[int], db: Session) -> list[tuple[str, float]]:
    """Return [(YYYY-MM, regen_score), ...] sorted ascending."""
    if not field_ids:
        return []

    health_by_month: dict[str, list[float]] = defaultdict(list)
    for scored_at, score in (
        db.query(HealthScore.scored_at, HealthScore.score)
        .filter(HealthScore.field_id.in_(field_ids))
        .all()
    ):
        if scored_at is not None:
            health_by_month[scored_at.strftime("%Y-%m")].append(score)

    treatment_by_month: dict[str, dict] = defaultdict(lambda: {"total": 0, "organic": 0})
    for created_at, organic in (
        db.query(TreatmentRecord.created_at, TreatmentRecord.organic)
        .filter(TreatmentRecord.field_id.in_(field_ids))
        .all()
    ):
        if created_at is not None:
            key = created_at.strftime("%Y-%m")
            treatment_by_month[key]["total"] += 1
            if organic:
                treatment_by_month[key]["organic"] += 1

    # Require health data for the month — a regen score with zero health signal
    # is misleading (a single organic treatment would instantly score 60).
    months = sorted(health_by_month.keys())
    result = []
    for m in months:
        health_scores = health_by_month[m]
        avg_health = sum(health_scores) / len(health_scores)
        t = treatment_by_month.get(m, {"total": 0, "organic": 0})
        organic_pct = (t["organic"] / t["total"] * 100.0) if t["total"] > 0 else 0.0
        regen_score = organic_pct * 0.6 + avg_health * 0.4
        result.append((m, regen_score))
    return result


def _month_key_to_dt(month_key: str) -> datetime:
    """Convert 'YYYY-MM' → datetime at the first of that month."""
    return datetime.strptime(month_key + "-01", "%Y-%m-%d")
