"""Health score volatility service.

Computes the population standard deviation of HealthScore.score values over the
last 60 days for a given field. Low std dev = stable management; high = erratic
or crisis-prone field.

Volatility tiers:
  stable           — std_dev < 5
  moderate         — 5 <= std_dev <= 15
  volatile         — std_dev > 15
  insufficient_data — fewer than 2 scores in the 60-day window
"""

from __future__ import annotations

import statistics
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from cultivos.db.models import Field, HealthScore

_PERIOD_DAYS = 60


_INTERPRETATIONS = {
    "stable": (
        "Campo estable — las puntuaciones de salud son consistentes. "
        "Continuar con el manejo actual."
    ),
    "moderate": (
        "Variabilidad moderada — el campo muestra fluctuaciones ocasionales. "
        "Monitorear causas de variación y ajustar manejo preventivo."
    ),
    "volatile": (
        "Campo inestable — puntuaciones de salud muy variables. "
        "Investigar factores de estrés recurrentes e implementar manejo correctivo urgente."
    ),
    "insufficient_data": (
        "Datos insuficientes — se requieren al menos 2 registros de salud "
        f"en los últimos {_PERIOD_DAYS} días para calcular volatilidad."
    ),
}


def compute_health_volatility(field: Field, db: Session) -> dict:
    """Compute health score volatility for the field over the last 60 days."""
    cutoff = datetime.utcnow() - timedelta(days=_PERIOD_DAYS)

    scores_q = (
        db.query(HealthScore.score)
        .filter(
            HealthScore.field_id == field.id,
            HealthScore.scored_at >= cutoff,
        )
        .order_by(HealthScore.scored_at.asc())
        .all()
    )
    scores = [row.score for row in scores_q]
    count = len(scores)

    if count < 2:
        return {
            "field_id": field.id,
            "period_days": _PERIOD_DAYS,
            "score_count": count,
            "mean_health": round(scores[0], 1) if count == 1 else None,
            "std_dev": None,
            "volatility_tier": "insufficient_data",
            "interpretation_es": _INTERPRETATIONS["insufficient_data"],
        }

    mean = statistics.mean(scores)
    std = statistics.pstdev(scores)  # population std dev (not sample)

    if std < 5.0:
        tier = "stable"
    elif std <= 15.0:
        tier = "moderate"
    else:
        tier = "volatile"

    return {
        "field_id": field.id,
        "period_days": _PERIOD_DAYS,
        "score_count": count,
        "mean_health": round(mean, 1),
        "std_dev": round(std, 2),
        "volatility_tier": tier,
        "interpretation_es": _INTERPRETATIONS[tier],
    }
