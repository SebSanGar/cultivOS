"""Farm comparison service — pure queries, no HTTP concerns.

Composes per-farm KPIs for side-by-side comparison across selected farms.
Unknown farm IDs return null rows (not errors).
"""

from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord
from cultivos.models.farm_comparison import FarmComparisonOut, FarmComparisonRow
from cultivos.services.intelligence.certification import compute_certification_readiness

_SOC_TO_CO2E = 3.67


def _co2e_for_farm(farm_fields: list, db: Session) -> float:
    """Estimate CO2e tonnes from soil organic matter for all fields in a farm."""
    from cultivos.db.models import SoilAnalysis

    total = 0.0
    for fld in farm_fields:
        soil = (
            db.query(SoilAnalysis)
            .filter(SoilAnalysis.field_id == fld.id)
            .order_by(SoilAnalysis.sampled_at.desc())
            .first()
        )
        if soil and soil.organic_matter_pct and fld.hectares:
            soc_per_ha = soil.organic_matter_pct * 0.58
            total += soc_per_ha * (fld.hectares or 0) * _SOC_TO_CO2E
    return round(total, 2)


def _row_for_farm(farm_id: int, db: Session) -> FarmComparisonRow:
    """Build one comparison row for a farm. Returns null row if farm not found."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if farm is None:
        return FarmComparisonRow(farm_id=farm_id)

    farm_fields = db.query(Field).filter(Field.farm_id == farm_id).all()
    field_ids = [f.id for f in farm_fields]

    # avg_health: latest score per field
    latest_scores = []
    for fld in farm_fields:
        hs = (
            db.query(HealthScore)
            .filter(HealthScore.field_id == fld.id)
            .order_by(HealthScore.scored_at.desc())
            .first()
        )
        if hs:
            latest_scores.append(hs.score)

    avg_health = round(sum(latest_scores) / len(latest_scores), 1) if latest_scores else None
    total_hectares = round(sum(f.hectares or 0 for f in farm_fields), 1)

    # treatment_count and organic_pct
    treatments = (
        db.query(TreatmentRecord)
        .filter(TreatmentRecord.field_id.in_(field_ids))
        .all() if field_ids else []
    )
    treatment_count = len(treatments)
    if treatment_count > 0:
        organic_count = sum(1 for t in treatments if t.organic)
        organic_pct = round(organic_count / treatment_count * 100, 1)
    else:
        organic_pct = None

    co2e = _co2e_for_farm(farm_fields, db)

    cert = compute_certification_readiness(farm_id, db)
    certification_readiness = cert["overall_pct"] if cert else None

    return FarmComparisonRow(
        farm_id=farm.id,
        farm_name=farm.name,
        avg_health=avg_health,
        total_hectares=total_hectares,
        treatment_count=treatment_count,
        co2e_sequestered=co2e,
        organic_pct=organic_pct,
        certification_readiness=certification_readiness,
    )


def compute_farm_comparison(farm_ids: list[int], db: Session) -> FarmComparisonOut:
    """Compare multiple farms by their KPIs.

    Order matches input farm_ids. Unknown IDs yield null rows.
    Empty input returns empty list.
    """
    rows = [_row_for_farm(fid, db) for fid in farm_ids]
    return FarmComparisonOut(farms=rows)
