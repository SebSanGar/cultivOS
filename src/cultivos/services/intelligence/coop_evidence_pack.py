"""Cooperative FODECIJAL evidence pack (task #208).

Composes 6 existing cooperative-level services into a single grant-ready
rollup. Pure composition — zero new ORM models or SQL.

Pillars used for strength/weakness ranking (all normalized 0-100):
    - readiness_score          (fodecijal_readiness.overall_score)
    - portfolio_health_avg     (cooperative_portfolio.avg_health_score)
    - regen_adoption_pct       (regen_adoption.overall_regen_score_avg)
"""

from datetime import datetime

from sqlalchemy.orm import Session

from cultivos.db.models import Cooperative
from cultivos.services.intelligence.carbon_summary import (
    compute_coop_carbon_summary,
)
from cultivos.services.intelligence.coop_crop_diversity import (
    compute_coop_crop_diversity,
)
from cultivos.services.intelligence.cooperative_portfolio import (
    compute_portfolio_health,
)
from cultivos.services.intelligence.fodecijal_readiness import (
    compute_fodecijal_readiness,
)
from cultivos.services.intelligence.outbreak_risk import compute_outbreak_risk
from cultivos.services.intelligence.regen_adoption import compute_regen_adoption

_PILLAR_LABEL_ES = {
    "readiness": "Preparación FODECIJAL",
    "portfolio_health": "Salud promedio del portafolio",
    "regen_adoption": "Adopción regenerativa",
}


def compute_coop_evidence_pack(coop: Cooperative, db: Session) -> dict:
    """Return a single grant-ready rollup composing 6 services."""
    readiness = compute_fodecijal_readiness(coop, db)
    portfolio = compute_portfolio_health(coop, db)
    carbon = compute_coop_carbon_summary(coop, db)
    outbreak = compute_outbreak_risk(coop, db)
    regen = compute_regen_adoption(coop, 30, db)
    diversity = compute_coop_crop_diversity(coop.id, db)

    readiness_score = float(readiness.overall_score)
    portfolio_health_avg = portfolio.get("avg_health_score")
    total_co2e = float(carbon.get("total_co2e_baseline_t", 0.0))
    outbreak_risk_level = outbreak.get("overall_risk_level", "low")
    regen_adoption_pct = float(regen.get("overall_regen_score_avg", 0.0))
    shannon = float(diversity.get("shannon_index", 0.0))

    pillars = {
        "readiness": readiness_score,
        "portfolio_health": (
            float(portfolio_health_avg) if portfolio_health_avg is not None else 0.0
        ),
        "regen_adoption": regen_adoption_pct,
    }

    top_key = max(pillars, key=lambda k: pillars[k])
    low_key = min(pillars, key=lambda k: pillars[k])
    top_strength_es = (
        f"{_PILLAR_LABEL_ES[top_key]} es el pilar más fuerte "
        f"({pillars[top_key]:.1f}/100)."
    )
    top_weakness_es = (
        f"{_PILLAR_LABEL_ES[low_key]} es el pilar más débil "
        f"({pillars[low_key]:.1f}/100) — priorizar para la aplicación FODECIJAL."
    )

    return {
        "cooperative_id": coop.id,
        "cooperative_name": coop.name,
        "readiness_score": round(readiness_score, 2),
        "portfolio_health_avg": portfolio_health_avg,
        "total_co2e_sequestered_t": round(total_co2e, 2),
        "outbreak_risk_level": outbreak_risk_level,
        "regen_adoption_pct": round(regen_adoption_pct, 2),
        "shannon_diversity_index": round(shannon, 4),
        "top_strength_es": top_strength_es,
        "top_weakness_es": top_weakness_es,
        "generated_at": datetime.utcnow(),
    }
