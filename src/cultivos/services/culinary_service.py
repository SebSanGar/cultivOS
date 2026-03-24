"""Culinary intelligence DB service — CRUD for techniques, DNA, evolution, affinities."""

import json
from decimal import Decimal

from sqlalchemy.orm import Session

from cultivos.db.models import (
    DishDNA,
    DishEvolution,
    Ingredient,
    IngredientAffinity,
    IngredientSeason,
    Recipe,
    RecipeIngredient,
    RecipeStep,
    RecipeTechnique,
    Technique,
)
from cultivos.models.culinary import (
    DishEvolutionCreate,
    IngredientAffinityCreate,
    RecipeTechniqueCreate,
    TechniqueCreate,
)
from cultivos.services import intelligence_service


# ---------------------------------------------------------------------------
# Techniques
# ---------------------------------------------------------------------------

def create_technique(db: Session, data: TechniqueCreate) -> Technique:
    tech = Technique(
        name=data.name,
        category=data.category,
        subcategory=data.subcategory,
        description=data.description,
        difficulty_level=data.difficulty_level,
        equipment_required_json=json.dumps(data.equipment_required),
        time_profile=data.time_profile,
        best_for_json=json.dumps(data.best_for),
        season_affinity_json=json.dumps(data.season_affinity),
        flavor_impact=data.flavor_impact,
        texture_impact=data.texture_impact,
        related_techniques_json=json.dumps(data.related_techniques),
        location_id=data.location_id,
    )
    db.add(tech)
    db.commit()
    db.refresh(tech)
    return tech


def list_techniques(
    db: Session, location_id: int, category: str | None = None, in_use: bool | None = None
) -> list[Technique]:
    q = db.query(Technique).filter(
        Technique.location_id == location_id,
        Technique.deleted_at.is_(None),
    )
    if category:
        q = q.filter(Technique.category == category)
    if in_use is not None:
        q = q.filter(Technique.in_use == in_use)
    return q.order_by(Technique.category, Technique.name).all()


def get_technique(db: Session, technique_id: int) -> Technique | None:
    return db.query(Technique).filter(
        Technique.id == technique_id, Technique.deleted_at.is_(None)
    ).first()


# ---------------------------------------------------------------------------
# Recipe-technique links
# ---------------------------------------------------------------------------

def add_technique_to_recipe(
    db: Session, recipe_id: int, data: RecipeTechniqueCreate
) -> RecipeTechnique | None:
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        return None
    rt = RecipeTechnique(
        recipe_id=recipe_id,
        technique_id=data.technique_id,
        step_order=data.step_order,
    )
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return rt


def get_recipe_techniques(db: Session, recipe_id: int) -> list[RecipeTechnique]:
    return (
        db.query(RecipeTechnique)
        .filter(RecipeTechnique.recipe_id == recipe_id)
        .order_by(RecipeTechnique.step_order)
        .all()
    )


# ---------------------------------------------------------------------------
# DishDNA
# ---------------------------------------------------------------------------

def generate_and_store_dna(db: Session, recipe_id: int) -> DishDNA | None:
    """Generate DishDNA from recipe data and store it."""
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        return None

    # Get techniques linked to this recipe
    rts = get_recipe_techniques(db, recipe_id)
    technique_ids = [rt.technique_id for rt in rts]
    technique_data = []
    for rt in rts:
        tech = db.query(Technique).filter(Technique.id == rt.technique_id).first()
        if tech:
            technique_data.append({
                "id": tech.id,
                "name": tech.name,
                "flavor_impact": tech.flavor_impact,
                "texture_impact": tech.texture_impact,
            })

    num_ingredients = db.query(RecipeIngredient).filter(
        RecipeIngredient.recipe_id == recipe_id
    ).count()
    num_steps = db.query(RecipeStep).filter(
        RecipeStep.recipe_id == recipe_id
    ).count()

    dna_data = intelligence_service.generate_dish_dna(
        technique_ids=technique_ids,
        technique_data=technique_data,
        num_ingredients=num_ingredients,
        num_steps=num_steps,
    )

    return upsert_dish_dna(db, recipe_id, dna_data)


