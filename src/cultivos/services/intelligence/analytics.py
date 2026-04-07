"""Cross-farm analytics service — pure queries, no HTTP concerns."""

from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from cultivos.db.models import (
    Alert,
    Farm,
    FarmerFeedback,
    Field,
    HealthScore,
    MicrobiomeRecord,
    NDVIResult,
    SoilAnalysis,
    ThermalResult,
    TreatmentRecord,
    WeatherRecord,
)
from cultivos.services.crop.health import (
    MicrobiomeInput,
    NDVIInput,
    SoilInput,
    ThermalInput,
    compute_health_score,
)


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


def compare_farms(db: Session, farm_ids: list[int]) -> dict:
    """Compare health, yield, treatments, soil, carbon, alerts, and completeness across farms.

    Returns a list of farm summaries with avg health (from latest score per field),
    total yield prediction, treatment count, avg soil organic matter, carbon
    sequestration estimate, alert count, and data completeness percentage.
    Raises ValueError if any farm_id is not found.
    """
    from cultivos.services.intelligence.carbon import estimate_soc
    from cultivos.services.intelligence.yield_model import predict_yield

    _SOC_TO_CO2E = 3.67

    results = []
    for fid in farm_ids:
        farm = db.query(Farm).filter(Farm.id == fid).first()
        if not farm:
            raise ValueError(f"Farm {fid} not found")

        fields = db.query(Field).filter(Field.farm_id == fid).all()

        latest_scores: list[float] = []
        total_yield = 0.0
        total_treatment_count = 0
        total_hectares = 0.0
        soil_om_values: list[float] = []
        total_co2e = 0.0
        has_soil_data = False

        # Collect all health scores across fields for history/trend
        field_ids = [f.id for f in fields]
        all_scores = []
        if field_ids:
            all_scores = (
                db.query(HealthScore)
                .filter(HealthScore.field_id.in_(field_ids))
                .order_by(HealthScore.scored_at.asc())
                .all()
            )

        for field in fields:
            total_hectares += field.hectares or 0

            # Latest health score for this field
            latest_hs = (
                db.query(HealthScore)
                .filter(HealthScore.field_id == field.id)
                .order_by(HealthScore.scored_at.desc())
                .first()
            )
            if latest_hs:
                latest_scores.append(latest_hs.score)
                # Yield prediction using latest health score
                yp = predict_yield(
                    crop_type=field.crop_type or "maiz",
                    hectares=field.hectares or 0,
                    health_score=latest_hs.score,
                )
                total_yield += yp["total_kg"]

            # Treatment count
            tc = db.query(func.count(TreatmentRecord.id)).filter(
                TreatmentRecord.field_id == field.id
            ).scalar() or 0
            total_treatment_count += tc

            # Latest soil analysis for OM avg and carbon
            latest_soil = (
                db.query(SoilAnalysis)
                .filter(
                    SoilAnalysis.field_id == field.id,
                    SoilAnalysis.organic_matter_pct.isnot(None),
                )
                .order_by(SoilAnalysis.sampled_at.desc())
                .first()
            )
            if latest_soil:
                has_soil_data = True
                soil_om_values.append(float(latest_soil.organic_matter_pct))
                soc = estimate_soc(
                    organic_matter_pct=float(latest_soil.organic_matter_pct),
                    depth_cm=float(latest_soil.depth_cm or 30.0),
                )
                field_ha = field.hectares or 0
                total_co2e += soc["soc_tonnes_per_ha"] * field_ha * _SOC_TO_CO2E

        avg_health = round(sum(latest_scores) / len(latest_scores), 1) if latest_scores else None

        # Soil OM average
        soil_om_avg = round(sum(soil_om_values) / len(soil_om_values), 1) if soil_om_values else None

        # Carbon CO2e
        carbon_co2e_tonnes = round(total_co2e, 2) if has_soil_data else None

        # Alert count for this farm
        alert_count = db.query(func.count(Alert.id)).filter(
            Alert.farm_id == fid
        ).scalar() or 0

        # Data completeness: check 5 types per field, average
        completeness_pct = None
        if fields:
            has_weather = (
                db.query(WeatherRecord)
                .filter(WeatherRecord.farm_id == fid)
                .first()
                is not None
            )
            field_scores = []
            for field in fields:
                present = sum([
                    db.query(SoilAnalysis).filter(SoilAnalysis.field_id == field.id).first() is not None,
                    db.query(NDVIResult).filter(NDVIResult.field_id == field.id).first() is not None,
                    db.query(ThermalResult).filter(ThermalResult.field_id == field.id).first() is not None,
                    db.query(TreatmentRecord).filter(TreatmentRecord.field_id == field.id).first() is not None,
                    has_weather,
                ])
                field_scores.append(round((present / 5) * 100, 1))
            completeness_pct = round(sum(field_scores) / len(field_scores), 1)

        # Build health history: avg score per scored_at date, last 10
        history_by_date: dict[str, list[float]] = {}
        for hs in all_scores:
            date_key = str(hs.scored_at.date()) if hs.scored_at else "unknown"
            history_by_date.setdefault(date_key, []).append(hs.score)
        health_history = [
            round(sum(scores) / len(scores), 1)
            for _, scores in sorted(history_by_date.items())
        ][-10:]

        # Compute trend from history
        trend = None
        if len(health_history) >= 2:
            recent = health_history[-3:] if len(health_history) >= 3 else health_history
            delta = recent[-1] - recent[0]
            if delta > 3:
                trend = "improving"
            elif delta < -3:
                trend = "declining"
            else:
                trend = "stable"

        results.append({
            "farm_id": fid,
            "farm_name": farm.name,
            "field_count": len(fields),
            "total_hectares": round(total_hectares, 1),
            "avg_health": avg_health,
            "yield_total_kg": round(total_yield, 1),
            "treatment_count": total_treatment_count,
            "health_history": health_history,
            "trend": trend,
            "soil_om_avg": soil_om_avg,
            "carbon_co2e_tonnes": carbon_co2e_tonnes,
            "alert_count": alert_count,
            "completeness_pct": completeness_pct,
        })

    return {"farms": results}


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


