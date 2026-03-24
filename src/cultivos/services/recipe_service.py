"""Recipe CRUD service — database operations for recipes and ingredients."""

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload

from cultivos.db.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeStep,
    ScalingRule,
)
from cultivos.models.recipe import (
    IngredientCreate,
    RecipeCreate,
    RecipeIngredientCreate,
    RecipeStepCreate,
    RecipeUpdate,
    ScalingRuleCreate,
)


# ---------------------------------------------------------------------------
# Ingredients
# ---------------------------------------------------------------------------

def create_ingredient(db: Session, data: IngredientCreate) -> Ingredient:
    ing = Ingredient(
        name=data.name,
        category=data.category,
        default_unit=data.default_unit,
        location_id=data.location_id,
    )
    db.add(ing)
    db.commit()
    db.refresh(ing)
    return ing


def list_ingredients(db: Session, location_id: int, category: str | None = None) -> list[Ingredient]:
    q = db.query(Ingredient).filter(
        Ingredient.location_id == location_id,
        Ingredient.deleted_at.is_(None),
    )
    if category:
        q = q.filter(Ingredient.category == category)
    return q.order_by(Ingredient.name).all()


def get_ingredient(db: Session, ingredient_id: int) -> Ingredient | None:
    return db.query(Ingredient).filter(
        Ingredient.id == ingredient_id,
        Ingredient.deleted_at.is_(None),
    ).first()


# ---------------------------------------------------------------------------
# Recipes
# ---------------------------------------------------------------------------

def create_recipe(db: Session, data: RecipeCreate) -> Recipe:
    recipe = Recipe(
        name=data.name,
        category=data.category,
        location_id=data.location_id,
        base_yield=data.base_yield,
        prep_time_minutes=data.prep_time_minutes,
        cook_time_minutes=data.cook_time_minutes,
        total_time_minutes=data.total_time_minutes,
        shelf_life_hours=data.shelf_life_hours,
        allergens_json=json.dumps(data.allergens),
        tags_json=json.dumps(data.tags),
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe


def get_recipe(db: Session, recipe_id: int) -> Recipe | None:
    return (
        db.query(Recipe)
        .options(
            joinedload(Recipe.ingredients).joinedload(RecipeIngredient.ingredient),
            joinedload(Recipe.steps),
            joinedload(Recipe.scaling_rules),
        )
        .filter(Recipe.id == recipe_id, Recipe.deleted_at.is_(None))
        .first()
    )


def list_recipes(db: Session, location_id: int, category: str | None = None) -> list[Recipe]:
    q = db.query(Recipe).filter(
        Recipe.location_id == location_id,
        Recipe.deleted_at.is_(None),
    )
    if category:
        q = q.filter(Recipe.category == category)
    return q.order_by(Recipe.name).all()


def update_recipe(db: Session, recipe_id: int, data: RecipeUpdate) -> Recipe | None:
    recipe = db.query(Recipe).filter(
        Recipe.id == recipe_id,
        Recipe.deleted_at.is_(None),
    ).first()
    if not recipe:
        return None

    update_data = data.model_dump(exclude_unset=True)
    if "allergens" in update_data:
        update_data["allergens_json"] = json.dumps(update_data.pop("allergens"))
    if "tags" in update_data:
        update_data["tags_json"] = json.dumps(update_data.pop("tags"))

    for key, value in update_data.items():
        setattr(recipe, key, value)

    db.commit()
    db.refresh(recipe)
    return recipe


def delete_recipe(db: Session, recipe_id: int) -> bool:
    recipe = db.query(Recipe).filter(
        Recipe.id == recipe_id,
        Recipe.deleted_at.is_(None),
    ).first()
    if not recipe:
        return False
    recipe.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# Recipe ingredients
# ---------------------------------------------------------------------------

def add_ingredient_to_recipe(
    db: Session, recipe_id: int, data: RecipeIngredientCreate
) -> RecipeIngredient | None:
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        return None

    ri = RecipeIngredient(
        recipe_id=recipe_id,
        ingredient_id=data.ingredient_id,
        amount=data.amount,
        unit=data.unit,
        scaling_type=data.scaling_type,
    )
    db.add(ri)
    db.commit()
    db.refresh(ri)
    return ri


# ---------------------------------------------------------------------------
# Recipe steps
# ---------------------------------------------------------------------------

def add_step_to_recipe(
    db: Session, recipe_id: int, data: RecipeStepCreate
) -> RecipeStep | None:
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        return None

    step = RecipeStep(
        recipe_id=recipe_id,
        step_order=data.step_order,
        instruction=data.instruction,
        time_minutes=data.time_minutes,
        temperature_c=data.temperature_c,
    )
    db.add(step)
    db.commit()
    db.refresh(step)
    return step


# ---------------------------------------------------------------------------
# Scaling rules
# ---------------------------------------------------------------------------

def set_scaling_rule(
    db: Session, recipe_id: int, data: ScalingRuleCreate
) -> ScalingRule:
    existing = db.query(ScalingRule).filter(
        ScalingRule.recipe_id == recipe_id,
        ScalingRule.ingredient_id == data.ingredient_id,
    ).first()

    if existing:
        existing.rule_type = data.rule_type
        existing.exponent = data.exponent
        existing.step_size = data.step_size
        existing.custom_curve_json = data.custom_curve_json
        db.commit()
        db.refresh(existing)
        return existing

    rule = ScalingRule(
        recipe_id=recipe_id,
        ingredient_id=data.ingredient_id,
        rule_type=data.rule_type,
        exponent=data.exponent,
        step_size=data.step_size,
        custom_curve_json=data.custom_curve_json,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def recipe_to_dict_for_scaling(recipe: Recipe) -> tuple[list[dict], dict[int, dict]]:
    """Extract ingredient + scaling data from an ORM recipe for the scaling service."""
    ingredients = []
    for ri in recipe.ingredients:
        ingredients.append({
            "ingredient_id": ri.ingredient_id,
            "ingredient_name": ri.ingredient.name if ri.ingredient else None,
            "amount": ri.amount,
            "unit": ri.unit,
            "scaling_type": ri.scaling_type,
        })

    rules = {}
    for sr in recipe.scaling_rules:
        rules[sr.ingredient_id] = {
            "rule_type": sr.rule_type,
            "exponent": sr.exponent,
            "step_size": sr.step_size,
        }

    return ingredients, rules
