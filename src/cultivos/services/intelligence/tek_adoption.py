"""Farm TEK (ancestral method) adoption service — #207.

Closes the TEK feedback loop: records which farmers have actually adopted
which ancestral practices from the AncestralMethod seed library.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from cultivos.db.models import AncestralMethod, Farm, Field, TEKAdoption


def _find_method(name: str, db: Session) -> AncestralMethod | None:
    return (
        db.query(AncestralMethod)
        .filter(AncestralMethod.name == name)
        .first()
    )


def create_adoption(
    farm: Farm,
    method_name: str,
    adopted_at: datetime,
    fields_applied: List[int],
    farmer_notes_es: str,
    db: Session,
) -> tuple[TEKAdoption, AncestralMethod]:
    """Create a TEKAdoption row. Raises ValueError("method"|"field") on invalid input."""
    method = _find_method(method_name, db)
    if method is None:
        raise ValueError("method")

    for fid in fields_applied:
        field = (
            db.query(Field)
            .filter(Field.id == fid, Field.farm_id == farm.id)
            .first()
        )
        if field is None:
            raise ValueError("field")

    row = TEKAdoption(
        farm_id=farm.id,
        method_name=method.name,
        adopted_at=adopted_at,
        fields_applied=list(fields_applied),
        farmer_notes_es=farmer_notes_es or "",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row, method


def list_adoptions(farm: Farm, db: Session) -> dict:
    rows = (
        db.query(TEKAdoption)
        .filter(TEKAdoption.farm_id == farm.id)
        .order_by(TEKAdoption.adopted_at.desc())
        .all()
    )

    # attach ecological_benefit by joining to AncestralMethod via name
    method_names = {r.method_name for r in rows}
    benefit_by_name: dict[str, int | None] = {}
    if method_names:
        methods = (
            db.query(AncestralMethod)
            .filter(AncestralMethod.name.in_(method_names))
            .all()
        )
        benefit_by_name = {m.name: m.ecological_benefit for m in methods}

    adoptions = []
    for r in rows:
        fields_list = r.fields_applied or []
        adoptions.append({
            "id": r.id,
            "method_name": r.method_name,
            "adopted_at": r.adopted_at,
            "fields_count": len(fields_list),
            "farmer_notes_es": r.farmer_notes_es or "",
            "ecological_benefit": benefit_by_name.get(r.method_name),
        })

    return {
        "farm_id": farm.id,
        "adoptions": adoptions,
        "adoption_count": len(adoptions),
        "most_recent_adoption_at": rows[0].adopted_at if rows else None,
    }
