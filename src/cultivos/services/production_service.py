"""Production scheduling service — calendars, par levels, production entries."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from cultivos.db.models import (
    ParLevel,
    ProductionCalendar,
    ProductionEntry,
    Recipe,
    ShelfLifeTracker,
)
from cultivos.models.production import (
    ParLevelCreate,
    ProductionCalendarCreate,
    ProductionEntryCreate,
    ProductionEntryUpdate,
    ProductionNeed,
)


# ---------------------------------------------------------------------------
# Par levels
# ---------------------------------------------------------------------------

def set_par_level(db: Session, data: ParLevelCreate) -> ParLevel:
    existing = db.query(ParLevel).filter(
        ParLevel.recipe_id == data.recipe_id,
        ParLevel.location_id == data.location_id,
    ).first()

    effective = data.base_par + data.safety_buffer

    if existing:
        existing.base_par = data.base_par
        existing.safety_buffer = data.safety_buffer
        existing.effective_par = effective
        existing.last_reviewed = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing

    par = ParLevel(
        recipe_id=data.recipe_id,
        location_id=data.location_id,
        base_par=data.base_par,
        safety_buffer=data.safety_buffer,
        effective_par=effective,
    )
    db.add(par)
    db.commit()
    db.refresh(par)
    return par


def list_par_levels(db: Session, location_id: int) -> list[ParLevel]:
    return (
        db.query(ParLevel)
        .filter(ParLevel.location_id == location_id)
        .all()
    )


# ---------------------------------------------------------------------------
# Production calendar
# ---------------------------------------------------------------------------

def create_calendar(db: Session, data: ProductionCalendarCreate) -> ProductionCalendar:
    cal = ProductionCalendar(
        location_id=data.location_id,
        week_start_date=data.week_start_date,
    )
    db.add(cal)
    db.commit()
    db.refresh(cal)
    return cal


def get_calendar(db: Session, calendar_id: int) -> ProductionCalendar | None:
    return db.query(ProductionCalendar).filter(
        ProductionCalendar.id == calendar_id
    ).first()


# ---------------------------------------------------------------------------
# Production entries
# ---------------------------------------------------------------------------

def add_entry(db: Session, calendar_id: int, data: ProductionEntryCreate) -> ProductionEntry | None:
    cal = db.query(ProductionCalendar).filter(ProductionCalendar.id == calendar_id).first()
    if not cal:
        return None

    entry = ProductionEntry(
        calendar_id=calendar_id,
        recipe_id=data.recipe_id,
        planned_quantity=data.planned_quantity,
        scheduled_date=data.scheduled_date,
        slot=data.slot,
        assigned_to=data.assigned_to,
        notes=data.notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def update_entry(db: Session, entry_id: int, data: ProductionEntryUpdate) -> ProductionEntry | None:
    entry = db.query(ProductionEntry).filter(ProductionEntry.id == entry_id).first()
    if not entry:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(entry, key, value)

    db.commit()
    db.refresh(entry)
    return entry


# ---------------------------------------------------------------------------
# Production needs
# ---------------------------------------------------------------------------

def get_production_needs(db: Session, location_id: int) -> list[ProductionNeed]:
    """Calculate what needs to be produced: par_level - current_stock."""
    pars = db.query(ParLevel).filter(ParLevel.location_id == location_id).all()
    needs = []

    for par in pars:
        recipe = db.query(Recipe).filter(Recipe.id == par.recipe_id).first()
        # Current stock = sum of quantity_remaining from fresh/use_soon batches
        batches = (
            db.query(ShelfLifeTracker)
            .filter(
                ShelfLifeTracker.recipe_id == par.recipe_id,
                ShelfLifeTracker.location_id == location_id,
                ShelfLifeTracker.status.in_(["fresh", "use_soon"]),
            )
            .all()
        )
        current_stock = sum(b.quantity_remaining for b in batches)
        needed = max(0, par.effective_par - current_stock)

        needs.append(ProductionNeed(
            recipe_id=par.recipe_id,
            recipe_name=recipe.name if recipe else None,
            effective_par=par.effective_par,
            current_stock=current_stock,
            needed=needed,
        ))

    return needs
