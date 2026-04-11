"""Disease outbreak risk assessment service.

Combines weather trends + NDVI patterns + soil pH + crop type to assess
disease outbreak risk for a field.

Risk score formula:
  humidity_pct > 70%          → +20
  NDVI drop > 20% MoM         → +25
  soil pH < 5.5               → +15
  temp_c > 35°C               → +10
  clamped to [0, 100]

Risk levels:
  0-25   → low
  26-50  → medium
  51+    → high
"""

from __future__ import annotations

from datetime import date
from sqlalchemy.orm import Session

from cultivos.db.models import Field, NDVIResult, SoilAnalysis, WeatherRecord


# Disease list: {trigger → [{name_es, probability, preventive_action}]}
_DISEASES_BY_TRIGGER: dict[str, list[dict]] = {
    "humidity": [
        {
            "name_es": "Tizón tardío (Phytophthora infestans)",
            "probability": 0.70,
            "preventive_action": "Aplicar caldo bordelés (1%) antes de lluvias; evitar riego por aspersión.",
        },
        {
            "name_es": "Roya del maíz (Puccinia sorghi)",
            "probability": 0.55,
            "preventive_action": "Mejorar ventilación entre surcos; aplicar azufre micronizado en preventivo.",
        },
    ],
    "ndvi_drop": [
        {
            "name_es": "Cogollero del maíz (Spodoptera frugiperda)",
            "probability": 0.65,
            "preventive_action": "Inspección visual del cogollo; aplicar Bacillus thuringiensis si se confirma.",
        },
        {
            "name_es": "Pulgón de la hoja (Rhopalosiphum maidis)",
            "probability": 0.50,
            "preventive_action": "Liberar depredadores naturales (catarinas); evitar exceso de nitrógeno.",
        },
    ],
    "ph": [
        {
            "name_es": "Marchitez por Fusarium (Fusarium oxysporum)",
            "probability": 0.60,
            "preventive_action": "Encalar el suelo con cal agrícola para elevar pH a 6.0–6.5.",
        },
    ],
    "temp": [
        {
            "name_es": "Estrés por calor / golpe de sol",
            "probability": 0.75,
            "preventive_action": "Regar en las horas más frescas; aplicar mulch para retener humedad.",
        },
    ],
}


def compute_disease_risk_assessment(field: Field, db: Session) -> dict:
    """Assess disease outbreak risk for a field.

    Returns a dict with keys:
        risk_level, risk_score, at_risk_diseases, assessment_date
    """
    score: float = 0.0
    at_risk: list[dict] = []

    # --- Latest weather ---
    weather = (
        db.query(WeatherRecord)
        .filter(WeatherRecord.farm_id == field.farm_id)
        .order_by(WeatherRecord.recorded_at.desc())
        .first()
    )

    if weather is not None:
        if weather.humidity_pct > 70.0:
            score += 20.0
            at_risk.extend(_DISEASES_BY_TRIGGER["humidity"])

        if weather.temp_c > 35.0:
            score += 10.0
            at_risk.extend(_DISEASES_BY_TRIGGER["temp"])

    # --- NDVI month-over-month drop ---
    ndvi_records = (
        db.query(NDVIResult)
        .filter(NDVIResult.field_id == field.id)
        .order_by(NDVIResult.created_at.asc())
        .all()
    )
    if len(ndvi_records) >= 2:
        older = ndvi_records[-2].ndvi_mean
        newer = ndvi_records[-1].ndvi_mean
        if older > 0 and ((older - newer) / older) > 0.20:
            score += 25.0
            at_risk.extend(_DISEASES_BY_TRIGGER["ndvi_drop"])

    # --- Soil pH ---
    soil = (
        db.query(SoilAnalysis)
        .filter(SoilAnalysis.field_id == field.id)
        .order_by(SoilAnalysis.created_at.desc())
        .first()
    )
    if soil is not None and soil.ph is not None and soil.ph < 5.5:
        score += 15.0
        at_risk.extend(_DISEASES_BY_TRIGGER["ph"])

    # Clamp + level
    risk_score = min(score, 100.0)
    if risk_score <= 25:
        risk_level = "low"
    elif risk_score <= 50:
        risk_level = "medium"
    else:
        risk_level = "high"

    return {
        "risk_level": risk_level,
        "risk_score": round(risk_score, 1),
        "at_risk_diseases": at_risk,
        "assessment_date": date.today().isoformat(),
    }
