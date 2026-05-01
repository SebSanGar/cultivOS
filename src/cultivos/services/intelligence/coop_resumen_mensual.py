"""Cooperative 30-day monthly summary in Spanish — WhatsApp-ready."""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from cultivos.db.models import (
    AlertLog, Cooperative, Farm, Field, HealthScore, TreatmentRecord,
)

PERIOD_DAYS = 30


def compute_coop_resumen_mensual(
    cooperative: Cooperative, db: Session, *, _now: Optional[datetime] = None,
) -> dict:
    now = _now or datetime.utcnow()
    cutoff = now - timedelta(days=PERIOD_DAYS)

    farms = db.query(Farm).filter(Farm.cooperative_id == cooperative.id).all()

    if not farms:
        return {
            "coop_name": cooperative.name,
            "total_farms": 0,
            "total_fields": 0,
            "period_days": PERIOD_DAYS,
            "avg_health_change": None,
            "total_treatments": 0,
            "total_alerts": 0,
            "resumen_es": f"{cooperative.name}: sin fincas miembro registradas.",
        }

    farm_ids = [f.id for f in farms]
    field_rows = db.query(Field).filter(Field.farm_id.in_(farm_ids)).all()
    field_ids = [fld.id for fld in field_rows]
    total_fields = len(field_ids)

    total_treatments = 0
    total_alerts = 0
    health_deltas = []

    if field_ids:
        total_treatments = (
            db.query(func.count(TreatmentRecord.id))
            .filter(
                TreatmentRecord.field_id.in_(field_ids),
                TreatmentRecord.created_at >= cutoff,
            )
            .scalar()
        ) or 0

        total_alerts = (
            db.query(func.count(AlertLog.id))
            .filter(
                AlertLog.field_id.in_(field_ids),
                AlertLog.created_at >= cutoff,
            )
            .scalar()
        ) or 0

        for fid in field_ids:
            scores = (
                db.query(HealthScore)
                .filter(
                    HealthScore.field_id == fid,
                    HealthScore.scored_at >= cutoff,
                )
                .order_by(HealthScore.scored_at.asc())
                .all()
            )
            if len(scores) >= 2:
                health_deltas.append(scores[-1].score - scores[0].score)

    avg_health_change = None
    if health_deltas:
        avg_health_change = round(sum(health_deltas) / len(health_deltas), 1)

    resumen = _build_resumen(
        cooperative.name, len(farms), total_fields,
        avg_health_change, total_treatments, total_alerts,
    )

    return {
        "coop_name": cooperative.name,
        "total_farms": len(farms),
        "total_fields": total_fields,
        "period_days": PERIOD_DAYS,
        "avg_health_change": avg_health_change,
        "total_treatments": total_treatments,
        "total_alerts": total_alerts,
        "resumen_es": resumen,
    }


def _build_resumen(
    name: str, farms: int, fields: int,
    health_change: Optional[float], treatments: int, alerts: int,
) -> str:
    base = f"{name}: {farms} finca(s), {fields} campo(s) en 30 días."

    parts = []
    if health_change is not None:
        if health_change > 0:
            parts.append(f"Salud promedio mejoró +{health_change} pts")
        elif health_change < 0:
            parts.append(f"Salud promedio bajó {health_change} pts")
        else:
            parts.append("Salud promedio estable")

    if treatments > 0:
        parts.append(f"{treatments} tratamiento(s) aplicado(s)")

    if alerts > 0:
        parts.append(f"{alerts} alerta(s) generada(s)")

    if not parts:
        resumen = f"{base} Sin actividad registrada."
    else:
        resumen = f"{base} {'. '.join(parts)}."

    if len(resumen) > 300:
        resumen = resumen[:297] + "..."

    return resumen
