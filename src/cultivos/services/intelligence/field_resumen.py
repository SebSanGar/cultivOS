"""Field Spanish plain-language summary — composes HealthScore, AlertLog, TreatmentRecord."""

from sqlalchemy.orm import Session

from cultivos.db.models import AlertLog, Field, HealthScore, TreatmentRecord

_HEALTH_ADJ = {
    "bueno": "bueno",
    "regular": "regular",
    "malo": "delicado",
    "sin_datos": "sin evaluar",
}

_SEV_ADJ = {
    "alta": "criticas",
    "media": "importantes",
    "baja": "menores",
}

_SEV_TO_URGENCY = {
    "critical": "alta",
    "warning": "media",
    "info": "baja",
    "low": "baja",
}


def _health_status(score: float | None) -> str:
    if score is None:
        return "sin_datos"
    if score >= 70:
        return "bueno"
    if score >= 50:
        return "regular"
    return "malo"


def _urgency_from_alerts(alerts: list[AlertLog]) -> str:
    if not alerts:
        return "ninguna"
    severities = {_SEV_TO_URGENCY.get(a.severity, "baja") for a in alerts}
    for level in ("alta", "media", "baja"):
        if level in severities:
            return level
    return "ninguna"


def _sentence_next_step(health_status: str, pending: TreatmentRecord | None) -> str:
    if pending is not None:
        return f"Siguiente paso: {pending.tratamiento}."
    if health_status == "malo":
        return "Siguiente paso: revisar el campo."
    return "Siguiente paso: continuar monitoreo."


def compute_field_resumen(field: Field, db: Session) -> dict:
    """Return dict with field_name, health_status, urgency, summary_es."""
    latest_health = (
        db.query(HealthScore)
        .filter(HealthScore.field_id == field.id)
        .order_by(HealthScore.scored_at.desc())
        .first()
    )
    score = latest_health.score if latest_health else None
    health_status = _health_status(score)

    open_alerts = (
        db.query(AlertLog)
        .filter(
            AlertLog.field_id == field.id,
            AlertLog.acknowledged == False,  # noqa: E712
        )
        .all()
    )
    urgency = _urgency_from_alerts(open_alerts)

    pending_treatment = (
        db.query(TreatmentRecord)
        .filter(
            TreatmentRecord.field_id == field.id,
            TreatmentRecord.applied_at.is_(None),
        )
        .order_by(TreatmentRecord.created_at.desc())
        .first()
    )

    s1 = f"El campo {field.name} esta en estado {_HEALTH_ADJ[health_status]}."
    if urgency != "ninguna":
        s2 = f"Hay {len(open_alerts)} alerta(s) {_SEV_ADJ[urgency]} sin atender."
    else:
        s2 = "No hay problemas urgentes."
    s3 = _sentence_next_step(health_status, pending_treatment)

    return {
        "field_name": field.name,
        "health_status": health_status,
        "urgency": urgency,
        "summary_es": f"{s1} {s2} {s3}",
    }