def compute_treatment_effectiveness_report(
    db: Session, crop_type: Optional[str] = None
) -> dict:
    """Aggregate treatment effectiveness across all farms/fields.

    Groups treatments by name, computes:
    - total applications
    - feedback count, success rate (% worked=True), avg rating
    - avg health delta (next health score - health_score_used)
    - composite score: 60% feedback success rate + 40% normalized delta

    Returns treatments ranked by composite score descending.
    """
    # Build base query for treatments, optionally filtered by crop_type
    query = db.query(TreatmentRecord).join(Field, TreatmentRecord.field_id == Field.id)
    if crop_type:
        query = query.filter(Field.crop_type == crop_type)
    treatments = query.all()

    # Group by treatment name
    groups: dict[str, list[TreatmentRecord]] = {}
    for tr in treatments:
        groups.setdefault(tr.tratamiento, []).append(tr)

    results = []
    for name, records in groups.items():
        total_applications = len(records)

        # Gather feedback for these treatment records
        tr_ids = [r.id for r in records]
        feedbacks = (
            db.query(FarmerFeedback)
            .filter(FarmerFeedback.treatment_id.in_(tr_ids))
            .all()
        )
        feedback_count = len(feedbacks)
        feedback_success_rate = None
        avg_rating = None
        if feedback_count > 0:
            positive = sum(1 for f in feedbacks if f.worked)
            feedback_success_rate = round((positive / feedback_count) * 100, 1)
            avg_rating = round(sum(f.rating for f in feedbacks) / feedback_count, 2)

        # Compute avg health delta from health scores after treatment
        deltas: list[float] = []
        for tr in records:
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
                    deltas.append(next_hs.score - tr.health_score_used)

        avg_health_delta = round(sum(deltas) / len(deltas), 1) if deltas else None

        # Composite score: 60% feedback success + 40% normalized delta
        # Feedback success: 0-100 → use directly as 0-100
        # Delta: normalize to 0-100 scale (clamp -50..+50 → 0..100)
        fb_component = feedback_success_rate if feedback_success_rate is not None else 50.0
        if avg_health_delta is not None:
            clamped = max(-50, min(50, avg_health_delta))
            delta_normalized = (clamped + 50)  # -50→0, 0→50, +50→100
        else:
            delta_normalized = 50.0  # neutral when no data

        composite_score = round(fb_component * 0.6 + delta_normalized * 0.4, 1)

        results.append({
            "tratamiento": name,
            "total_applications": total_applications,
            "feedback_count": feedback_count,
            "feedback_success_rate": feedback_success_rate,
            "avg_rating": avg_rating,
            "avg_health_delta": avg_health_delta,
            "composite_score": composite_score,
        })

    # Sort by composite score descending
    results.sort(key=lambda x: x["composite_score"], reverse=True)
    return {"treatments": results}


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


