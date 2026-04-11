"""Field intervention timeline service.

Collects all events for a field in chronological order:
health score recordings, NDVI measurements, treatments applied, alerts triggered.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy.orm import Session

from cultivos.db.models import Alert, Field, HealthScore, NDVIResult, TreatmentRecord


def _to_dt(d: date) -> datetime:
    return datetime(d.year, d.month, d.day)


def compute_field_timeline(
    field: Field,
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> dict:
    """Return all events for a field sorted chronologically."""
    start_dt = _to_dt(start_date) if start_date else None
    end_dt = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59) if end_date else None

    events: list[dict] = []

    # ── Health scores ──────────────────────────────────────────────────────────
    hs_q = db.query(HealthScore).filter(HealthScore.field_id == field.id)
    if start_dt:
        hs_q = hs_q.filter(HealthScore.scored_at >= start_dt)
    if end_dt:
        hs_q = hs_q.filter(HealthScore.scored_at <= end_dt)
    for h in hs_q.all():
        events.append({
            "event_type": "health_score",
            "date": h.scored_at.isoformat() if h.scored_at else "",
            "summary_es": f"Puntuacion de salud: {h.score:.0f}/100",
            "value": h.score,
            "_sort_dt": h.scored_at,
        })

    # ── NDVI results ───────────────────────────────────────────────────────────
    ndvi_q = db.query(NDVIResult).filter(NDVIResult.field_id == field.id)
    if start_dt:
        ndvi_q = ndvi_q.filter(NDVIResult.analyzed_at >= start_dt)
    if end_dt:
        ndvi_q = ndvi_q.filter(NDVIResult.analyzed_at <= end_dt)
    for n in ndvi_q.all():
        events.append({
            "event_type": "ndvi",
            "date": n.analyzed_at.isoformat() if n.analyzed_at else "",
            "summary_es": f"NDVI medido: {n.ndvi_mean:.3f}",
            "value": n.ndvi_mean,
            "_sort_dt": n.analyzed_at,
        })

    # ── Treatment records ──────────────────────────────────────────────────────
    treat_q = db.query(TreatmentRecord).filter(TreatmentRecord.field_id == field.id)
    if start_dt:
        treat_q = treat_q.filter(TreatmentRecord.created_at >= start_dt)
    if end_dt:
        treat_q = treat_q.filter(TreatmentRecord.created_at <= end_dt)
    for t in treat_q.all():
        events.append({
            "event_type": "treatment",
            "date": t.created_at.isoformat() if t.created_at else "",
            "summary_es": t.tratamiento,
            "value": float(t.costo_estimado_mxn) if t.costo_estimado_mxn is not None else None,
            "_sort_dt": t.created_at,
        })

    # ── Alerts ─────────────────────────────────────────────────────────────────
    alert_q = db.query(Alert).filter(Alert.field_id == field.id)
    if start_dt:
        alert_q = alert_q.filter(Alert.sent_at >= start_dt)
    if end_dt:
        alert_q = alert_q.filter(Alert.sent_at <= end_dt)
    for a in alert_q.all():
        events.append({
            "event_type": "alert",
            "date": a.sent_at.isoformat() if a.sent_at else "",
            "summary_es": a.message,
            "value": None,
            "_sort_dt": a.sent_at,
        })

    # ── Sort ASC by date ───────────────────────────────────────────────────────
    events.sort(key=lambda e: e["_sort_dt"] or datetime.min)

    # Strip internal sort key before returning
    for e in events:
        del e["_sort_dt"]

    return {"field_id": field.id, "events": events}
