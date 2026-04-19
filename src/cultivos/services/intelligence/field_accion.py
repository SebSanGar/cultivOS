"""Field one-sentence Spanish next-action — ranks AlertLog > TreatmentRecord > HealthScore."""

from sqlalchemy.orm import Session

from cultivos.db.models import AlertLog, Field, HealthScore, TreatmentRecord

_ALERT_SEVERITY_RANK = {"critical": 3, "warning": 2, "low": 1, "info": 1}


def _alert_priority_source_accion(alert: AlertLog) -> tuple[str, str, str]:
    sev = alert.severity
    if sev == "critical":
        return "alta", "alert", f"Atender alerta critica: {alert.message}."
    if sev == "warning":
        return "media", "alert", f"Atender alerta: {alert.message}."
    return "baja", "alert", f"Revisar alerta: {alert.message}."


def _treatment_priority(urgencia: str | None) -> str:
    if urgencia == "alta":
        return "alta"
    if urgencia == "baja":
        return "baja"
    return "media"


def compute_field_accion(field: Field, db: Session) -> dict:
    """Return dict with field_name, priority, source, accion_es."""
    open_alerts = (
        db.query(AlertLog)
        .filter(
            AlertLog.field_id == field.id,
            AlertLog.acknowledged == False,  # noqa: E712
        )
        .all()
    )
    if open_alerts:
        best = max(
            open_alerts,
            key=lambda a: (
                _ALERT_SEVERITY_RANK.get(a.severity, 0),
                a.created_at or 0,
            ),
        )
        priority, source, accion_es = _alert_priority_source_accion(best)
        return {
            "field_name": field.name,
            "priority": priority,
            "source": source,
            "accion_es": accion_es,
        }

    pending_treatment = (
        db.query(TreatmentRecord)
        .filter(
            TreatmentRecord.field_id == field.id,
            TreatmentRecord.applied_at.is_(None),
        )
        .order_by(TreatmentRecord.created_at.desc())
        .first()
    )
    if pending_treatment is not None:
        return {
            "field_name": field.name,
            "priority": _treatment_priority(pending_treatment.urgencia),
            "source": "treatment",
            "accion_es": f"Aplicar tratamiento: {pending_treatment.tratamiento}.",
        }

    latest_health = (
        db.query(HealthScore)
        .filter(HealthScore.field_id == field.id)
        .order_by(HealthScore.scored_at.desc())
        .first()
    )
    if latest_health is not None:
        score = latest_health.score
        if score < 50:
            score_int = int(round(score))
            return {
                "field_name": field.name,
                "priority": "media",
                "source": "health",
                "accion_es": f"Revisar el campo: salud baja ({score_int}/100).",
            }
        if score < 70:
            return {
                "field_name": field.name,
                "priority": "baja",
                "source": "monitoring",
                "accion_es": "Monitorear el campo: salud regular.",
            }

    return {
        "field_name": field.name,
        "priority": "ninguna",
        "source": "monitoring",
        "accion_es": "No hay acciones urgentes. Continuar monitoreo.",
    }