def compute_batch_health(db: Session, field_ids: list[int]) -> dict:
    """Compute health score + trend for multiple fields in one call.

    Returns a result entry for every requested field_id.
    Fields that don't exist or have no data get null score/trend.
    """
    if not field_ids:
        return {"results": []}

    # Bulk-fetch fields with their farms
    fields = (
        db.query(Field, Farm.name)
        .join(Farm, Field.farm_id == Farm.id)
        .filter(Field.id.in_(field_ids))
        .all()
    )
    field_map = {f.id: (f, farm_name) for f, farm_name in fields}

    results = []
    for fid in field_ids:
        if fid not in field_map:
            # Field doesn't exist
            results.append({
                "field_id": fid,
                "field_name": None,
                "farm_name": None,
                "score": None,
                "trend": None,
                "sources": None,
                "breakdown": None,
            })
            continue

        field, farm_name = field_map[fid]

        # Fetch latest data sources
        latest_ndvi = (
            db.query(NDVIResult)
            .filter(NDVIResult.field_id == fid)
            .order_by(NDVIResult.analyzed_at.desc())
            .first()
        )
        latest_soil = (
            db.query(SoilAnalysis)
            .filter(SoilAnalysis.field_id == fid)
            .order_by(SoilAnalysis.sampled_at.desc())
            .first()
        )
        latest_microbiome = (
            db.query(MicrobiomeRecord)
            .filter(MicrobiomeRecord.field_id == fid)
            .order_by(MicrobiomeRecord.sampled_at.desc())
            .first()
        )
        latest_thermal = (
            db.query(ThermalResult)
            .filter(ThermalResult.field_id == fid)
            .order_by(ThermalResult.analyzed_at.desc())
            .first()
        )

        if not any([latest_ndvi, latest_soil, latest_microbiome, latest_thermal]):
            # Field exists but has no data
            results.append({
                "field_id": fid,
                "field_name": field.name,
                "farm_name": farm_name,
                "score": None,
                "trend": None,
                "sources": None,
                "breakdown": None,
            })
            continue

        # Build inputs
        ndvi_input = NDVIInput(
            ndvi_mean=latest_ndvi.ndvi_mean,
            ndvi_std=latest_ndvi.ndvi_std,
            stress_pct=latest_ndvi.stress_pct,
        ) if latest_ndvi else None

        soil_input = SoilInput(
            ph=latest_soil.ph,
            organic_matter_pct=latest_soil.organic_matter_pct,
            nitrogen_ppm=latest_soil.nitrogen_ppm,
            phosphorus_ppm=latest_soil.phosphorus_ppm,
            potassium_ppm=latest_soil.potassium_ppm,
            moisture_pct=latest_soil.moisture_pct,
        ) if latest_soil else None

        microbiome_input = MicrobiomeInput(
            respiration_rate=latest_microbiome.respiration_rate,
            microbial_biomass_carbon=latest_microbiome.microbial_biomass_carbon,
            fungi_bacteria_ratio=latest_microbiome.fungi_bacteria_ratio,
            classification=latest_microbiome.classification,
        ) if latest_microbiome else None

        thermal_input = ThermalInput(
            stress_pct=latest_thermal.stress_pct,
            temp_mean=latest_thermal.temp_mean,
            irrigation_deficit=latest_thermal.irrigation_deficit,
        ) if latest_thermal else None

        # Previous score for trend
        previous = (
            db.query(HealthScore)
            .filter(HealthScore.field_id == fid)
            .order_by(HealthScore.scored_at.desc())
            .first()
        )
        previous_score = previous.score if previous else None

        health = compute_health_score(
            ndvi=ndvi_input,
            soil=soil_input,
            previous_score=previous_score,
            microbiome=microbiome_input,
            thermal=thermal_input,
        )

        results.append({
            "field_id": fid,
            "field_name": field.name,
            "farm_name": farm_name,
            "score": health["score"],
            "trend": health["trend"],
            "sources": health["sources"],
            "breakdown": health["breakdown"],
        })

    return {"results": results}


