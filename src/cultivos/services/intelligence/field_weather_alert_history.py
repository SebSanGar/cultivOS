"""Field weather alert history aggregator (#209).

Replays detect_weather_alerts over the farm's WeatherRecord rows in the
window, then aggregates by alert_type. Per-type stats: count, dominant
severity (critica vs moderada — whichever has more occurrences),
last_alert_at. Window-level stats: total_alerts, most_frequent_type,
alerts_per_month_avg, first-half-vs-second-half trend.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from cultivos.db.models import WeatherRecord
from cultivos.services.intelligence.weather_alerts import detect_weather_alerts


def compute_field_weather_alert_history(
    farm_id: int, period_days: int, db: Session
) -> dict:
    cutoff = datetime.utcnow() - timedelta(days=period_days)
    half = datetime.utcnow() - timedelta(days=period_days / 2)

    records = (
        db.query(WeatherRecord)
        .filter(WeatherRecord.farm_id == farm_id)
        .filter(WeatherRecord.recorded_at >= cutoff)
        .order_by(WeatherRecord.recorded_at.asc())
        .all()
    )

    # type → {count, last_at, severity_counts: {critica, moderada}}
    by_type: dict[str, dict] = {}
    first_half_count = 0
    second_half_count = 0

    for rec in records:
        alerts = detect_weather_alerts(
            temp_c=rec.temp_c,
            humidity_pct=rec.humidity_pct,
            wind_kmh=rec.wind_kmh,
            rainfall_mm=rec.rainfall_mm,
            description=rec.description or "",
            forecast_3day=None,  # historical replay — only "current" alerts
        )
        # Only count "current"-source alerts; forecasts would double-count
        # against later rows.
        for alert in alerts:
            if alert.get("source") != "current":
                continue
            atype = alert["alert_type"]
            sev = alert.get("severity", "moderada")
            entry = by_type.setdefault(
                atype,
                {"count": 0, "last_at": None, "severity": {"critica": 0, "moderada": 0}},
            )
            entry["count"] += 1
            entry["severity"][sev] = entry["severity"].get(sev, 0) + 1
            if entry["last_at"] is None or rec.recorded_at > entry["last_at"]:
                entry["last_at"] = rec.recorded_at

            if rec.recorded_at < half:
                first_half_count += 1
            else:
                second_half_count += 1

    summary = []
    for atype, entry in sorted(by_type.items(), key=lambda kv: -kv[1]["count"]):
        sev_counts = entry["severity"]
        dominant = (
            "critica"
            if sev_counts.get("critica", 0) >= sev_counts.get("moderada", 0)
            and sev_counts.get("critica", 0) > 0
            else "moderada"
        )
        summary.append(
            {
                "alert_type": atype,
                "count": entry["count"],
                "last_alert_at": entry["last_at"].isoformat() if entry["last_at"] else None,
                "dominant_severity": dominant,
            }
        )

    total = sum(s["count"] for s in summary)
    most_frequent = summary[0]["alert_type"] if summary else None
    months = period_days / 30.0 if period_days > 0 else 1.0
    per_month = round(total / months, 4) if months > 0 else 0.0

    if total == 0:
        trend = "stable"
    elif second_half_count > first_half_count:
        trend = "rising"
    elif second_half_count < first_half_count:
        trend = "falling"
    else:
        trend = "stable"

    return {
        "period_days": period_days,
        "total_alerts": total,
        "by_type": summary,
        "most_frequent_type": most_frequent,
        "alerts_per_month_avg": per_month,
        "trend": trend,
    }
