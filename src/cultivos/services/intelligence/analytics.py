"""Cross-farm analytics service — pure queries, no HTTP concerns."""

from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, HealthScore, SoilAnalysis, TreatmentRecord


def _classify_season(dt: datetime) -> tuple[str, int]:
    """Classify a datetime into Jalisco season and start year.

    Temporal: Jun-Oct (start year = same year)
    Secas: Nov-May (start year = previous year if Jan-May, same year if Nov-Dec)
    """
    month = dt.month
    if 6 <= month <= 10:
        return "temporal", dt.year
    elif month >= 11:
        return "secas", dt.year
    else:  # Jan-May
        return "secas", dt.year - 1


def compute_summary(db: Session) -> dict:
    """Compute cross-farm summary: total farms, fields, avg health, worst field."""
    total_farms = db.query(func.count(Farm.id)).scalar() or 0
    total_fields = db.query(func.count(Field.id)).scalar() or 0

    # Latest health score per field (subquery)
    fields = db.query(Field).all()
    latest_scores: list[tuple] = []  # (field, score)

    for field in fields:
        latest_hs = (
            db.query(HealthScore)
            .filter(HealthScore.field_id == field.id)
            .order_by(HealthScore.scored_at.desc())
            .first()
        )
        if latest_hs:
            latest_scores.append((field, latest_hs.score))

    avg_health = None
    worst_field = None

    if latest_scores:
        avg_health = round(sum(s for _, s in latest_scores) / len(latest_scores), 1)
        worst = min(latest_scores, key=lambda x: x[1])
        farm = db.query(Farm).filter(Farm.id == worst[0].farm_id).first()
        worst_field = {
            "field_id": worst[0].id,
            "field_name": worst[0].name,
            "farm_name": farm.name if farm else "Unknown",
            "score": worst[1],
        }

    return {
        "total_farms": total_farms,
        "total_fields": total_fields,
        "avg_health": avg_health,
        "worst_field": worst_field,
    }


def compute_soil_trends(db: Session) -> dict:
    """Compute soil pH and organic matter averages grouped by month."""
    analyses = (
        db.query(SoilAnalysis)
        .filter(SoilAnalysis.ph.isnot(None), SoilAnalysis.organic_matter_pct.isnot(None))
        .order_by(SoilAnalysis.sampled_at.asc())
        .all()
    )

    # Group by year-month
    monthly: dict[str, list] = {}
    for sa in analyses:
        key = sa.sampled_at.strftime("%Y-%m")
        monthly.setdefault(key, []).append(sa)

    trends = []
    for date_key, records in sorted(monthly.items()):
        avg_ph = round(sum(r.ph for r in records) / len(records), 2)
        avg_om = round(sum(r.organic_matter_pct for r in records) / len(records), 2)
        trends.append({
            "date": date_key,
            "avg_ph": avg_ph,
            "avg_organic_matter": avg_om,
            "sample_count": len(records),
        })

    return {"trends": trends}


def compute_treatment_effectiveness(db: Session) -> dict:
    """List treatments with health score before and after (if available)."""
    treatments = db.query(TreatmentRecord).all()
    results = []

    for tr in treatments:
        field = db.query(Field).filter(Field.id == tr.field_id).first()
        farm = db.query(Farm).filter(Farm.id == field.farm_id).first() if field else None

        # health_before = the score used when treatment was generated
        health_before = tr.health_score_used

        # health_after = the next health score recorded after this treatment
        health_after = None
        delta = None
        if tr.created_at:
            next_hs = (
                db.query(HealthScore)
                .filter(
                    HealthScore.field_id == tr.field_id,
                    HealthScore.scored_at > tr.created_at,
                )
                .order_by(HealthScore.scored_at.asc())
                .first()
            )
            if next_hs:
                health_after = next_hs.score
                delta = round(next_hs.score - health_before, 1)

        results.append({
            "field_name": field.name if field else "Unknown",
            "farm_name": farm.name if farm else "Unknown",
            "tratamiento": tr.tratamiento,
            "health_before": health_before,
            "health_after": health_after,
            "delta": delta,
            "urgencia": tr.urgencia,
            "organic": tr.organic,
        })

    return {"treatments": results}


def compute_anomalies(db: Session) -> dict:
    """Find fields with health declining 2+ consecutive readings."""
    fields = db.query(Field).all()
    anomalies = []

    for field in fields:
        scores = (
            db.query(HealthScore)
            .filter(HealthScore.field_id == field.id)
            .order_by(HealthScore.scored_at.asc())
            .all()
        )

        if len(scores) < 2:
            continue

        # Count consecutive declines from the end
        consecutive = 0
        for i in range(len(scores) - 1, 0, -1):
            if scores[i].score < scores[i - 1].score:
                consecutive += 1
            else:
                break

        if consecutive >= 2:
            farm = db.query(Farm).filter(Farm.id == field.farm_id).first()
            anomalies.append({
                "field_id": field.id,
                "field_name": field.name,
                "farm_name": farm.name if farm else "Unknown",
                "consecutive_declines": consecutive,
                "latest_score": scores[-1].score,
                "score_history": [s.score for s in scores],
            })

    return {"anomalies": anomalies}


def compute_seasonal_performance(
    db: Session, field_id: int, year: Optional[int] = None
) -> dict:
    """Group health scores by Jalisco season (temporal/secas) for a field."""
    query = db.query(HealthScore).filter(HealthScore.field_id == field_id)
    scores = query.order_by(HealthScore.scored_at.asc()).all()

    # Group by (season, start_year)
    groups: dict[tuple[str, int], list[float]] = {}
    for hs in scores:
        season, start_year = _classify_season(hs.scored_at)
        groups.setdefault((season, start_year), []).append(hs.score)

    # Filter by year if requested
    if year is not None:
        groups = {k: v for k, v in groups.items() if k[1] == year}

    seasons = []
    for (season, start_year), score_list in sorted(groups.items(), key=lambda x: (x[0][1], x[0][0])):
        count = len(score_list)
        avg = round(sum(score_list) / count, 2)
        status = "ok" if count >= 2 else "insufficient_data"
        seasons.append({
            "season": season,
            "year": start_year,
            "avg_score": avg,
            "count": count,
            "status": status,
        })

    return {"seasons": seasons}