def compute_economics_summary(db: Session) -> dict:
    """Aggregate economic impact across all farms."""
    from cultivos.services.intelligence.economics import calculate_farm_savings

    farms = db.query(Farm).all()
    if not farms:
        return {
            "total_farms": 0,
            "total_hectares": 0,
            "water_savings_mxn": 0,
            "fertilizer_savings_mxn": 0,
            "yield_improvement_mxn": 0,
            "total_savings_mxn": 0,
            "farms": [],
        }

    farm_entries = []
    agg_water = 0
    agg_fert = 0
    agg_yield = 0
    total_hectares = 0.0

    for farm in farms:
        fields = db.query(Field).filter(Field.farm_id == farm.id).all()
        ha = sum(f.hectares or 0 for f in fields)
        total_hectares += ha
        field_ids = [f.id for f in fields]

        # Average health score
        health_scores = []
        for fid in field_ids:
            latest = (
                db.query(HealthScore)
                .filter(HealthScore.field_id == fid)
                .order_by(HealthScore.scored_at.desc())
                .first()
            )
            if latest:
                health_scores.append(float(latest.score))
        avg_health = sum(health_scores) / len(health_scores) if health_scores else 50.0

        treatment_count = (
            db.query(func.count(TreatmentRecord.id))
            .filter(TreatmentRecord.field_id.in_(field_ids))
            .scalar()
        ) if field_ids else 0
        treatment_count = treatment_count or 0

        result = calculate_farm_savings(
            health_score=avg_health,
            hectares=ha,
            treatment_count=treatment_count,
            irrigation_efficiency=None,
        )

        agg_water += result["water_savings_mxn"]
        agg_fert += result["fertilizer_savings_mxn"]
        agg_yield += result["yield_improvement_mxn"]

        farm_entries.append({
            "farm_id": farm.id,
            "farm_name": farm.name,
            "hectares": ha,
            "water_savings_mxn": result["water_savings_mxn"],
            "fertilizer_savings_mxn": result["fertilizer_savings_mxn"],
            "yield_improvement_mxn": result["yield_improvement_mxn"],
            "total_savings_mxn": result["total_savings_mxn"],
        })

    return {
        "total_farms": len(farms),
        "total_hectares": total_hectares,
        "water_savings_mxn": agg_water,
        "fertilizer_savings_mxn": agg_fert,
        "yield_improvement_mxn": agg_yield,
        "total_savings_mxn": agg_water + agg_fert + agg_yield,
        "farms": farm_entries,
    }


# SOC to CO2e conversion factor (molecular weight ratio CO2/C)
_SOC_TO_CO2E = 3.67


