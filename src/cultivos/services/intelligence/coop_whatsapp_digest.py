"""Cooperative WhatsApp digest aggregate service (#202).

GET /api/cooperatives/{coop_id}/whatsapp-digest

Composes per-farm whatsapp-status (#185) into a single cooperative digest:
- Aggregate critical + high alert counts across all member farms
- Top 3 farms needing attention, ranked by (critical_count DESC, high_count
  DESC, farm_id ASC)
- One-line Spanish digest_message_es suitable for a cooperative manager's
  WhatsApp group chat
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from cultivos.db.models import Farm
from cultivos.services.intelligence.active_alerts_summary import (
    compute_active_alerts_summary,
)
from cultivos.services.intelligence.whatsapp_status import compute_whatsapp_status

_TOP_N = 3


def _digest_message(
    total_farms: int,
    farms_with_alerts: int,
    total_critical: int,
    total_high: int,
    top_farm_name: str | None,
) -> str:
    if total_farms == 0:
        return "Cooperativa sin fincas registradas."
    if farms_with_alerts == 0:
        return (
            f"Cooperativa: Sin alertas activas en {total_farms} fincas. "
            "Monitoreo al dia."
        )
    parts = [
        f"Cooperativa: {farms_with_alerts} de {total_farms} fincas con alertas activas"
    ]
    counts: list[str] = []
    if total_critical:
        counts.append(f"{total_critical} criticas")
    if total_high:
        counts.append(f"{total_high} altas")
    if counts:
        parts.append(" (" + ", ".join(counts) + ")")
    parts.append(".")
    if top_farm_name:
        parts.append(f" Atencion prioritaria: {top_farm_name}.")
    return "".join(parts)


def compute_coop_whatsapp_digest(coop_id: int, db: Session) -> dict:
    farms = (
        db.query(Farm)
        .filter(Farm.cooperative_id == coop_id)
        .order_by(Farm.id)
        .all()
    )

    total_critical = 0
    total_high = 0
    attention: list[dict] = []

    for farm in farms:
        summary = compute_active_alerts_summary(farm, db)
        critical = int(summary.get("critical_count", 0) or 0)
        high = int(summary.get("high_count", 0) or 0)
        total_critical += critical
        total_high += high
        if critical + high == 0:
            continue
        status = compute_whatsapp_status(farm, db)
        attention.append(
            {
                "farm_id": farm.id,
                "farm_name": farm.name,
                "critical_count": critical,
                "high_count": high,
                "message_es": status.get("message_es", ""),
            }
        )

    attention.sort(key=lambda f: (-f["critical_count"], -f["high_count"], f["farm_id"]))
    top = attention[:_TOP_N]
    farms_with_alerts = len(attention)
    top_farm_name = top[0]["farm_name"] if top else None

    return {
        "cooperative_id": coop_id,
        "generated_at": datetime.utcnow().isoformat(),
        "total_farms": len(farms),
        "total_critical_alerts": total_critical,
        "total_high_alerts": total_high,
        "farms_with_alerts": farms_with_alerts,
        "top_attention_farms": top,
        "digest_message_es": _digest_message(
            len(farms),
            farms_with_alerts,
            total_critical,
            total_high,
            top_farm_name,
        ),
    }
