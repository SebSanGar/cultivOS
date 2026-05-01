"""Cooperative weekly agenda — top 5 stressed fields across all member farms."""

from sqlalchemy.orm import Session

from cultivos.db.models import Cooperative, Farm, Field
from cultivos.services.intelligence.field_priority import compute_field_priority


def compute_coop_agenda_semanal(cooperative: Cooperative, db: Session) -> dict:
    """Return dict with coop_name, total_farms, total_fields, top_items, resumen_es."""
    farms = db.query(Farm).filter(Farm.cooperative_id == cooperative.id).all()

    if not farms:
        return {
            "coop_name": cooperative.name,
            "total_farms": 0,
            "total_fields": 0,
            "top_items": [],
            "resumen_es": f"{cooperative.name}: sin fincas miembro registradas.",
        }

    all_fields = []
    total_field_count = 0

    for farm in farms:
        priority_data = compute_field_priority(farm, db)
        for field_entry in priority_data["fields"]:
            total_field_count += 1
            all_fields.append({
                "farm_name": farm.name,
                "field_name": field_entry["name"],
                "priority_score": field_entry["priority_score"],
                "top_issue": field_entry["top_issue"],
                "accion_es": field_entry["recommended_action"],
            })

    all_fields.sort(key=lambda x: x["priority_score"], reverse=True)
    top_items = all_fields[:5]

    if total_field_count == 0:
        resumen = f"{cooperative.name}: {len(farms)} finca(s), sin campos registrados."
    elif not top_items or top_items[0]["priority_score"] <= 20:
        resumen = (
            f"{cooperative.name}: {len(farms)} finca(s), {total_field_count} campo(s). "
            f"Todo en orden, sin acciones urgentes."
        )
    else:
        top = top_items[0]
        resumen = (
            f"{cooperative.name}: {len(farms)} finca(s), {total_field_count} campo(s). "
            f"Prioridad: {top['field_name']} ({top['farm_name']}) — {top['accion_es']}"
        )

    if len(resumen) > 200:
        resumen = resumen[:197] + "..."

    return {
        "coop_name": cooperative.name,
        "total_farms": len(farms),
        "total_fields": total_field_count,
        "top_items": top_items,
        "resumen_es": resumen,
    }
