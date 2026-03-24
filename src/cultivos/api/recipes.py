"""Recipe and scaling API routes."""

import json
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cultivos.db.session import get_db
from cultivos.models.recipe import (
    CostBreakdown,
    RecipeCreate,
    RecipeDetail,
    RecipeIngredientCreate,
    RecipeIngredientRead,
    RecipeRead,
    RecipeStepCreate,
    RecipeStepRead,
    RecipeUpdate,
    ScaledRecipeResponse,
    ScalingRuleCreate,
    ScalingRuleRead,
)
from cultivos.services import recipe_service, scaling_service, cost_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Recipe CRUD
# ---------------------------------------------------------------------------

@router.post("/recipes", response_model=RecipeRead, status_code=201)
def create_recipe(data: RecipeCreate, db: Session = Depends(get_db)):
    recipe = recipe_service.create_recipe(db, data)
    return _recipe_to_read(recipe)


@router.get("/recipes", response_model=list[RecipeRead])
def list_recipes(
    location_id: int = Query(...),
    category: str | None = None,
    db: Session = Depends(get_db),
):
    recipes = recipe_service.list_recipes(db, location_id, category)
    return [_recipe_to_read(r) for r in recipes]


@router.get("/recipes/{recipe_id}", response_model=RecipeDetail)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = recipe_service.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return _recipe_to_detail(recipe)


@router.put("/recipes/{recipe_id}", response_model=RecipeRead)
def update_recipe(recipe_id: int, data: RecipeUpdate, db: Session = Depends(get_db)):
    recipe = recipe_service.update_recipe(db, recipe_id, data)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return _recipe_to_read(recipe)


@router.delete("/recipes/{recipe_id}", status_code=200)
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    if not recipe_service.delete_recipe(db, recipe_id):
        raise HTTPException(status_code=404, detail="Recipe not found")
    return {"detail": "Recipe deleted"}


# ---------------------------------------------------------------------------
# Recipe ingredients
# ---------------------------------------------------------------------------

@router.post("/recipes/{recipe_id}/ingredients", response_model=RecipeIngredientRead, status_code=201)
def add_ingredient(recipe_id: int, data: RecipeIngredientCreate, db: Session = Depends(get_db)):
    ri = recipe_service.add_ingredient_to_recipe(db, recipe_id, data)
    if not ri:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return RecipeIngredientRead(
        id=ri.id,
        recipe_id=ri.recipe_id,
        ingredient_id=ri.ingredient_id,
        ingredient_name=ri.ingredient.name if ri.ingredient else None,
        amount=ri.amount,
        unit=ri.unit,
        scaling_type=ri.scaling_type,
    )


# ---------------------------------------------------------------------------
# Recipe steps
# ---------------------------------------------------------------------------

@router.post("/recipes/{recipe_id}/steps", response_model=RecipeStepRead, status_code=201)
def add_step(recipe_id: int, data: RecipeStepCreate, db: Session = Depends(get_db)):
    step = recipe_service.add_step_to_recipe(db, recipe_id, data)
    if not step:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return RecipeStepRead.model_validate(step)


# ---------------------------------------------------------------------------
# Scaling rules
# ---------------------------------------------------------------------------

@router.post("/recipes/{recipe_id}/scaling-rules", response_model=ScalingRuleRead, status_code=201)
def set_scaling_rule(recipe_id: int, data: ScalingRuleCreate, db: Session = Depends(get_db)):
    rule = recipe_service.set_scaling_rule(db, recipe_id, data)
    return ScalingRuleRead.model_validate(rule)


# ---------------------------------------------------------------------------
# THE KEY ENDPOINT: Scale a recipe
# ---------------------------------------------------------------------------

@router.get("/recipes/{recipe_id}/scale", response_model=ScaledRecipeResponse)
def scale_recipe(
    recipe_id: int,
    target_yield: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):
    recipe = recipe_service.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    ingredients, rules = recipe_service.recipe_to_dict_for_scaling(recipe)
    scaled = scaling_service.scale_recipe(ingredients, recipe.base_yield, target_yield, rules)

    cpp = cost_service.cost_per_portion(db, recipe_id)

    return ScaledRecipeResponse(
        recipe_id=recipe.id,
        recipe_name=recipe.name,
        base_yield=recipe.base_yield,
        target_yield=target_yield,
        scale_factor=Decimal(str(target_yield)) / Decimal(str(recipe.base_yield)),
        ingredients=scaled,
        cost_per_portion=cpp,
    )


# ---------------------------------------------------------------------------
# Cost
# ---------------------------------------------------------------------------

@router.get("/recipes/{recipe_id}/cost", response_model=CostBreakdown)
def get_recipe_cost(recipe_id: int, db: Session = Depends(get_db)):
    breakdown = cost_service.recipe_cost_breakdown(db, recipe_id)
    if not breakdown:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return breakdown


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _recipe_to_read(recipe) -> RecipeRead:
    return RecipeRead(
        id=recipe.id,
        name=recipe.name,
        category=recipe.category,
        location_id=recipe.location_id,
        base_yield=recipe.base_yield,
        prep_time_minutes=recipe.prep_time_minutes,
        cook_time_minutes=recipe.cook_time_minutes,
        total_time_minutes=recipe.total_time_minutes,
        shelf_life_hours=recipe.shelf_life_hours,
        allergens=json.loads(recipe.allergens_json or "[]"),
        tags=json.loads(recipe.tags_json or "[]"),
        created_at=recipe.created_at,
        updated_at=recipe.updated_at,
    )


def _recipe_to_detail(recipe) -> RecipeDetail:
    return RecipeDetail(
        id=recipe.id,
        name=recipe.name,
        category=recipe.category,
        location_id=recipe.location_id,
        base_yield=recipe.base_yield,
        prep_time_minutes=recipe.prep_time_minutes,
        cook_time_minutes=recipe.cook_time_minutes,
        total_time_minutes=recipe.total_time_minutes,
        shelf_life_hours=recipe.shelf_life_hours,
        allergens=json.loads(recipe.allergens_json or "[]"),
        tags=json.loads(recipe.tags_json or "[]"),
        created_at=recipe.created_at,
        updated_at=recipe.updated_at,
        ingredients=[
            RecipeIngredientRead(
                id=ri.id,
                recipe_id=ri.recipe_id,
                ingredient_id=ri.ingredient_id,
                ingredient_name=ri.ingredient.name if ri.ingredient else None,
                amount=ri.amount,
                unit=ri.unit,
                scaling_type=ri.scaling_type,
            )
            for ri in recipe.ingredients
        ],
        steps=[RecipeStepRead.model_validate(s) for s in sorted(recipe.steps, key=lambda s: s.step_order)],
        scaling_rules=[ScalingRuleRead.model_validate(sr) for sr in recipe.scaling_rules],
    )
