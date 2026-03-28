"""Regenerative practice verification — scores how regenerative a field's management is."""

from sqlalchemy.orm import Session

from cultivos.db.models import (
    Field, TreatmentRecord, SoilAnalysis, MicrobiomeRecord,
)

# Component weights (total = 100)
WEIGHT_ORGANIC = 25       # % of treatments that are organic
WEIGHT_ANCESTRAL = 20     # usage of ancestral/TEK methods
WEIGHT_SOIL_TREND = 25    # soil organic matter improving over time
WEIGHT_MICROBIOME = 20    # microbiome health classification
WEIGHT_DIVERSITY = 10     # treatment diversity (different methods used)


def compute_regenerative_score(field_id: int, db: Session) -> dict:
    """Compute regenerative practice score 0-100 for a field.

    Returns dict with score, breakdown per component, and Spanish recommendations.
    """
    treatments = (
        db.query(TreatmentRecord)
        .filter(TreatmentRecord.field_id == field_id)
        .order_by(TreatmentRecord.created_at.desc())
        .all()
    )
    soil_analyses = (
        db.query(SoilAnalysis)
        .filter(SoilAnalysis.field_id == field_id)
        .order_by(SoilAnalysis.sampled_at.asc())
        .all()
    )
    latest_microbiome = (
        db.query(MicrobiomeRecord)
        .filter(MicrobiomeRecord.field_id == field_id)
        .order_by(MicrobiomeRecord.sampled_at.desc())
        .first()
    )

    breakdown = {
        "organic_treatments": _score_organic(treatments),
        "ancestral_methods": _score_ancestral(treatments),
        "soil_organic_trend": _score_soil_trend(soil_analyses),
        "microbiome_health": _score_microbiome(latest_microbiome),
        "treatment_diversity": _score_diversity(treatments),
    }

    score = sum(breakdown.values())
    recommendations = _generate_recommendations(breakdown, treatments, soil_analyses, latest_microbiome)

    return {
        "score": round(score, 1),
        "breakdown": breakdown,
        "recommendations": recommendations,
    }


def _score_organic(treatments: list) -> float:
    """Score based on % of treatments that are organic. Full marks = 100% organic."""
    if not treatments:
        return 0.0
    organic_count = sum(1 for t in treatments if t.organic)
    ratio = organic_count / len(treatments)
    return round(ratio * WEIGHT_ORGANIC, 1)


def _score_ancestral(treatments: list) -> float:
    """Score based on usage of ancestral/TEK methods in treatments."""
    if not treatments:
        return 0.0
    ancestral_count = sum(1 for t in treatments if t.ancestral_method_name)
    ratio = ancestral_count / len(treatments)
    return round(ratio * WEIGHT_ANCESTRAL, 1)


def _score_soil_trend(soil_analyses: list) -> float:
    """Score based on soil organic matter trend (improving = full marks)."""
    if len(soil_analyses) < 2:
        return 0.0

    first_om = soil_analyses[0].organic_matter_pct
    last_om = soil_analyses[-1].organic_matter_pct

    if first_om is None or last_om is None:
        return 0.0

    if last_om > first_om:
        # Improving — scale by magnitude of improvement (cap at 2% improvement = full marks)
        improvement = min((last_om - first_om) / 2.0, 1.0)
        return round(improvement * WEIGHT_SOIL_TREND, 1)
    elif last_om == first_om:
        # Stable — partial credit
        return round(WEIGHT_SOIL_TREND * 0.3, 1)
    else:
        # Declining — no credit
        return 0.0


def _score_microbiome(record) -> float:
    """Score based on latest microbiome classification."""
    if not record:
        return 0.0

    scores = {"healthy": 1.0, "moderate": 0.5, "degraded": 0.1}
    ratio = scores.get(record.classification, 0.0)
    return round(ratio * WEIGHT_MICROBIOME, 1)


def _score_diversity(treatments: list) -> float:
    """Score based on diversity of treatment methods used."""
    if not treatments:
        return 0.0

    unique_methods = set()
    for t in treatments:
        if t.ancestral_method_name:
            unique_methods.add(t.ancestral_method_name)
        else:
            unique_methods.add(t.tratamiento[:30])

    # 1 method = 20%, 2 = 50%, 3+ = 100%
    if len(unique_methods) >= 3:
        ratio = 1.0
    elif len(unique_methods) == 2:
        ratio = 0.5
    else:
        ratio = 0.2

    return round(ratio * WEIGHT_DIVERSITY, 1)


def _generate_recommendations(
    breakdown: dict,
    treatments: list,
    soil_analyses: list,
    microbiome,
) -> list[str]:
    """Generate Spanish-language recommendations for improving regenerative score."""
    recs = []

    if breakdown["organic_treatments"] < WEIGHT_ORGANIC * 0.8:
        if not treatments:
            recs.append(
                "No hay registros de tratamientos. Comience con prácticas orgánicas "
                "como composta o abonos verdes para mejorar la salud del suelo."
            )
        else:
            non_organic = sum(1 for t in treatments if not t.organic)
            recs.append(
                f"Se detectaron {non_organic} tratamientos no orgánicos. "
                "Sustituya por alternativas orgánicas como biofertilizantes, "
                "extractos de neem o composta enriquecida."
            )

    if breakdown["ancestral_methods"] < WEIGHT_ANCESTRAL * 0.5:
        recs.append(
            "Incorpore métodos ancestrales como la Milpa (maíz-frijol-calabaza), "
            "chinampas o el uso de ceniza volcánica para fortalecer la biodiversidad del suelo."
        )

    if breakdown["soil_organic_trend"] == 0:
        if len(soil_analyses) < 2:
            recs.append(
                "Se necesitan al menos 2 análisis de suelo para evaluar la tendencia "
                "de materia orgánica. Realice un análisis cada 6 meses."
            )
        else:
            recs.append(
                "La materia orgánica del suelo no está mejorando. Aplique composta, "
                "abonos verdes o cultivos de cobertura para incrementarla."
            )

    if breakdown["microbiome_health"] == 0:
        recs.append(
            "No hay datos de microbioma del suelo. Un análisis de actividad microbiana "
            "ayuda a evaluar la salud biológica del suelo y guiar intervenciones."
        )
    elif breakdown["microbiome_health"] < WEIGHT_MICROBIOME * 0.5:
        recs.append(
            "El microbioma del suelo necesita atención. Considere inoculantes micorrízicos, "
            "reducir la labranza y aumentar la diversidad de cultivos de cobertura."
        )

    if breakdown["treatment_diversity"] < WEIGHT_DIVERSITY * 0.5:
        recs.append(
            "Diversifique las prácticas de manejo: combine rotación de cultivos, "
            "cultivos de cobertura, composta y control biológico de plagas."
        )

    return recs
