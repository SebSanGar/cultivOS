"""Alert escalation backlog service.

Lists alerts that have been active >=3 days on the farm's fields without a
corresponding TreatmentRecord applied after the alert was sent. Used to
surface the actionability gap in the alert→treatment loop for FODECIJAL.

Severity is derived from alert_type (Alert table has no severity column);
recommended_action_es is a static Spanish guidance string per alert_type.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from cultivos.db.models import Alert, Farm, Field, TreatmentRecord


_MIN_DAYS_PENDING = 3


_SEVERITY_BY_TYPE: dict[str, str] = {
    "low_health": "critical",
    "anomaly_health_drop": "critical",
    "pest": "high",
    "disease": "high",
    "anomaly_ndvi_drop": "high",
    "irrigation": "medium",
    "weather": "medium",
}


_ACTION_BY_TYPE: dict[str, str] = {
    "low_health": "Revisar cultivo urgente: aplicar compost o te de humus y programar riego.",
    "anomaly_health_drop": "Caida brusca de salud: inspeccionar plagas y suelo, aplicar tratamiento organico.",
    "pest": "Inspeccionar plaga y aplicar control biologico (ajo, chile, aceite de neem).",
    "disease": "Remover hojas afectadas y aplicar tratamiento organico (cobre natural, caldo sulfocalcico).",
    "anomaly_ndvi_drop": "Verificar estres del cultivo: NDVI bajo indica problema en hojas o riego.",
    "irrigation": "Programar riego inmediato segun recomendacion de eficiencia hidrica.",
    "weather": "Proteger cultivo ante alerta climatica y revisar estado del campo.",
}


def _severity_for(alert_type: str) -> str:
    return _SEVERITY_BY_TYPE.get(alert_type, "medium")


def _action_for(alert_type: str) -> str:
    return _ACTION_BY_TYPE.get(
        alert_type,
        "Revisar la alerta y registrar una intervencion en el campo.",
    )


def compute_alert_escalations(farm: Farm, db: Session, days: int = 30) -> dict:
    """Return escalation backlog for alerts >=3 days old without treatment."""
    now = datetime.utcnow()
    window_start = now - timedelta(days=days)

    alerts = (
        db.query(Alert)
        .filter(
            Alert.farm_id == farm.id,
            Alert.sent_at != None,  # noqa: E711
            Alert.sent_at >= window_start,
        )
        .all()
    )

    escalations: list[dict] = []
    for alert in alerts:
        days_pending = (now - alert.sent_at).days
        if days_pending < _MIN_DAYS_PENDING:
            continue

        treated = (
            db.query(TreatmentRecord)
            .filter(
                TreatmentRecord.field_id == alert.field_id,
                TreatmentRecord.applied_at != None,  # noqa: E711
                TreatmentRecord.applied_at > alert.sent_at,
            )
            .first()
        )
        if treated is not None:
            continue

        field = db.query(Field).filter(Field.id == alert.field_id).first()
        field_name = field.name if field else f"Field {alert.field_id}"

        escalations.append(
            {
                "alert_id": alert.id,
                "field_id": alert.field_id,
                "field_name": field_name,
                "alert_type": alert.alert_type,
                "message": alert.message,
                "days_pending": days_pending,
                "severity": _severity_for(alert.alert_type),
                "recommended_action_es": _action_for(alert.alert_type),
            }
        )

    escalations.sort(key=lambda e: (-e["days_pending"], e["alert_id"]))

    return {
        "farm_id": farm.id,
        "days": days,
        "total": len(escalations),
        "escalations": escalations,
    }
