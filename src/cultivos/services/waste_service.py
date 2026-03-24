"""Waste tracking service — logging, summaries, pattern detection."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from cultivos.db.models import (
    Ingredient,
    IngredientPrice,
    Recipe,
    ShelfLifeTracker,
    WasteLog,
)
from cultivos.models.waste import (
    ShelfLifeCreate,
    ShelfLifeUpdate,
    TopWastedItem,
    WasteLogCreate,
    WastePattern,
    WasteSummary,
)
from cultivos.services.cost_service import get_latest_price


def log_waste(db: Session, data: WasteLogCreate) -> WasteLog:
    """Log a waste entry, auto-calculating cost if not provided."""
    cost = data.cost_estimate
    if cost is None and data.ingredient_id:
        unit_price = get_latest_price(db, data.ingredient_id)
        if unit_price > 0:
            cost = (data.quantity * unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    entry = WasteLog(
        location_id=data.location_id,
        logged_by=data.logged_by,
        recipe_id=data.recipe_id,
        ingredient_id=data.ingredient_id,
        category=data.category,
        quantity=data.quantity,
        unit=data.unit,
        cost_estimate=cost,
        reason=data.reason,
        photo_url=data.photo_url,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def daily_summary(db: Session, location_id: int, date: datetime) -> WasteSummary:
    """Aggregate waste for a single day."""
    start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return _summarize(db, location_id, start, end, "daily")


def weekly_summary(db: Session, location_id: int, week_start: datetime) -> WasteSummary:
    """Aggregate waste for a week."""
    start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=7)
    return _summarize(db, location_id, start, end, "weekly")


def _summarize(
    db: Session, location_id: int, start: datetime, end: datetime, period: str
) -> WasteSummary:
    logs = (
        db.query(WasteLog)
        .filter(
            WasteLog.location_id == location_id,
            WasteLog.logged_at >= start,
            WasteLog.logged_at < end,
        )
        .all()
    )

    total_kg = Decimal("0")
    total_cost = Decimal("0")
    by_category: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for log in logs:
        qty = Decimal(str(log.quantity))
        cost = Decimal(str(log.cost_estimate)) if log.cost_estimate else Decimal("0")
        if log.unit == "kg":
            total_kg += qty
        elif log.unit == "g":
            total_kg += qty / Decimal("1000")
        total_cost += cost
        by_category[log.category] += cost

    return WasteSummary(
        location_id=location_id,
        period=period,
        start_date=start,
        total_waste_kg=total_kg.quantize(Decimal("0.01")),
        total_waste_cost=total_cost.quantize(Decimal("0.01")),
        by_category=dict(by_category),
    )


def top_wasted_items(
    db: Session, location_id: int, days: int = 7, limit: int = 5
) -> list[TopWastedItem]:
    """Top wasted items by cost in the last N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    logs = (
        db.query(WasteLog)
        .filter(
            WasteLog.location_id == location_id,
            WasteLog.logged_at >= cutoff,
        )
        .all()
    )

    # Group by recipe_id or ingredient_id
    groups: dict[str, dict] = {}
    for log in logs:
        key = f"r:{log.recipe_id}" if log.recipe_id else f"i:{log.ingredient_id}"
        if key not in groups:
            name = None
            if log.recipe_id:
                r = db.query(Recipe).filter(Recipe.id == log.recipe_id).first()
                name = r.name if r else None
            elif log.ingredient_id:
                i = db.query(Ingredient).filter(Ingredient.id == log.ingredient_id).first()
                name = i.name if i else None
            groups[key] = {
                "recipe_id": log.recipe_id,
                "ingredient_id": log.ingredient_id,
                "name": name,
                "total_quantity": Decimal("0"),
                "total_cost": Decimal("0"),
                "occurrences": 0,
            }
        groups[key]["total_quantity"] += Decimal(str(log.quantity))
        groups[key]["total_cost"] += Decimal(str(log.cost_estimate or 0))
        groups[key]["occurrences"] += 1

    sorted_items = sorted(groups.values(), key=lambda x: x["total_cost"], reverse=True)
    return [TopWastedItem(**item) for item in sorted_items[:limit]]


def waste_rate(db: Session, location_id: int, days: int = 7) -> Decimal:
    """Waste rate = waste_cost / total_food_cost * 100. Stub: returns waste cost only."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    logs = (
        db.query(WasteLog)
        .filter(WasteLog.location_id == location_id, WasteLog.logged_at >= cutoff)
        .all()
    )
    total = sum(Decimal(str(log.cost_estimate or 0)) for log in logs)
    return total.quantize(Decimal("0.01"))


# ---------------------------------------------------------------------------
# Shelf life tracking
# ---------------------------------------------------------------------------

def create_batch(db: Session, data: ShelfLifeCreate) -> ShelfLifeTracker:
    batch = ShelfLifeTracker(
        recipe_id=data.recipe_id,
        location_id=data.location_id,
        produced_at=data.produced_at or datetime.now(timezone.utc),
        expires_at=data.expires_at,
        quantity_produced=data.quantity_produced,
        quantity_remaining=data.quantity_remaining or data.quantity_produced,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def get_expiring_batches(
    db: Session, location_id: int, hours_threshold: int = 6
) -> list[ShelfLifeTracker]:
    """Get batches expiring within the next N hours."""
    now = datetime.now(timezone.utc)
    deadline = now + timedelta(hours=hours_threshold)
    return (
        db.query(ShelfLifeTracker)
        .filter(
            ShelfLifeTracker.location_id == location_id,
            ShelfLifeTracker.expires_at <= deadline,
            ShelfLifeTracker.expires_at > now,
            ShelfLifeTracker.status.in_(["fresh", "use_soon"]),
            ShelfLifeTracker.quantity_remaining > 0,
        )
        .order_by(ShelfLifeTracker.expires_at)
        .all()
    )


def update_batch(db: Session, batch_id: int, data: ShelfLifeUpdate) -> ShelfLifeTracker | None:
    batch = db.query(ShelfLifeTracker).filter(ShelfLifeTracker.id == batch_id).first()
    if not batch:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(batch, key, value)
    db.commit()
    db.refresh(batch)
    return batch
