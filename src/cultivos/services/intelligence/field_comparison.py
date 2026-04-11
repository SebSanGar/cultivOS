"""Service: multi-field health comparison for a farm.

For each field, retrieves the latest HealthScore, NDVIResult, and SoilAnalysis,
then returns them sorted by latest_health descending.
"""

from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, HealthScore, NDVIResult, SoilAnalysis


def compute_field_comparison(farm: Farm, db: Session) -> list[dict]:
    """Return side-by-side comparison of all fields in a farm.

    Each dict has: field_id, field_name, latest_health, latest_ndvi,
    latest_soil_ph, trend. Nulls for missing data. Sorted by latest_health DESC
    (fields with no health score appear at the end).
    """
    fields = db.query(Field).filter(Field.farm_id == farm.id).all()

    results = []
    for field in fields:
        # Latest HealthScore
        hs = (
            db.query(HealthScore)
            .filter(HealthScore.field_id == field.id)
            .order_by(HealthScore.scored_at.desc())
            .first()
        )
        # Latest NDVIResult
        ndvi = (
            db.query(NDVIResult)
            .filter(NDVIResult.field_id == field.id)
            .order_by(NDVIResult.analyzed_at.desc())
            .first()
        )
        # Latest SoilAnalysis
        soil = (
            db.query(SoilAnalysis)
            .filter(SoilAnalysis.field_id == field.id)
            .order_by(SoilAnalysis.sampled_at.desc())
            .first()
        )

        results.append({
            "field_id": field.id,
            "field_name": field.name,
            "latest_health": hs.score if hs else None,
            "latest_ndvi": round(ndvi.ndvi_mean, 4) if ndvi else None,
            "latest_soil_ph": round(soil.ph, 2) if soil else None,
            "trend": hs.trend if hs else None,
        })

    # Sort by latest_health descending (nulls last)
    results.sort(key=lambda x: (x["latest_health"] is None, -(x["latest_health"] or 0)))
    return results
