"""Ingredient API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cultivos.db.session import get_db
from cultivos.models.recipe import IngredientCreate, IngredientRead
from cultivos.services import recipe_service

router = APIRouter()


@router.post("/ingredients", response_model=IngredientRead, status_code=201)
def create_ingredient(data: IngredientCreate, db: Session = Depends(get_db)):
    ingredient = recipe_service.create_ingredient(db, data)
    return IngredientRead.model_validate(ingredient)


@router.get("/ingredients", response_model=list[IngredientRead])
def list_ingredients(
    location_id: int = Query(...),
    category: str | None = None,
    db: Session = Depends(get_db),
):
    ingredients = recipe_service.list_ingredients(db, location_id, category)
    return [IngredientRead.model_validate(i) for i in ingredients]


@router.get("/ingredients/{ingredient_id}", response_model=IngredientRead)
def get_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    ingredient = recipe_service.get_ingredient(db, ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return IngredientRead.model_validate(ingredient)