def upsert_dish_dna(db: Session, recipe_id: int, dna_data: dict) -> DishDNA:
    existing = db.query(DishDNA).filter(DishDNA.recipe_id == recipe_id).first()

    if existing:
        existing.technique_fingerprint_json = json.dumps(dna_data["technique_fingerprint"])
        existing.flavor_profile_json = json.dumps(dna_data["flavor_profile"])
        existing.texture_profile_json = json.dumps(dna_data["texture_profile"])
        existing.cuisine_influences_json = json.dumps(dna_data["cuisine_influences"])
        existing.seasonal_peak = dna_data.get("seasonal_peak")
        existing.complexity_score = dna_data["complexity_score"]
        db.commit()
        db.refresh(existing)
        return existing

    dna = DishDNA(
        recipe_id=recipe_id,
        technique_fingerprint_json=json.dumps(dna_data["technique_fingerprint"]),
        flavor_profile_json=json.dumps(dna_data["flavor_profile"]),
        texture_profile_json=json.dumps(dna_data["texture_profile"]),
        cuisine_influences_json=json.dumps(dna_data["cuisine_influences"]),
        seasonal_peak=dna_data.get("seasonal_peak"),
        complexity_score=dna_data["complexity_score"],
    )
    db.add(dna)
    db.commit()
    db.refresh(dna)
    return dna


def get_dish_dna(db: Session, recipe_id: int) -> DishDNA | None:
    return db.query(DishDNA).filter(DishDNA.recipe_id == recipe_id).first()


# ---------------------------------------------------------------------------
# Evolution
# ---------------------------------------------------------------------------

def log_evolution(db: Session, data: DishEvolutionCreate) -> DishEvolution:
    evo = DishEvolution(
        recipe_id=data.recipe_id,
        parent_recipe_id=data.parent_recipe_id,
        generation=data.generation,
        evolution_type=data.evolution_type,
        changelog_json=json.dumps(data.changelog),
        techniques_added_json=json.dumps(data.techniques_added),
        techniques_removed_json=json.dumps(data.techniques_removed),
        ingredients_swapped_json=json.dumps(data.ingredients_swapped),
        performance_delta_json=json.dumps(data.performance_delta),
        evolved_by=data.evolved_by,
    )
    db.add(evo)
    db.commit()
    db.refresh(evo)
    return evo


def get_lineage(db: Session, recipe_id: int) -> list[DishEvolution]:
    """Get full evolution chain for a recipe, ordered by generation."""
    return (
        db.query(DishEvolution)
        .filter(DishEvolution.recipe_id == recipe_id)
        .order_by(DishEvolution.generation)
        .all()
    )


# ---------------------------------------------------------------------------
# Affinities
# ---------------------------------------------------------------------------

def add_affinity(db: Session, data: IngredientAffinityCreate) -> IngredientAffinity:
    aff = IngredientAffinity(
        ingredient_a_id=data.ingredient_a_id,
        ingredient_b_id=data.ingredient_b_id,
        strength_score=data.strength_score,
        notes=data.notes,
    )
    db.add(aff)
    db.commit()
    db.refresh(aff)
    return aff


def get_affinities(db: Session, ingredient_id: int) -> list[IngredientAffinity]:
    """Get all pairings for an ingredient (either side of the relationship)."""
    return (
        db.query(IngredientAffinity)
        .filter(
            (IngredientAffinity.ingredient_a_id == ingredient_id)
            | (IngredientAffinity.ingredient_b_id == ingredient_id)
        )
        .order_by(IngredientAffinity.strength_score.desc())
        .all()
    )


# ---------------------------------------------------------------------------
# Seasonal
# ---------------------------------------------------------------------------

def get_seasonal_ingredients(db: Session, season: str) -> list[IngredientSeason]:
    return (
        db.query(IngredientSeason)
        .filter(IngredientSeason.season == season)
        .all()
    )