def compute_carbon_summary(db: Session) -> dict:
    """Aggregate carbon sequestration metrics across all fields with soil data."""
    from cultivos.services.intelligence.carbon import estimate_soc, compute_carbon_trend

    # Find all fields that have soil analyses with organic_matter_pct
    fields_with_soil = (
        db.query(Field)
        .join(SoilAnalysis, SoilAnalysis.field_id == Field.id)
        .filter(SoilAnalysis.organic_matter_pct.isnot(None))
        .distinct()
        .all()
    )

    if not fields_with_soil:
        return {
            "total_fields": 0,
            "total_hectares": 0,
            "avg_soc_tonnes_per_ha": 0,
            "total_sequestration_tonnes": 0,
            "fields": [],
        }

    field_entries = []
    total_soc = 0.0
    total_ha = 0.0
    total_co2e = 0.0

    for field in fields_with_soil:
        soil_records = (
            db.query(SoilAnalysis)
            .filter(
                SoilAnalysis.field_id == field.id,
                SoilAnalysis.organic_matter_pct.isnot(None),
            )
            .order_by(SoilAnalysis.sampled_at.asc())
            .all()
        )
        if not soil_records:
            continue

        latest = soil_records[-1]
        soc = estimate_soc(
            organic_matter_pct=float(latest.organic_matter_pct),
            depth_cm=float(latest.depth_cm or 30.0),
        )

        # Trend from history
        trend_records = [
            {
                "organic_matter_pct": float(r.organic_matter_pct),
                "depth_cm": float(r.depth_cm or 30.0),
                "sampled_at": r.sampled_at.isoformat() if hasattr(r.sampled_at, "isoformat") else str(r.sampled_at),
            }
            for r in soil_records
        ]
        trend = compute_carbon_trend(trend_records)

        ha = float(field.hectares or 0)
        soc_per_ha = soc["soc_tonnes_per_ha"]
        co2e = soc_per_ha * ha * _SOC_TO_CO2E

        # Get farm name
        farm = db.query(Farm).filter(Farm.id == field.farm_id).first()
        farm_name = farm.name if farm else "Desconocida"

        total_soc += soc_per_ha
        total_ha += ha
        total_co2e += co2e

        field_entries.append({
            "field_id": field.id,
            "field_name": field.name,
            "farm_name": farm_name,
            "hectares": ha,
            "soc_tonnes_per_ha": soc_per_ha,
            "clasificacion": soc["clasificacion"],
            "tendencia": trend["tendencia"],
        })

    avg_soc = round(total_soc / len(field_entries), 2) if field_entries else 0

    return {
        "total_fields": len(field_entries),
        "total_hectares": total_ha,
        "avg_soc_tonnes_per_ha": avg_soc,
        "total_sequestration_tonnes": round(total_co2e, 2),
        "fields": field_entries,
    }


def compute_farm_carbon_summary(db: Session, farm_id: int) -> dict:
    """Aggregate carbon sequestration metrics for a single farm's fields."""
    from cultivos.services.intelligence.carbon import estimate_soc, compute_carbon_trend

    fields_with_soil = (
        db.query(Field)
        .join(SoilAnalysis, SoilAnalysis.field_id == Field.id)
        .filter(Field.farm_id == farm_id, SoilAnalysis.organic_matter_pct.isnot(None))
        .distinct()
        .all()
    )

    empty = {
        "total_fields": 0,
        "total_hectares": 0,
        "avg_soc_tonnes_per_ha": 0,
        "total_co2e_tonnes": 0,
        "soc_per_ha_rate": 0,
        "fields": [],
    }

    if not fields_with_soil:
        return empty

    field_entries = []
    total_soc = 0.0
    total_ha = 0.0
    total_co2e = 0.0

    for field in fields_with_soil:
        soil_records = (
            db.query(SoilAnalysis)
            .filter(
                SoilAnalysis.field_id == field.id,
                SoilAnalysis.organic_matter_pct.isnot(None),
            )
            .order_by(SoilAnalysis.sampled_at.asc())
            .all()
        )
        if not soil_records:
            continue

        latest = soil_records[-1]
        soc = estimate_soc(
            organic_matter_pct=float(latest.organic_matter_pct),
            depth_cm=float(latest.depth_cm or 30.0),
        )

        trend_records = [
            {
                "organic_matter_pct": float(r.organic_matter_pct),
                "depth_cm": float(r.depth_cm or 30.0),
                "sampled_at": r.sampled_at.isoformat() if hasattr(r.sampled_at, "isoformat") else str(r.sampled_at),
            }
            for r in soil_records
        ]
        trend = compute_carbon_trend(trend_records)

        ha = float(field.hectares or 0)
        soc_per_ha = soc["soc_tonnes_per_ha"]
        co2e = soc_per_ha * ha * _SOC_TO_CO2E

        total_soc += soc_per_ha
        total_ha += ha
        total_co2e += co2e

        field_entries.append({
            "field_id": field.id,
            "field_name": field.name,
            "hectares": ha,
            "soc_tonnes_per_ha": round(soc_per_ha, 2),
            "co2e_tonnes": round(co2e, 2),
            "clasificacion": soc["clasificacion"],
            "tendencia": trend["tendencia"],
        })

    avg_soc = round(total_soc / len(field_entries), 2) if field_entries else 0
    soc_per_ha_rate = round(total_co2e / total_ha, 2) if total_ha > 0 else 0

    return {
        "total_fields": len(field_entries),
        "total_hectares": total_ha,
        "avg_soc_tonnes_per_ha": avg_soc,
        "total_co2e_tonnes": round(total_co2e, 2),
        "soc_per_ha_rate": soc_per_ha_rate,
        "fields": field_entries,
    }


