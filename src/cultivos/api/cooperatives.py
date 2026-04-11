"""Cooperative CRUD + dashboard endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from cultivos.db.models import Cooperative, Farm, Field, HealthScore
from cultivos.db.session import get_db
from cultivos.models.cooperative import (
    CooperativeCreate,
    CooperativeDashboard,
    CooperativeFarmSummary,
    CooperativeOut,
    CooperativeUpdate,
)
from cultivos.models.cooperative_portfolio import CooperativePortfolioOut
from cultivos.models.cooperative_ranking import CooperativeRankingOut
from cultivos.services.intelligence.cooperative_portfolio import compute_portfolio_health
from cultivos.services.intelligence.cooperative_ranking import compute_member_ranking

router = APIRouter(prefix="/api/cooperatives", tags=["cooperatives"])


def _coop_to_out(coop: Cooperative, db: Session) -> dict:
    """Convert ORM cooperative to output dict with farm_count."""
    farm_count = db.query(func.count(Farm.id)).filter(Farm.cooperative_id == coop.id).scalar() or 0
    return {
        "id": coop.id,
        "name": coop.name,
        "state": coop.state,
        "contact_name": coop.contact_name,
        "contact_phone": coop.contact_phone,
        "farm_count": farm_count,
        "created_at": coop.created_at,
    }


@router.post("", response_model=CooperativeOut, status_code=201)
def create_cooperative(body: CooperativeCreate, db: Session = Depends(get_db)):
    """Create a new cooperative."""
    coop = Cooperative(**body.model_dump())
    db.add(coop)
    db.commit()
    db.refresh(coop)
    return _coop_to_out(coop, db)


@router.get("")
def list_cooperatives(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List cooperatives with pagination and farm counts."""
    query = db.query(Cooperative)
    total = query.count()
    items = query.order_by(Cooperative.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "data": [_coop_to_out(c, db) for c in items],
        "meta": {"total": total, "page": page, "page_size": page_size},
    }


@router.get("/{coop_id}", response_model=CooperativeOut)
def get_cooperative(coop_id: int, db: Session = Depends(get_db)):
    """Get a single cooperative by ID."""
    coop = db.query(Cooperative).filter(Cooperative.id == coop_id).first()
    if not coop:
        raise HTTPException(status_code=404, detail="Cooperative not found")
    return _coop_to_out(coop, db)


@router.put("/{coop_id}", response_model=CooperativeOut)
def update_cooperative(coop_id: int, body: CooperativeUpdate, db: Session = Depends(get_db)):
    """Update a cooperative. Only provided fields are changed."""
    coop = db.query(Cooperative).filter(Cooperative.id == coop_id).first()
    if not coop:
        raise HTTPException(status_code=404, detail="Cooperative not found")
    for key, val in body.model_dump(exclude_unset=True).items():
        setattr(coop, key, val)
    db.commit()
    db.refresh(coop)
    return _coop_to_out(coop, db)


@router.delete("/{coop_id}", status_code=204)
def delete_cooperative(coop_id: int, db: Session = Depends(get_db)):
    """Delete a cooperative. Does not delete member farms — they become unaffiliated."""
    coop = db.query(Cooperative).filter(Cooperative.id == coop_id).first()
    if not coop:
        raise HTTPException(status_code=404, detail="Cooperative not found")
    # Unset cooperative_id on member farms
    db.query(Farm).filter(Farm.cooperative_id == coop_id).update({"cooperative_id": None})
    db.delete(coop)
    db.commit()


@router.get("/{coop_id}/dashboard", response_model=CooperativeDashboard)
def cooperative_dashboard(coop_id: int, db: Session = Depends(get_db)):
    """Aggregate stats across all farms in a cooperative."""
    coop = db.query(Cooperative).filter(Cooperative.id == coop_id).first()
    if not coop:
        raise HTTPException(status_code=404, detail="Cooperative not found")

    farms = db.query(Farm).filter(Farm.cooperative_id == coop_id).all()
    farm_ids = [f.id for f in farms]

    total_hectares = sum(f.total_hectares or 0 for f in farms)
    total_fields = 0
    all_health_scores = []
    farm_summaries = []

    if farm_ids:
        fields = db.query(Field).filter(Field.farm_id.in_(farm_ids)).all()
        total_fields = len(fields)
        field_ids = [f.id for f in fields]

        # Build farm_id -> fields mapping
        farm_fields: dict[int, list] = {}
        for f in fields:
            farm_fields.setdefault(f.farm_id, []).append(f)

        # Get latest health score per field via subquery
        if field_ids:
            from sqlalchemy import and_
            latest_sub = (
                db.query(
                    HealthScore.field_id,
                    func.max(HealthScore.scored_at).label("max_scored"),
                )
                .filter(HealthScore.field_id.in_(field_ids))
                .group_by(HealthScore.field_id)
                .subquery()
            )
            latest_scores = (
                db.query(HealthScore)
                .join(
                    latest_sub,
                    and_(
                        HealthScore.field_id == latest_sub.c.field_id,
                        HealthScore.scored_at == latest_sub.c.max_scored,
                    ),
                )
                .all()
            )
            field_health = {hs.field_id: hs.score for hs in latest_scores}
            all_health_scores = list(field_health.values())
        else:
            field_health = {}

        for farm in farms:
            ff = farm_fields.get(farm.id, [])
            farm_health_vals = [field_health[f.id] for f in ff if f.id in field_health]
            farm_summaries.append(CooperativeFarmSummary(
                id=farm.id,
                name=farm.name,
                total_hectares=farm.total_hectares or 0,
                field_count=len(ff),
                avg_health=round(sum(farm_health_vals) / len(farm_health_vals), 1) if farm_health_vals else None,
            ))

    avg_health = round(sum(all_health_scores) / len(all_health_scores), 1) if all_health_scores else None

    return CooperativeDashboard(
        cooperative_id=coop.id,
        cooperative_name=coop.name,
        total_farms=len(farms),
        total_fields=total_fields,
        total_hectares=total_hectares,
        avg_health=avg_health,
        farms=farm_summaries,
    )


@router.get("/{coop_id}/member-ranking", response_model=CooperativeRankingOut)
def member_ranking(coop_id: int, db: Session = Depends(get_db)):
    """Rank member farms by composite score: health(40%) + regen(30%) + alert response(30%)."""
    coop = db.query(Cooperative).filter(Cooperative.id == coop_id).first()
    if not coop:
        raise HTTPException(status_code=404, detail="Cooperative not found")
    return compute_member_ranking(coop, db)


@router.get("/{coop_id}/portfolio-health", response_model=CooperativePortfolioOut)
def portfolio_health(coop_id: int, db: Session = Depends(get_db)):
    """Aggregate portfolio health: farms, fields, health, carbon, economic impact."""
    coop = db.query(Cooperative).filter(Cooperative.id == coop_id).first()
    if not coop:
        raise HTTPException(status_code=404, detail="Cooperative not found")
    return compute_portfolio_health(coop, db)
