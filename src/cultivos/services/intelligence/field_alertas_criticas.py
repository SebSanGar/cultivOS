"""Field critical/high alert list in Spanish — voice-ready."""

from sqlalchemy.orm import Session

from cultivos.db.models import AlertLog, Field

_ALERT_TYPE_ES = {
    "health": "salud",
    "irrigation": "riego",
    "pest": "plaga",
    "recommendation": "recomendación",
}

_SEVERITY_ES = {
    "critical": "crítica",
    "high": "alta",
}


def compute_alertas_criticas(field: Field, db: Session) -> dict:
    alerts = (
        db.query(AlertLog)
        .filter(
            AlertLog.field_id == field.id,
            AlertLog.severity.in_(["critical", "high"]),
            AlertLog.acknowledged == False,
        )
        .order_by(AlertLog.created_at.desc())
        .all()
    )

    items = []
    for a in alerts:
        tipo = _ALERT_TYPE_ES.get(a.alert_type, a.alert_type)
        sev = _SEVERITY_ES.get(a.severity, a.severity)
        mensaje = f"Alerta de {tipo} ({sev}): {a.message}"
        items.append({
            "alert_id": a.id,
            "severity": a.severity,
            "mensaje_es": mensaje,
        })

    return {
        "field_name": field.name,
        "total": len(items),
        "alertas": items,
    }
