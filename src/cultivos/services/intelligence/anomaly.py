"""Pure anomaly detection — data in, anomalies out. No HTTP, no DB, no side effects.

Detects health score drops and NDVI anomalies from chronological records.
Returns structured anomaly dicts with Spanish-language recommendations.
"""

from datetime import datetime
from typing import TypedDict


HEALTH_DROP_THRESHOLD = 15  # points drop between consecutive scores
NDVI_DROP_THRESHOLD = 0.20  # 20% below historical average


class AnomalyResult(TypedDict):
    type: str  # health_drop, ndvi_drop
    field_name: str
    recommendation: str


def detect_health_anomalies(
    scores: list[dict],
    field_name: str,
) -> list[dict]:
    """Detect health score anomalies from chronological score records.

    Args:
        scores: list of dicts with 'score' (float) and 'scored_at' (datetime),
                ordered by scored_at ascending.
        field_name: name of the field (for messages).

    Returns:
        list of anomaly dicts with type, drop, field_name, recommendation.
    """
    if len(scores) < 2:
        return []

    # Sort by scored_at to ensure chronological order
    sorted_scores = sorted(scores, key=lambda s: s["scored_at"])

    anomalies = []
    for i in range(1, len(sorted_scores)):
        prev = sorted_scores[i - 1]["score"]
        curr = sorted_scores[i]["score"]
        drop = prev - curr

        if drop > HEALTH_DROP_THRESHOLD:
            anomalies.append({
                "type": "health_drop",
                "field_name": field_name,
                "drop": drop,
                "previous_score": prev,
                "current_score": curr,
                "recommendation": (
                    f"Alerta: {field_name} bajo {drop:.0f} puntos de salud "
                    f"(de {prev:.0f} a {curr:.0f}). "
                    f"Revise el campo y considere analisis de suelo o vuelo de dron."
                ),
            })

    return anomalies


def detect_ndvi_anomalies(
    ndvi_records: list[dict],
    field_name: str,
) -> list[dict]:
    """Detect NDVI anomalies when latest reading drops >20% below historical average.

    Args:
        ndvi_records: list of dicts with 'ndvi_mean' (float) and 'analyzed_at' (datetime).
        field_name: name of the field (for messages).

    Returns:
        list of anomaly dicts with type, current_ndvi, historical_avg, field_name, recommendation.
    """
    if len(ndvi_records) < 2:
        return []

    # Sort by analyzed_at
    sorted_records = sorted(ndvi_records, key=lambda r: r["analyzed_at"])

    # Historical average = all records except the latest
    historical = sorted_records[:-1]
    latest = sorted_records[-1]

    hist_avg = sum(r["ndvi_mean"] for r in historical) / len(historical)

    if hist_avg <= 0:
        return []

    drop_pct = (hist_avg - latest["ndvi_mean"]) / hist_avg

    anomalies = []
    if drop_pct > NDVI_DROP_THRESHOLD:
        anomalies.append({
            "type": "ndvi_drop",
            "field_name": field_name,
            "current_ndvi": latest["ndvi_mean"],
            "historical_avg": round(hist_avg, 4),
            "drop_pct": round(drop_pct * 100, 1),
            "recommendation": (
                f"Alerta: {field_name} muestra caida de NDVI del {drop_pct * 100:.0f}% "
                f"respecto al promedio historico ({hist_avg:.2f} → {latest['ndvi_mean']:.2f}). "
                f"Programe un vuelo de dron para inspeccionar el campo."
            ),
        })

    return anomalies
