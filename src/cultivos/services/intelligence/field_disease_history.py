"""Service: field pest/disease history summary (#204).

Aggregates disease-risk triggers per month over the last N months using
WeatherRecord + NDVIResult + SoilAnalysis data. Each trigger maps to ONE
canonical disease name so monthly counts stay clean.

Triggers mirror compute_disease_risk_assessment thresholds:
- humidity_pct > 70  → "Tizón tardío"
- temp_c > 35        → "Estrés por calor"
- NDVI MoM drop >20% → "Cogollero del maíz"
- soil ph < 5.5      → "Marchitez por Fusarium"
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from cultivos.db.models import Field, NDVIResult, SoilAnalysis, WeatherRecord
from cultivos.models.field_disease_history import (
    DiseaseHistoryMonth,
    FieldDiseaseHistoryOut,
)


_TRIGGER_DISEASE: dict[str, str] = {
    "humidity": "Tizón tardío",
    "temp": "Estrés por calor",
    "ndvi_drop": "Cogollero del maíz",
    "ph": "Marchitez por Fusarium",
}


def _month_key(dt: datetime) -> str:
    return f"{dt.year:04d}-{dt.month:02d}"


def _shift_months(dt: datetime, delta: int) -> datetime:
    """Return a datetime at the first of (dt's month + delta)."""
    total = dt.year * 12 + (dt.month - 1) + delta
    year, month = divmod(total, 12)
    return datetime(year, month + 1, 1)


def compute_field_disease_history(
    field: Field,
    db: Session,
    months: int = 12,
) -> FieldDiseaseHistoryOut:
    """Return monthly disease history for a field over the last `months` months."""
    now = datetime.utcnow()
    # Build the ordered month keys: oldest first, most recent last.
    month_keys: list[str] = []
    for i in range(months - 1, -1, -1):
        month_keys.append(_month_key(_shift_months(now, -i)))

    window_start = _shift_months(now, -(months - 1))

    # --- Weather records in window, grouped by month ---
    weather_rows = (
        db.query(WeatherRecord)
        .filter(
            WeatherRecord.farm_id == field.farm_id,
            WeatherRecord.recorded_at >= window_start,
        )
        .all()
    )
    weather_by_month: dict[str, list[WeatherRecord]] = {}
    for w in weather_rows:
        weather_by_month.setdefault(_month_key(w.recorded_at), []).append(w)

    # --- Soil analyses in window, grouped by month ---
    soil_rows = (
        db.query(SoilAnalysis)
        .filter(
            SoilAnalysis.field_id == field.id,
            SoilAnalysis.created_at >= window_start,
        )
        .all()
    )
    soil_by_month: dict[str, list[SoilAnalysis]] = {}
    for s in soil_rows:
        soil_by_month.setdefault(_month_key(s.created_at), []).append(s)

    # --- NDVI records in window + the most recent prior-window record for MoM seed ---
    ndvi_rows = (
        db.query(NDVIResult)
        .filter(
            NDVIResult.field_id == field.id,
            NDVIResult.created_at >= window_start,
        )
        .order_by(NDVIResult.created_at.asc())
        .all()
    )
    ndvi_by_month: dict[str, list[float]] = {}
    for n in ndvi_rows:
        ndvi_by_month.setdefault(_month_key(n.created_at), []).append(n.ndvi_mean)
    prior_ndvi = (
        db.query(NDVIResult)
        .filter(
            NDVIResult.field_id == field.id,
            NDVIResult.created_at < window_start,
        )
        .order_by(NDVIResult.created_at.desc())
        .first()
    )
    prior_avg: Optional[float] = prior_ndvi.ndvi_mean if prior_ndvi else None

    monthly: list[DiseaseHistoryMonth] = []
    disease_counter: Counter[str] = Counter()
    months_disease_free = 0

    last_monthly_ndvi: Optional[float] = prior_avg
    for key in month_keys:
        triggers: list[str] = []

        for w in weather_by_month.get(key, []):
            if w.humidity_pct > 70.0 and "humidity" not in triggers:
                triggers.append("humidity")
            if w.temp_c > 35.0 and "temp" not in triggers:
                triggers.append("temp")

        soil_list = soil_by_month.get(key, [])
        if any(s.ph is not None and s.ph < 5.5 for s in soil_list):
            triggers.append("ph")

        ndvi_list = ndvi_by_month.get(key, [])
        if ndvi_list:
            month_avg = sum(ndvi_list) / len(ndvi_list)
            if (
                last_monthly_ndvi is not None
                and last_monthly_ndvi > 0
                and ((last_monthly_ndvi - month_avg) / last_monthly_ndvi) > 0.20
            ):
                triggers.append("ndvi_drop")
            last_monthly_ndvi = month_avg

        diseases = [_TRIGGER_DISEASE[t] for t in triggers]
        for d in diseases:
            disease_counter[d] += 1
        if not diseases:
            months_disease_free += 1

        monthly.append(
            DiseaseHistoryMonth(
                month=key,
                triggers=triggers,
                diseases=diseases,
                disease_count=len(diseases),
            )
        )

    disease_counts = dict(disease_counter)
    most_common_disease = (
        disease_counter.most_common(1)[0][0] if disease_counter else None
    )
    recurring_diseases = sorted(
        [name for name, count in disease_counter.items() if count >= 2]
    )
    recurrence_detected = len(recurring_diseases) > 0

    return FieldDiseaseHistoryOut(
        farm_id=field.farm_id,
        field_id=field.id,
        months=months,
        total_months_analyzed=len(month_keys),
        monthly=monthly,
        disease_counts=disease_counts,
        most_common_disease=most_common_disease,
        recurring_diseases=recurring_diseases,
        recurrence_detected=recurrence_detected,
        months_disease_free=months_disease_free,
    )
