"""Cooperative sensor freshness rollup.

Composes compute_sensor_freshness per member farm, aggregates field-level
staleness counts, and computes average days-since-last-signal per sensor
type across all fields in the cooperative.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from cultivos.db.models import Cooperative
from cultivos.services.intelligence.sensor_freshness import compute_sensor_freshness


_SENSOR_KEYS = ("ndvi", "soil", "health", "weather")


def _avg_or_none(values: list[int]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def compute_coop_sensor_freshness(cooperative: Cooperative, db: Session) -> dict:
    """Aggregate sensor data freshness across all member farms."""
    sensor_values: dict[str, list[int]] = {k: [] for k in _SENSOR_KEYS}

    farm_entries: list[dict] = []
    total_fields = 0
    fields_with_stale = 0

    for farm in cooperative.farms:
        farm_result = compute_sensor_freshness(farm, db)
        field_items = farm_result["fields"]
        farm_total = len(field_items)
        farm_stale = sum(1 for item in field_items if item["stale_sensors"])

        total_fields += farm_total
        fields_with_stale += farm_stale

        for item in field_items:
            for key in _SENSOR_KEYS:
                val = item[f"{key}_days_ago"]
                if val is not None:
                    sensor_values[key].append(val)

        pct = round((farm_stale / farm_total) * 100, 2) if farm_total > 0 else 0.0
        farm_entries.append({
            "farm_id": farm.id,
            "farm_name": farm.name,
            "total_fields": farm_total,
            "stale_fields": farm_stale,
            "stale_fields_pct": pct,
        })

    avg_by_sensor = {
        key: _avg_or_none(sensor_values[key]) for key in _SENSOR_KEYS
    }

    worst_farm: dict | None = None
    if farm_entries:
        worst = max(
            farm_entries,
            key=lambda fm: (fm["stale_fields_pct"], fm["stale_fields"]),
        )
        worst_farm = {
            "farm_id": worst["farm_id"],
            "farm_name": worst["farm_name"],
            "total_fields": worst["total_fields"],
            "stale_fields": worst["stale_fields"],
            "stale_fields_pct": worst["stale_fields_pct"],
        }

    return {
        "cooperative_id": cooperative.id,
        "farms_count": len(farm_entries),
        "total_fields": total_fields,
        "fields_with_stale_sensors": fields_with_stale,
        "avg_days_since_last_signal": avg_by_sensor,
        "worst_farm": worst_farm,
        "farms": farm_entries,
    }
