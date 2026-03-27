"""SMS alert service — format messages and deduplication logic.

Pure functions for message formatting. DB-aware function for dedup check.
Actual SMS sending (Twilio) is stubbed until API key is configured.
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from cultivos.db.models import Alert

HEALTH_THRESHOLD = 40  # score below this triggers alert


def format_sms_message(
    farm_name: str,
    field_name: str,
    alert_type: str,
    score: float,
) -> str:
    """Format an SMS alert message in Spanish.

    Returns a concise Spanish-language message suitable for basic phones (160 char SMS).
    """
    if alert_type == "low_health":
        return (
            f"[cultivOS] Alerta de salud: {field_name} en {farm_name} "
            f"tiene puntuacion {score:.0f}/100. "
            f"Revise su parcela lo antes posible."
        )
    return (
        f"[cultivOS] Alerta: {field_name} en {farm_name} "
        f"requiere atencion. Puntuacion: {score:.0f}/100."
    )


def format_irrigation_sms(
    farm_name: str,
    field_name: str,
    urgencia: str,
    liters_per_ha: float,
    crop_type: str,
) -> str:
    """Format an irrigation SMS alert in farmer-friendly Spanish.

    Urgency levels: alta (act now), media (plan today), baja (informational).
    """
    liters_str = f"{liters_per_ha:.0f}"

    if urgencia == "alta":
        return (
            f"[cultivOS] {field_name} en {farm_name}: "
            f"su {crop_type} necesita riego urgente. "
            f"Regar hoy {liters_str} litros/ha, temprano antes de 8am."
        )
    elif urgencia == "media":
        return (
            f"[cultivOS] {field_name} en {farm_name}: "
            f"programe riego de {liters_str} litros/ha para {crop_type} esta semana."
        )
    return (
        f"[cultivOS] {field_name} en {farm_name}: "
        f"riego normal de {liters_str} litros/ha para {crop_type}."
    )


def format_anomaly_sms(
    farm_name: str,
    field_name: str,
    anomaly_type: str,
    recommendation: str,
) -> str:
    """Format an anomaly alert SMS in farmer-friendly Spanish."""
    if anomaly_type == "health_drop":
        return (
            f"[cultivOS] {field_name} en {farm_name}: "
            f"{recommendation}"
        )
    elif anomaly_type == "ndvi_drop":
        return (
            f"[cultivOS] {field_name} en {farm_name}: "
            f"{recommendation}"
        )
    return (
        f"[cultivOS] {field_name} en {farm_name}: "
        f"anomalia detectada. Revise su parcela."
    )


def should_send_alert(
    db: Session,
    farm_id: int,
    field_id: int,
    alert_type: str,
) -> bool:
    """Check if an alert of this type was already sent within 24 hours.

    Returns True if no duplicate exists (safe to send), False otherwise.
    """
    cutoff = datetime.utcnow() - timedelta(hours=24)
    existing = (
        db.query(Alert)
        .filter(
            Alert.farm_id == farm_id,
            Alert.field_id == field_id,
            Alert.alert_type == alert_type,
            Alert.sent_at >= cutoff,
        )
        .first()
    )
    return existing is None
