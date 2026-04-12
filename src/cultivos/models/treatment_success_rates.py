from pydantic import BaseModel


class TreatmentSuccessRateItem(BaseModel):
    crop_type: str
    problema: str
    avg_health_delta: float
    success_rate_pct: float
    treatment_count: int
