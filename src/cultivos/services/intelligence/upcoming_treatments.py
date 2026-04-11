"""Per-field upcoming treatment schedule service — pure function, no HTTP, no side effects.

Suggests up to 3 upcoming treatment windows based on:
1. Days since last treatment (minimum interval enforcement)
2. Current crop growth stage (critical stages trigger sooner windows)
3. Seasonal calendar context

Degrades gracefully: no phenology → generic 30/60/90-day schedule.
"""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from cultivos.db.models import Field, TreatmentRecord
from cultivos.models.upcoming_treatments import UpcomingTreatmentOut
from cultivos.services.crop.phenology import compute_growth_stage

# Minimum days between treatments (prevent over-application)
MIN_INTERVAL_DAYS = 21

# Growth stages that shorten the next treatment window (Spanish — from phenology.py)
CRITICAL_STAGES = {"siembra", "floracion", "fructificacion"}

# Generic treatment sequence for fields without phenology data
GENERIC_SCHEDULE = [
    ("fertilizacion", 30, "Aplicacion de composta organica — mantenimiento mensual de fertilidad."),
    ("monitoreo_plagas", 60, "Revision de plagas y enfermedades — evaluacion cada dos meses."),
    ("riego_ajuste", 90, "Ajuste de riego segun condicion del suelo — revision trimestral."),
]

# Stage-specific treatment advice (Spanish stage names from phenology.py)
STAGE_ADVICE: dict[str, tuple[str, str]] = {
    "siembra": (
        "riego_cuidadoso",
        "Siembra en curso — riego ligero para establecer plantula sin anegar.",
    ),
    "vegetativo": (
        "fertilizacion_nitrogeno",
        "Etapa vegetativa — aplicar nitrogeno organico (composta o guano) para impulsar follaje.",
    ),
    "floracion": (
        "control_plagas",
        "Floracion — revision urgente de plagas y polinizadores. Evitar aplicaciones que danen flores.",
    ),
    "fructificacion": (
        "riego_constante",
        "Fructificacion — mantener humedad constante para maximizar rendimiento.",
    ),
    "cosecha": (
        "preparacion_cosecha",
        "Madurez proxima — preparar equipo de cosecha y reducir riego gradualmente.",
    ),
}


def _days_since_last_treatment(db: Session, field_id: int) -> int | None:
    """Return days since the most recent treatment, or None if no treatments."""
    last = (
        db.query(TreatmentRecord)
        .filter(TreatmentRecord.field_id == field_id)
        .order_by(TreatmentRecord.created_at.desc())
        .first()
    )
    if last is None:
        return None
    ref = last.applied_at or last.created_at
    if ref is None:
        return None
    return (date.today() - ref.date()).days


def compute_upcoming_treatments(
    field: Field, db: Session
) -> list[UpcomingTreatmentOut]:
    """Suggest up to 3 upcoming treatment windows for a field."""
    days_since = _days_since_last_treatment(db, field.id)

    # Determine base offset: if treated recently, push first window out
    if days_since is not None and days_since < MIN_INTERVAL_DAYS:
        base_offset = MIN_INTERVAL_DAYS - days_since
    else:
        base_offset = 0

    # Try to get phenology stage
    stage_result = compute_growth_stage(field.crop_type, field.planted_at)

    if stage_result is None:
        # No phenology data — return generic schedule offset by base_offset
        windows = []
        for treatment_type, day_offset, reason in GENERIC_SCHEDULE:
            rec_date = date.today() + timedelta(days=max(base_offset, day_offset))
            windows.append(UpcomingTreatmentOut(
                treatment_type=treatment_type,
                recommended_date=rec_date.isoformat(),
                reason_es=reason,
            ))
        return windows

    # Phenology-aware schedule
    stage_name = stage_result.get("stage") or ""
    is_critical = stage_name in CRITICAL_STAGES

    windows: list[UpcomingTreatmentOut] = []

    # Window 1: stage-specific advice (sooner if critical stage)
    w1_offset = max(base_offset, 0 if is_critical else 7)
    stage_type, stage_reason = STAGE_ADVICE.get(
        stage_name,
        ("inspeccion_general", f"Inspeccion general del cultivo de {field.crop_type or 'cultivo'}."),
    )
    windows.append(UpcomingTreatmentOut(
        treatment_type=stage_type,
        recommended_date=(date.today() + timedelta(days=w1_offset)).isoformat(),
        reason_es=stage_reason,
    ))

    # Window 2: preventive fertilization (3 weeks after w1)
    w2_offset = w1_offset + 21
    windows.append(UpcomingTreatmentOut(
        treatment_type="fertilizacion_preventiva",
        recommended_date=(date.today() + timedelta(days=w2_offset)).isoformat(),
        reason_es=(
            f"Fertilizacion preventiva con composta organica — "
            f"mantener nutricion del suelo para {field.crop_type or 'cultivo'}."
        ),
    ))

    # Window 3: monitoring check (6 weeks after w1)
    w3_offset = w1_offset + 42
    windows.append(UpcomingTreatmentOut(
        treatment_type="monitoreo_general",
        recommended_date=(date.today() + timedelta(days=w3_offset)).isoformat(),
        reason_es=(
            "Monitoreo general de salud del campo — revision de plagas, "
            "enfermedades y condicion del suelo antes de la siguiente fase."
        ),
    ))

    return windows
