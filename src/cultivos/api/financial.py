"""Financial and menu engineering API routes."""

from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from cultivos.db.session import get_db
from cultivos.models.financial import MenuEngineeringMatrix
from cultivos.services import cost_service, menu_engineering_service
from cultivos.db.models import Recipe

router = APIRouter()


@router.get("/menu-engineering", response_model=MenuEngineeringMatrix)
def get_menu_engineering(
    location_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Build menu engineering matrix for all active recipes at a location.

    Note: menu_price and popularity are placeholder values for MVP.
    In production, these come from POS integration.
    """
    recipes = (
        db.query(Recipe)
        .filter(Recipe.location_id == location_id, Recipe.deleted_at.is_(None))
        .all()
    )

    items = []
    for recipe in recipes:
        cpp = cost_service.cost_per_portion(db, recipe.id)
        items.append({
            "recipe_id": recipe.id,
            "recipe_name": recipe.name,
            "food_cost": cpp,
            "menu_price": None,
            "popularity": 0,
            "location_id": location_id,
        })

    matrix = menu_engineering_service.build_menu_matrix(items)
    matrix.location_id = location_id
    return matrix
