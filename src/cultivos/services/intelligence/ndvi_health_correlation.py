"""Field NDVI vs health Pearson correlation (#212).

Pure compute over HealthScore rows (which already carry both `score` and
`ndvi_mean` inline). Filters to the requested window and skips rows with
null ndvi_mean. Fewer than 5 valid pairs → insufficient_data.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from math import sqrt

from sqlalchemy.orm import Session

from cultivos.db.models import HealthScore

MIN_SAMPLES = 5


def _classify(r: float) -> str:
    ar = abs(r)
    if ar >= 0.7:
        return "strong"
    if ar >= 0.4:
        return "moderate"
    if ar >= 0.15:
        return "weak"
    return "none"


def _interpret(strength: str, r: float | None, sample_size: int) -> str:
    if strength == "insufficient_data":
        return (
            "Datos insuficientes — se necesitan al menos 5 lecturas con NDVI "
            "y puntaje de salud."
        )
    assert r is not None
    sign = "positiva" if r >= 0 else "inversa"
    if strength == "strong" and r >= 0:
        return (
            "Correlación positiva fuerte — monitorear NDVI es un indicador "
            "confiable de la salud del cultivo."
        )
    if strength == "strong" and r < 0:
        return (
            "Correlación inversa fuerte — revisar el modelo de salud; NDVI "
            "alto coincide con puntajes bajos."
        )
    if strength == "moderate":
        return (
            f"Correlación {sign} moderada — NDVI explica parte de la "
            "variación en salud, pero no toda."
        )
    if strength == "weak":
        return (
            f"Correlación {sign} débil — NDVI y salud varían casi "
            "independientemente en esta ventana."
        )
    return "No hay correlación significativa entre NDVI y salud en la ventana."


def compute_ndvi_health_correlation(
    field_id: int, period_days: int, db: Session
) -> dict:
    cutoff = datetime.utcnow() - timedelta(days=period_days)
    rows = (
        db.query(HealthScore)
        .filter(HealthScore.field_id == field_id)
        .filter(HealthScore.scored_at >= cutoff)
        .all()
    )
    pairs = [
        (float(r.score), float(r.ndvi_mean))
        for r in rows
        if r.ndvi_mean is not None and r.score is not None
    ]
    n = len(pairs)

    if n < MIN_SAMPLES:
        return {
            "period_days": period_days,
            "sample_size": n,
            "correlation": None,
            "strength": "insufficient_data",
            "interpretation_es": _interpret("insufficient_data", None, n),
            "mean_health": round(sum(p[0] for p in pairs) / n, 4) if n else None,
            "mean_ndvi": round(sum(p[1] for p in pairs) / n, 4) if n else None,
        }

    mean_h = sum(p[0] for p in pairs) / n
    mean_n = sum(p[1] for p in pairs) / n
    cov = sum((p[0] - mean_h) * (p[1] - mean_n) for p in pairs)
    var_h = sum((p[0] - mean_h) ** 2 for p in pairs)
    var_n = sum((p[1] - mean_n) ** 2 for p in pairs)

    denom = sqrt(var_h * var_n)
    if denom == 0:
        r = 0.0
    else:
        r = cov / denom
    # clamp rounding drift
    if r > 1.0:
        r = 1.0
    if r < -1.0:
        r = -1.0

    strength = _classify(r)
    return {
        "period_days": period_days,
        "sample_size": n,
        "correlation": round(r, 4),
        "strength": strength,
        "interpretation_es": _interpret(strength, r, n),
        "mean_health": round(mean_h, 4),
        "mean_ndvi": round(mean_n, 4),
    }
