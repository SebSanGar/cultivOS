"""Field 7-day Spanish trajectory — composes HealthScore + AlertLog + TreatmentRecord into trend narrative."""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from cultivos.db.models import AlertLog, Field, HealthScore, TreatmentRecord


def _classify_trend(delta: float | None) -> str:
    if delta is None:
        return "sin_datos"
    if delta >= 2:
        return "mejorando"
    if delta <= -2:
        return "empeorando"
    return "estable"


def _build_narrativa(trend: str, delta: float | None, alerts_count: int, treatments_count: int) -> str:
    if trend == "sin_datos":
        return "No hay datos suficientes para evaluar la tendencia. Recomendamos registrar mediciones esta semana."
    if trend == "mejorando":
        return (
            f"Tendencia positiva: salud subio {delta:+.0f} puntos en 7 dias. "
            f"{alerts_count} alertas y {treatments_count} tratamientos registrados."
        )
    if trend == "empeorando":
        return (
            f"Atencion: salud bajo {delta:+.0f} puntos en 7 dias. "
            f"{alerts_count} alertas y {treatments_count} tratamientos registrados."
        )
    return (
        f"Estado estable: variacion de {delta:+.0f} puntos en 7 dias. "
        f"{alerts_count} alertas y {treatments_count} tratamientos registrados."
    )


def compute_field_trayectoria(field: Field, db: Session) -> dict:
    """Return dict matching FieldTrayectoriaOut schema."""
    now = datetime.utcnow()
    cutoff = now - timedelta(days=7)

    scores_in_window = (
        db.query(HealthScore)
        .filter(
            HealthScore.field_id == field.id,
            HealthScore.scored_at >= cutoff,
        )
        .order_by(HealthScore.scored_at.asc())
        .all()
    )

    if len(scores_in_window) >= 2:
        oldest = scores_in_window[0].score
        latest = scores_in_window[-1].score
        health_delta = latest - oldest
    else:
        health_delta = None

    alerts_count = (
        db.query(AlertLog)
        .filter(
            AlertLog.field_id == field.id,
            AlertLog.created_at >= cutoff,
        )
        .count()
    )

    treatments_count = (
        db.query(TreatmentRecord)
        .filter(
            TreatmentRecord.field_id == field.id,
            TreatmentRecord.applied_at.isnot(None),
            TreatmentRecord.applied_at >= cutoff,
        )
        .count()
    )

    trend = _classify_trend(health_delta)
    narrativa_es = _build_narrativa(trend, health_delta, alerts_count, treatments_count)

    return {
        "field_name": field.name,
        "days_window": 7,
        "health_delta": health_delta,
        "alerts_count": alerts_count,
        "treatments_count": treatments_count,
        "trend": trend,
        "narrativa_es": narrativa_es,
    }
