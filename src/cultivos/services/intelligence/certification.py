"""Organic certification readiness service.

Computes a 4-check readiness score indicating how close a farm is to
qualifying for organic certification. All checks are derived from
existing data (TreatmentRecord, SoilAnalysis) — no new data model needed.
"""

from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, SoilAnalysis, TreatmentRecord

# Keywords that indicate a cover crop / living mulch treatment (Spanish)
_COVER_CROP_KEYWORDS = [
    "cobertura",
    "cubierta",
    "abono verde",
    "abono_verde",
    "cover crop",
    "siderata",
    "cultivo de cobertura",
]

# Each cover crop treatment record is treated as ~30 days of coverage
_DAYS_PER_COVER_CROP_RECORD = 30
_COVER_CROP_THRESHOLD_DAYS = 90


def _has_cover_crop(tratamiento: str) -> bool:
    lower = tratamiento.lower()
    return any(kw in lower for kw in _COVER_CROP_KEYWORDS)


def _soc_trend_positive(soil_records: list) -> bool:
    """Return True if organic_matter_pct has a non-negative linear slope.

    Requires at least 2 records with non-None organic_matter_pct.
    """
    points = [
        (r.sampled_at.timestamp(), r.organic_matter_pct)
        for r in soil_records
        if r.organic_matter_pct is not None
    ]
    if len(points) < 2:
        return False

    points.sort(key=lambda p: p[0])
    n = len(points)
    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    sum_xy = sum(p[0] * p[1] for p in points)
    sum_xx = sum(p[0] * p[0] for p in points)

    denom = n * sum_xx - sum_x * sum_x
    if denom == 0:
        return True  # flat line = stable = no decline
    slope = (n * sum_xy - sum_x * sum_y) / denom
    return slope >= 0.0


def compute_certification_readiness(farm_id: int, db: Session) -> dict | None:
    """Compute organic certification readiness for a farm.

    Returns None if farm not found (signals 404 to caller).

    Checks:
    1. synthetic_inputs_free    — no TreatmentRecord with organic=False
    2. treatment_organic_only   — same as above (alias for certification language)
    3. soc_trend_positive       — soil organic carbon trend >= 0 (needs 2+ soil records)
    4. cover_crop_days_gte_90   — cover crop treatment records × 30 days >= 90

    overall_pct = (count of True checks / 4) × 100
    """
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if farm is None:
        return None

    fields = db.query(Field).filter(Field.farm_id == farm_id).all()
    field_ids = [f.id for f in fields]

    if not field_ids:
        return {
            "synthetic_inputs_free": True,
            "treatment_organic_only": True,
            "soc_trend_positive": False,
            "cover_crop_days_gte_90": False,
            "overall_pct": 50.0,
        }

    # --- Fetch all treatment records across the farm ---
    treatments = (
        db.query(TreatmentRecord)
        .filter(TreatmentRecord.field_id.in_(field_ids))
        .all()
    )

    # Check 1 + 2: all treatments must be organic
    has_synthetic = any(not t.organic for t in treatments)
    synthetic_inputs_free = not has_synthetic
    treatment_organic_only = synthetic_inputs_free

    # Check 4: cover crop days proxy
    cover_crop_count = sum(1 for t in treatments if _has_cover_crop(t.tratamiento))
    cover_crop_days = cover_crop_count * _DAYS_PER_COVER_CROP_RECORD
    cover_crop_days_gte_90 = cover_crop_days >= _COVER_CROP_THRESHOLD_DAYS

    # Check 3: SOC trend across all soil analyses for the farm
    soil_records = (
        db.query(SoilAnalysis)
        .filter(SoilAnalysis.field_id.in_(field_ids))
        .order_by(SoilAnalysis.sampled_at)
        .all()
    )
    soc_trend_positive = _soc_trend_positive(soil_records)

    checks = [
        synthetic_inputs_free,
        treatment_organic_only,
        soc_trend_positive,
        cover_crop_days_gte_90,
    ]
    # synthetic_inputs_free and treatment_organic_only are the same check — count as 2
    passing = sum(1 for c in checks if c)
    overall_pct = round(passing / len(checks) * 100, 1)

    return {
        "synthetic_inputs_free": synthetic_inputs_free,
        "treatment_organic_only": treatment_organic_only,
        "soc_trend_positive": soc_trend_positive,
        "cover_crop_days_gte_90": cover_crop_days_gte_90,
        "overall_pct": overall_pct,
    }
