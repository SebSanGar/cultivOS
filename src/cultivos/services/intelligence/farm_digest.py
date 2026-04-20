"""Farm-level Spanish daily digest — composes field_accion across all fields."""

from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field
from cultivos.services.intelligence.field_accion import compute_field_accion

_PRIORITY_RANK = {"alta": 3, "media": 2, "baja": 1, "ninguna": 0}


def compute_farm_digest(farm: Farm, db: Session) -> dict:
    """Return dict with farm_name, field_count, top_priority, digest_es."""
    fields = db.query(Field).filter(Field.farm_id == farm.id).all()

    if not fields:
        return {
            "farm_name": farm.name,
            "field_count": 0,
            "top_priority": "ninguna",
            "digest_es": f"{farm.name}: sin campos registrados.",
        }

    acciones = []
    for field in fields:
        accion = compute_field_accion(field, db)
        acciones.append(accion)

    acciones.sort(key=lambda a: _PRIORITY_RANK.get(a["priority"], 0), reverse=True)
    top = acciones[0]
    top_priority = top["priority"]

    n = len(fields)

    if top_priority == "ninguna":
        digest = f"{farm.name}: {n} campo(s), todo en orden. Continuar monitoreo."
    else:
        urgent_count = sum(1 for a in acciones if a["priority"] != "ninguna")
        ok_count = n - urgent_count
        digest = f"{farm.name}: {n} campo(s). {top['field_name']}: {top['accion_es']}"
        if ok_count > 0:
            digest += f" {ok_count} campo(s) sin urgencia."

    if len(digest) > 200:
        digest = digest[:197] + "..."

    return {
        "farm_name": farm.name,
        "field_count": n,
        "top_priority": top_priority,
        "digest_es": digest,
    }