def compute_sensor_fusion_overview(db: Session) -> dict:
    """Cross-field sensor fusion validation — run fusion per field, aggregate.

    For each field with at least one sensor reading (NDVI, thermal, soil),
    call validate_sensor_fusion and collect results into a summary.
    """
    from cultivos.services.crop.fusion import validate_sensor_fusion

    fields = db.query(Field).all()
    total_fields = len(fields)
    field_entries = []

    for field in fields:
        farm = db.query(Farm).filter(Farm.id == field.farm_id).first()
        farm_name = farm.name if farm else "Desconocida"

        latest_ndvi = (
            db.query(NDVIResult).filter(NDVIResult.field_id == field.id)
            .order_by(NDVIResult.analyzed_at.desc()).first()
        )
        latest_thermal = (
            db.query(ThermalResult).filter(ThermalResult.field_id == field.id)
            .order_by(ThermalResult.analyzed_at.desc()).first()
        )
        latest_soil = (
            db.query(SoilAnalysis).filter(SoilAnalysis.field_id == field.id)
            .order_by(SoilAnalysis.sampled_at.desc()).first()
        )

        if not any([latest_ndvi, latest_thermal, latest_soil]):
            continue

        result = validate_sensor_fusion(
            ndvi={
                "ndvi_mean": latest_ndvi.ndvi_mean,
                "ndvi_std": latest_ndvi.ndvi_std,
                "stress_pct": latest_ndvi.stress_pct,
            } if latest_ndvi else None,
            thermal={
                "stress_pct": latest_thermal.stress_pct,
                "temp_mean": latest_thermal.temp_mean,
                "irrigation_deficit": latest_thermal.irrigation_deficit,
            } if latest_thermal else None,
            soil={
                "ph": latest_soil.ph,
                "organic_matter_pct": latest_soil.organic_matter_pct,
                "nitrogen_ppm": latest_soil.nitrogen_ppm,
                "phosphorus_ppm": latest_soil.phosphorus_ppm,
                "potassium_ppm": latest_soil.potassium_ppm,
                "moisture_pct": latest_soil.moisture_pct,
            } if latest_soil else None,
        )

        field_entries.append({
            "field_id": field.id,
            "field_name": field.name,
            "farm_name": farm_name,
            "confidence": result["confidence"],
            "sensors_used": result["sensors_used"],
            "contradictions": result["contradictions"],
            "assessment": result["assessment"],
        })

    fields_with_data = len(field_entries)
    avg_confidence = (
        round(sum(f["confidence"] for f in field_entries) / fields_with_data, 2)
        if fields_with_data > 0 else 0
    )
    total_contradictions = sum(len(f["contradictions"]) for f in field_entries)

    return {
        "total_fields": total_fields,
        "fields_with_data": fields_with_data,
        "avg_confidence": avg_confidence,
        "total_contradictions": total_contradictions,
        "fields": field_entries,
    }


