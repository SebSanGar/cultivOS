"""WhatsApp-ready farm status message service.

GET /api/farms/{farm_id}/whatsapp-status

Composes a 3-line plain Spanish text message suitable for WhatsApp delivery.
Uses active_alerts_summary to determine alert state.

Message format:
  Line 1: "{farm_name} — {DD/MM/YYYY}"
  Line 2: "Alerta: {top_action_es}" | "Sin alertas activas"
  Line 3: "Accion: Revisar campo y atender urgencia" | "Monitoreo al dia"
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from cultivos.db.models import Farm
from cultivos.services.intelligence.active_alerts_summary import compute_active_alerts_summary

_NO_ALERT_LINE2 = "Sin alertas activas"
_NO_ALERT_LINE3 = "Monitoreo al dia"
_CRITICAL_LINE3 = "Accion: Revisar campo y atender urgencia de inmediato"
_HIGH_LINE3 = "Accion: Monitorear de cerca y preparar tratamiento preventivo"


def compute_whatsapp_status(farm: Farm, db: Session) -> dict:
    """Return WhatsApp-ready farm status message."""
    now = datetime.utcnow()
    date_str = now.strftime("%d/%m/%Y")

    summary = compute_active_alerts_summary(farm, db)
    has_alerts = not summary["safe"]
    critical_count = summary["critical_count"]
    top_action = summary.get("top_action_es", "")

    # Line 1: farm identity
    line1 = f"{farm.name} — {date_str}"

    # Line 2: alert status
    if has_alerts and top_action and not summary["safe"]:
        line2 = f"Alerta: {top_action}"
    else:
        line2 = _NO_ALERT_LINE2

    # Line 3: recommended action tier
    if critical_count > 0:
        line3 = _CRITICAL_LINE3
    elif summary["high_count"] > 0:
        line3 = _HIGH_LINE3
    else:
        line3 = _NO_ALERT_LINE3

    message_es = f"{line1}\n{line2}\n{line3}"

    return {
        "farm_id": farm.id,
        "message_es": message_es,
        "has_alerts": has_alerts,
        "generated_at": now.isoformat(),
    }
