"""Multi-sensor fusion validation endpoint."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from cultivos.auth import get_current_user
from cultivos.services.crop.fusion import validate_sensor_fusion

router = APIRouter(
    prefix="/api/analysis",
    tags=["fusion"],
    dependencies=[Depends(get_current_user)]
)


class NDVIPayload(BaseModel):
    ndvi_mean: float = Field(..., ge=0.0, le=1.0)
    ndvi_std: float = Field(0.0, ge=0.0)
    stress_pct: float = Field(0.0, ge=0.0, le=100.0)


class ThermalPayload(BaseModel):
    stress_pct: float = Field(0.0, ge=0.0, le=100.0)
    temp_mean: float = Field(25.0)
    irrigation_deficit: bool = False


class SoilPayload(BaseModel):
    ph: float | None = None
    organic_matter_pct: float | None = None
    nitrogen_ppm: float | None = None
    phosphorus_ppm: float | None = None
    potassium_ppm: float | None = None
    moisture_pct: float | None = None


class WeatherPayload(BaseModel):
    temp_c: float = 25.0
    humidity_pct: float = 50.0
    wind_kmh: float = 0.0


class FusionRequest(BaseModel):
    ndvi: NDVIPayload | None = None
    thermal: ThermalPayload | None = None
    soil: SoilPayload | None = None
    weather: WeatherPayload | None = None


class ContradictionOut(BaseModel):
    tag: str
    sensors: list[str]
    description: str


class FusionResponse(BaseModel):
    contradictions: list[ContradictionOut]
    confidence: float
    sensors_used: list[str]
    assessment: str


@router.post("/fusion", response_model=FusionResponse)
def sensor_fusion(request: FusionRequest):
    """Cross-validate multiple sensor readings for consistency.

    Flags contradictions between sensors (e.g. NDVI healthy but thermal
    stressed) and computes a confidence score based on sensor agreement.
    """
    result = validate_sensor_fusion(
        ndvi=request.ndvi.model_dump() if request.ndvi else None,
        thermal=request.thermal.model_dump() if request.thermal else None,
        soil=request.soil.model_dump() if request.soil else None,
        weather=request.weather.model_dump() if request.weather else None,
    )
    return result
