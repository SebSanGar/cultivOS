"""Soil carbon tracking endpoints — per-field and per-farm aggregates."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, SoilAnalysis
from cultivos.db.session import get_db
from cultivos.models.carbon import CarbonReportOut, FarmCarbonSummaryOut, SOCEstimateOut
from cultivos.services.intelligence.analytics import compute_farm_carbon_summary
from cultivos.services.intelligence.carbon import estimate_soc, compute_carbon_trend

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}/carbon",
    tags=["carbon"],
)

farm_carbon_router = APIRouter(
    prefix="/api/farms/{farm_id}/carbon",
    tags=["carbon"],
)


@farm_carbon_router.get("", response_model=FarmCarbonSummaryOut)
def get_farm_carbon_summary(
    farm_id: int,
    db: Session = Depends(get_db),
):
    """Aggregate carbon sequestration across all fields in a farm — SOC, CO2e, trend per field."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return compute_farm_carbon_summary(db, farm_id)


def _get_field(farm_id: int, field_id: int, db: Session) -> Field:
    """Validate farm and field exist."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.get("", response_model=CarbonReportOut)
def get_carbon_report(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """Get soil carbon report for a field — SOC estimate, trend, and recommendations."""
    field = _get_field(farm_id, field_id, db)

    # Fetch soil analyses with organic matter data, ordered by date
    soil_records = (
        db.query(SoilAnalysis)
        .filter(
            SoilAnalysis.field_id == field_id,
            SoilAnalysis.organic_matter_pct.isnot(None),
        )
        .order_by(SoilAnalysis.sampled_at.asc())
        .all()
    )

    if not soil_records:
        return CarbonReportOut(
            field_id=field_id,
            soc_actual=None,
            tendencia="datos_insuficientes",
            cambio_soc_tonnes_per_ha=0.0,
            registros=0,
            recomendaciones=[],
            resumen="No hay datos de materia organica disponibles para este campo. "
                    "Realice un analisis de suelo para obtener su reporte de carbono.",
        )

    # Latest SOC estimate
    latest = soil_records[-1]
    soc_current = estimate_soc(
        organic_matter_pct=float(latest.organic_matter_pct),
        depth_cm=float(latest.depth_cm or 30.0),
    )

    # Build records for trend computation
    trend_records = [
        {
            "organic_matter_pct": float(r.organic_matter_pct),
            "depth_cm": float(r.depth_cm or 30.0),
            "sampled_at": r.sampled_at.isoformat() if hasattr(r.sampled_at, 'isoformat') else str(r.sampled_at),
        }
        for r in soil_records
    ]

    trend = compute_carbon_trend(trend_records)

    # Generate Spanish summary
    resumen = _generate_summary(field.name, soc_current, trend)

    return CarbonReportOut(
        field_id=field_id,
        soc_actual=SOCEstimateOut(**soc_current),
        tendencia=trend["tendencia"],
        cambio_soc_tonnes_per_ha=trend["cambio_soc_tonnes_per_ha"],
        registros=trend["registros"],
        recomendaciones=trend["recomendaciones"],
        resumen=resumen,
    )


def _generate_summary(
    field_name: str,
    soc: dict,
    trend: dict,
) -> str:
    """Generate a farmer-friendly Spanish summary of the carbon report."""
    clasificacion_text = {
        "bajo": "bajo (necesita atencion)",
        "adecuado": "adecuado",
        "alto": "alto (excelente)",
    }

    tendencia_text = {
        "ganando": "Su suelo esta ganando carbono — las practicas regenerativas estan funcionando.",
        "estable": "El carbono del suelo se mantiene estable.",
        "perdiendo": "Su suelo esta perdiendo carbono — se recomienda incorporar practicas regenerativas.",
        "datos_insuficientes": "Se necesitan mas analisis de suelo para determinar la tendencia.",
    }

    nivel = clasificacion_text.get(soc["clasificacion"], soc["clasificacion"])
    tendencia_msg = tendencia_text.get(trend["tendencia"], "")

    resumen = (
        f"Campo \"{field_name}\": carbono organico del suelo estimado en "
        f"{soc['soc_tonnes_per_ha']} toneladas por hectarea (nivel {nivel}). "
        f"{tendencia_msg}"
    )

    if trend["tendencia"] == "ganando":
        cambio = abs(trend["cambio_soc_tonnes_per_ha"])
        resumen += f" Ganancia de {cambio} t/ha desde el primer analisis."

    return resumen
