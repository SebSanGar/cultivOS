"""Alert endpoints — nested under /api/farms/{farm_id}/alerts."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import Alert, AlertConfig, Farm, Field, HealthScore, NDVIResult, SoilAnalysis, ThermalResult, WeatherRecord
from cultivos.db.session import get_db
from cultivos.models.alert import AlertCheckResponse, AlertOut
from cultivos.services.alerts.sms import HEALTH_THRESHOLD, format_anomaly_sms, format_irrigation_sms, format_sms_message, should_send_alert
from cultivos.services.intelligence.anomaly import detect_health_anomalies, detect_ndvi_anomalies
from cultivos.services.intelligence.irrigation import compute_irrigation_schedule

router = APIRouter(
    prefix="/api/farms/{farm_id}/alerts",
    tags=["alerts"],
    dependencies=[Depends(get_current_user)]
)


def _get_farm(farm_id: int, db: Session) -> Farm:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


@router.post("/check", response_model=AlertCheckResponse)
def check_and_create_alerts(
    farm_id: int,
    db: Session = Depends(get_db),
):
    """Check all fields in a farm for low health and create alerts.

    Scans each field's latest health score. If score < 40,
    creates an SMS alert (unless one was sent within 24h).
    """
    farm = _get_farm(farm_id, db)
    fields = db.query(Field).filter(Field.farm_id == farm_id).all()

    # Use custom threshold if configured, otherwise default
    config = db.query(AlertConfig).filter(AlertConfig.farm_id == farm_id).first()
    threshold = config.health_score_floor if config else HEALTH_THRESHOLD

    alerts_created = []
    for field in fields:
        latest_score = (
            db.query(HealthScore)
            .filter(HealthScore.field_id == field.id)
            .order_by(HealthScore.scored_at.desc())
            .first()
        )
        if not latest_score or latest_score.score >= threshold:
            continue

        if not should_send_alert(db, farm_id, field.id, "low_health"):
            continue

        message = format_sms_message(
            farm_name=farm.name,
            field_name=field.name,
            alert_type="low_health",
            score=latest_score.score,
        )
        alert = Alert(
            farm_id=farm_id,
            field_id=field.id,
            alert_type="low_health",
            message=message,
            phone_number=None,  # filled when Twilio is configured
            status="pending",
        )
        db.add(alert)
        alerts_created.append(alert)

    if alerts_created:
        db.commit()
        for a in alerts_created:
            db.refresh(a)

    return AlertCheckResponse(
        farm_id=farm_id,
        alerts_created=[AlertOut.model_validate(a) for a in alerts_created],
        fields_checked=len(fields),
    )


@router.get("", response_model=list[AlertOut])
def list_alerts(
    farm_id: int,
    db: Session = Depends(get_db),
):
    """List all alerts for a farm, most recent first."""
    _get_farm(farm_id, db)
    return (
        db.query(Alert)
        .filter(Alert.farm_id == farm_id)
        .order_by(Alert.sent_at.desc())
        .all()
    )


@router.post("/check-irrigation", response_model=AlertCheckResponse)
def check_irrigation_alerts(
    farm_id: int,
    db: Session = Depends(get_db),
):
    """Check all fields for irrigation urgency and create alerts.

    Computes irrigation schedule per field using latest soil, weather,
    and thermal data. Creates an SMS alert only when urgency is 'alta'.
    Deduplicates: no repeat alert within 24h for the same field.
    """
    farm = _get_farm(farm_id, db)
    fields = db.query(Field).filter(Field.farm_id == farm_id).all()

    alerts_created = []
    for field in fields:
        # Skip if irrigation alert already sent within 24h
        if not should_send_alert(db, farm_id, field.id, "irrigation"):
            continue

        # Gather latest data for irrigation computation
        soil_record = (
            db.query(SoilAnalysis)
            .filter(SoilAnalysis.field_id == field.id)
            .order_by(SoilAnalysis.sampled_at.desc())
            .first()
        )
        soil_dict = None
        if soil_record:
            soil_dict = {
                "texture": soil_record.texture,
                "moisture_pct": soil_record.moisture_pct,
            }

        weather_record = (
            db.query(WeatherRecord)
            .filter(WeatherRecord.farm_id == farm_id)
            .order_by(WeatherRecord.recorded_at.desc())
            .first()
        )
        weather_dict = None
        if weather_record:
            weather_dict = {
                "temp_c": weather_record.temp_c,
                "humidity_pct": weather_record.humidity_pct,
                "recent_rainfall_mm": weather_record.rainfall_mm,
            }

        thermal_record = (
            db.query(ThermalResult)
            .filter(ThermalResult.field_id == field.id)
            .order_by(ThermalResult.analyzed_at.desc())
            .first()
        )
        thermal_dict = None
        if thermal_record:
            thermal_dict = {
                "stress_pct": thermal_record.stress_pct,
                "irrigation_deficit": thermal_record.irrigation_deficit,
            }

        result = compute_irrigation_schedule(
            crop_type=field.crop_type,
            hectares=field.hectares or 0.0,
            soil=soil_dict,
            weather=weather_dict,
            thermal=thermal_dict,
        )

        # Only alert on high urgency
        if result["urgencia"] != "alta":
            continue

        daily_liters = result["schedule"][0]["liters_per_ha"] if result["schedule"] else 0.0
        message = format_irrigation_sms(
            farm_name=farm.name,
            field_name=field.name,
            urgencia=result["urgencia"],
            liters_per_ha=daily_liters,
            crop_type=result["crop_type"],
        )
        alert = Alert(
            farm_id=farm_id,
            field_id=field.id,
            alert_type="irrigation",
            message=message,
            phone_number=None,
            status="pending",
        )
        db.add(alert)
        alerts_created.append(alert)

    if alerts_created:
        db.commit()
        for a in alerts_created:
            db.refresh(a)

    return AlertCheckResponse(
        farm_id=farm_id,
        alerts_created=[AlertOut.model_validate(a) for a in alerts_created],
        fields_checked=len(fields),
    )


@router.post("/check-anomalies", response_model=AlertCheckResponse)
def check_anomaly_alerts(
    farm_id: int,
    db: Session = Depends(get_db),
):
    """Scan all fields for health and NDVI anomalies and create alerts.

    Health anomaly: score drops >15 points between consecutive readings.
    NDVI anomaly: latest NDVI mean drops >20% below historical average.
    Deduplicates: no repeat alert within 24h for the same field+type.
    """
    farm = _get_farm(farm_id, db)
    fields = db.query(Field).filter(Field.farm_id == farm_id).all()

    alerts_created = []
    for field in fields:
        # --- Health score anomalies ---
        health_records = (
            db.query(HealthScore)
            .filter(HealthScore.field_id == field.id)
            .order_by(HealthScore.scored_at.asc())
            .all()
        )
        if len(health_records) >= 2:
            score_dicts = [
                {"score": hs.score, "scored_at": hs.scored_at}
                for hs in health_records
            ]
            health_anomalies = detect_health_anomalies(score_dicts, field_name=field.name)
            for anomaly in health_anomalies:
                alert_type = "anomaly_health_drop"
                if not should_send_alert(db, farm_id, field.id, alert_type):
                    continue
                message = format_anomaly_sms(
                    farm_name=farm.name,
                    field_name=field.name,
                    anomaly_type="health_drop",
                    recommendation=anomaly["recommendation"],
                )
                alert = Alert(
                    farm_id=farm_id,
                    field_id=field.id,
                    alert_type=alert_type,
                    message=message,
                    phone_number=None,
                    status="pending",
                )
                db.add(alert)
                alerts_created.append(alert)

        # --- NDVI anomalies ---
        ndvi_records = (
            db.query(NDVIResult)
            .filter(NDVIResult.field_id == field.id)
            .order_by(NDVIResult.analyzed_at.asc())
            .all()
        )
        if len(ndvi_records) >= 2:
            ndvi_dicts = [
                {"ndvi_mean": nr.ndvi_mean, "analyzed_at": nr.analyzed_at}
                for nr in ndvi_records
            ]
            ndvi_anomalies = detect_ndvi_anomalies(ndvi_dicts, field_name=field.name)
            for anomaly in ndvi_anomalies:
                alert_type = "anomaly_ndvi_drop"
                if not should_send_alert(db, farm_id, field.id, alert_type):
                    continue
                message = format_anomaly_sms(
                    farm_name=farm.name,
                    field_name=field.name,
                    anomaly_type="ndvi_drop",
                    recommendation=anomaly["recommendation"],
                )
                alert = Alert(
                    farm_id=farm_id,
                    field_id=field.id,
                    alert_type=alert_type,
                    message=message,
                    phone_number=None,
                    status="pending",
                )
                db.add(alert)
                alerts_created.append(alert)

    if alerts_created:
        db.commit()
        for a in alerts_created:
            db.refresh(a)

    return AlertCheckResponse(
        farm_id=farm_id,
        alerts_created=[AlertOut.model_validate(a) for a in alerts_created],
        fields_checked=len(fields),
    )