def compute_regional_summary(db: Session, state: Optional[str] = None) -> dict:
    """Aggregate intelligence by region (state).

    Groups farms by state, computes per-region:
    - Farm/field counts, total hectares
    - Average health score (latest per field)
    - Crop type distribution
    - Treatment stats + top treatments
    - Current seasonal alerts from TEK calendar
    - Ancestral method usage count
    """
    from cultivos.services.intelligence.seasonal_calendar import generate_seasonal_alerts

    query = db.query(Farm)
    if state:
        query = query.filter(Farm.state == state)
    farms = query.all()

    if not farms:
        return {"regions": []}

    # Group farms by (state, country)
    groups: dict[tuple[str, str], list[Farm]] = {}
    for farm in farms:
        key = (farm.state or "Unknown", farm.country or "MX")
        groups.setdefault(key, []).append(farm)

    regions = []
    for (region_state, country), region_farms in sorted(groups.items()):
        farm_ids = [f.id for f in region_farms]
        fields = db.query(Field).filter(Field.farm_id.in_(farm_ids)).all()
        field_ids = [f.id for f in fields]

        # Total hectares
        total_hectares = round(sum(f.hectares or 0 for f in fields), 1)

        # Avg health from latest score per field
        latest_scores: list[float] = []
        for field in fields:
            latest_hs = (
                db.query(HealthScore)
                .filter(HealthScore.field_id == field.id)
                .order_by(HealthScore.scored_at.desc())
                .first()
            )
            if latest_hs:
                latest_scores.append(latest_hs.score)

        avg_health = round(sum(latest_scores) / len(latest_scores), 1) if latest_scores else None

        # Crop distribution
        crop_groups: dict[str, list[Field]] = {}
        for field in fields:
            crop = field.crop_type or "desconocido"
            crop_groups.setdefault(crop, []).append(field)

        crop_distribution = [
            {
                "crop_type": crop,
                "field_count": len(crop_fields),
                "total_hectares": round(sum(f.hectares or 0 for f in crop_fields), 1),
            }
            for crop, crop_fields in sorted(crop_groups.items())
        ]

        # Treatment stats
        treatments = []
        if field_ids:
            treatments = (
                db.query(TreatmentRecord)
                .filter(TreatmentRecord.field_id.in_(field_ids))
                .all()
            )

        treatment_count = len(treatments)

        # Top treatments by frequency
        treatment_groups: dict[str, list[TreatmentRecord]] = {}
        for tr in treatments:
            treatment_groups.setdefault(tr.tratamiento, []).append(tr)

        top_treatments = sorted(
            [
                {
                    "tratamiento": name,
                    "application_count": len(recs),
                    "organic": all(r.organic for r in recs),
                }
                for name, recs in treatment_groups.items()
            ],
            key=lambda x: x["application_count"],
            reverse=True,
        )[:5]

        # Ancestral methods count
        ancestral_methods_count = sum(
            1 for tr in treatments if tr.ancestral_method_name
        )

        # Seasonal alerts (from TEK calendar)
        alerts = generate_seasonal_alerts()
        seasonal_alerts = [
            {
                "crop": a["crop"],
                "alert_type": a["alert_type"],
                "message": a["message"],
                "season": a["season"],
            }
            for a in alerts
        ]

        regions.append({
            "state": region_state,
            "country": country,
            "farm_count": len(region_farms),
            "field_count": len(fields),
            "total_hectares": total_hectares,
            "avg_health": avg_health,
            "crop_distribution": crop_distribution,
            "treatment_count": treatment_count,
            "top_treatments": top_treatments,
            "seasonal_alerts": seasonal_alerts,
            "ancestral_methods_count": ancestral_methods_count,
        })

    return {"regions": regions}
