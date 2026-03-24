"""Culinary intelligence API routes — techniques, DishDNA, evolution, affinities."""

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cultivos.db.session import get_db
from cultivos.db.models import DishDNA as DishDNAModel, Recipe, Technique
from cultivos.models.culinary import (
    DishDNARead,
    DishEvolutionCreate,
    DishEvolutionRead,
    DNAComparisonResult,
    DNAPair,
    IngredientAffinityCreate,
    IngredientAffinityRead,
    RecipeTechniqueCreate,
    RecipeTechniqueRead,
    TechniqueAuditResult,
    TechniqueCreate,
    TechniqueRead,
)
from cultivos.services import culinary_service, intelligence_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Techniques
# ---------------------------------------------------------------------------

@router.post("/techniques", response_model=TechniqueRead, status_code=201)
def create_technique(data: TechniqueCreate, db: Session = Depends(get_db)):
    tech = culinary_service.create_technique(db, data)
    return _technique_to_read(tech)


@router.get("/techniques", response_model=list[TechniqueRead])
def list_techniques(
    location_id: int = Query(...),
    category: str | None = None,
    in_use: bool | None = None,
    db: Session = Depends(get_db),
):
    techs = culinary_service.list_techniques(db, location_id, category, in_use)
    return [_technique_to_read(t) for t in techs]


@router.get("/techniques/audit", response_model=TechniqueAuditResult)
def technique_audit(location_id: int = Query(...), db: Session = Depends(get_db)):
    all_techs = culinary_service.list_techniques(db, location_id)
    tech_dicts = [{"id": t.id, "name": t.name, "category": t.category} for t in all_techs]

    # Get all technique IDs in use across recipes
    from cultivos.db.models import RecipeTechnique
    in_use_rows = db.query(RecipeTechnique.technique_id).distinct().all()
    in_use_ids = {row[0] for row in in_use_rows}

    result = intelligence_service.technique_audit(tech_dicts, in_use_ids)

    return TechniqueAuditResult(
        overall_score=result["overall_score"],
        by_category=result["by_category"],
        total_techniques=result["total_techniques"],
        in_use_count=result["in_use_count"],
        underused=[_technique_to_read(culinary_service.get_technique(db, t["id"])) for t in result["underused"] if culinary_service.get_technique(db, t["id"])],
        suggestions=result["suggestions"],
    )


@router.get("/techniques/{technique_id}", response_model=TechniqueRead)
def get_technique(technique_id: int, db: Session = Depends(get_db)):
    tech = culinary_service.get_technique(db, technique_id)
    if not tech:
        raise HTTPException(status_code=404, detail="Technique not found")
    return _technique_to_read(tech)


# ---------------------------------------------------------------------------
# Recipe-technique links
# ---------------------------------------------------------------------------

@router.post("/recipes/{recipe_id}/techniques", response_model=RecipeTechniqueRead, status_code=201)
def add_technique_to_recipe(recipe_id: int, data: RecipeTechniqueCreate, db: Session = Depends(get_db)):
    rt = culinary_service.add_technique_to_recipe(db, recipe_id, data)
    if not rt:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return RecipeTechniqueRead(
        id=rt.id,
        recipe_id=rt.recipe_id,
        technique_id=rt.technique_id,
        technique_name=rt.technique.name if rt.technique else None,
        step_order=rt.step_order,
    )


@router.get("/recipes/{recipe_id}/techniques", response_model=list[RecipeTechniqueRead])
def get_recipe_techniques(recipe_id: int, db: Session = Depends(get_db)):
    rts = culinary_service.get_recipe_techniques(db, recipe_id)
    return [
        RecipeTechniqueRead(
            id=rt.id,
            recipe_id=rt.recipe_id,
            technique_id=rt.technique_id,
            technique_name=rt.technique.name if rt.technique else None,
            step_order=rt.step_order,
        )
        for rt in rts
    ]


# ---------------------------------------------------------------------------
# DishDNA
# ---------------------------------------------------------------------------

@router.post("/recipes/{recipe_id}/dna/generate", response_model=DishDNARead)
def generate_dna(recipe_id: int, db: Session = Depends(get_db)):
    dna = culinary_service.generate_and_store_dna(db, recipe_id)
    if not dna:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return _dna_to_read(dna)


@router.get("/recipes/{recipe_id}/dna", response_model=DishDNARead)
def get_dna(recipe_id: int, db: Session = Depends(get_db)):
    dna = culinary_service.get_dish_dna(db, recipe_id)
    if not dna:
        raise HTTPException(status_code=404, detail="DishDNA not found — generate it first")
    return _dna_to_read(dna)


@router.get("/menu/dna-comparison", response_model=DNAComparisonResult)
def dna_comparison(location_id: int = Query(...), db: Session = Depends(get_db)):
    recipes = db.query(Recipe).filter(
        Recipe.location_id == location_id, Recipe.deleted_at.is_(None)
    ).all()

    dna_list = []
    for recipe in recipes:
        dna = culinary_service.get_dish_dna(db, recipe.id)
        if dna:
            dna_list.append({
                "recipe_id": recipe.id,
                "recipe_name": recipe.name,
                "technique_fingerprint": json.loads(dna.technique_fingerprint_json or "[]"),
                "flavor_profile": json.loads(dna.flavor_profile_json or "{}"),
                "texture_profile": json.loads(dna.texture_profile_json or "{}"),
            })

    pairs = intelligence_service.dna_comparison_matrix(dna_list)
    return DNAComparisonResult(
        location_id=location_id,
        pairs=[DNAPair(**p) for p in pairs],
    )


# ---------------------------------------------------------------------------
# Evolution
# ---------------------------------------------------------------------------

@router.post("/recipes/{recipe_id}/evolve", response_model=DishEvolutionRead, status_code=201)
def log_evolution(recipe_id: int, data: DishEvolutionCreate, db: Session = Depends(get_db)):
    data.recipe_id = recipe_id
    evo = culinary_service.log_evolution(db, data)
    return _evolution_to_read(evo)


@router.get("/recipes/{recipe_id}/lineage", response_model=list[DishEvolutionRead])
def get_lineage(recipe_id: int, db: Session = Depends(get_db)):
    evos = culinary_service.get_lineage(db, recipe_id)
    return [_evolution_to_read(e) for e in evos]


# ---------------------------------------------------------------------------
# Affinities
# ---------------------------------------------------------------------------

@router.post("/ingredient-affinities", response_model=IngredientAffinityRead, status_code=201)
def add_affinity(data: IngredientAffinityCreate, db: Session = Depends(get_db)):
    aff = culinary_service.add_affinity(db, data)
    return _affinity_to_read(aff)


@router.get("/ingredients/{ingredient_id}/affinities", response_model=list[IngredientAffinityRead])
def get_affinities(ingredient_id: int, db: Session = Depends(get_db)):
    affs = culinary_service.get_affinities(db, ingredient_id)
    return [_affinity_to_read(a) for a in affs]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _technique_to_read(tech) -> TechniqueRead:
    return TechniqueRead(
        id=tech.id,
        name=tech.name,
        category=tech.category,
        subcategory=tech.subcategory,
        description=tech.description,
        difficulty_level=tech.difficulty_level,
        equipment_required=json.loads(tech.equipment_required_json or "[]"),
        time_profile=tech.time_profile,
        best_for=json.loads(tech.best_for_json or "[]"),
        season_affinity=json.loads(tech.season_affinity_json or "[]"),
        flavor_impact=tech.flavor_impact,
        texture_impact=tech.texture_impact,
        related_techniques=json.loads(tech.related_techniques_json or "[]"),
        in_use=tech.in_use,
        location_id=tech.location_id,
        created_at=tech.created_at,
    )


def _dna_to_read(dna) -> DishDNARead:
    return DishDNARead(
        id=dna.id,
        recipe_id=dna.recipe_id,
        technique_fingerprint=json.loads(dna.technique_fingerprint_json or "[]"),
        flavor_profile=json.loads(dna.flavor_profile_json or "{}"),
        texture_profile=json.loads(dna.texture_profile_json or "{}"),
        cuisine_influences=json.loads(dna.cuisine_influences_json or "[]"),
        seasonal_peak=dna.seasonal_peak,
        complexity_score=dna.complexity_score,
        created_at=dna.created_at,
    )


def _evolution_to_read(evo) -> DishEvolutionRead:
    return DishEvolutionRead(
        id=evo.id,
        recipe_id=evo.recipe_id,
        parent_recipe_id=evo.parent_recipe_id,
        generation=evo.generation,
        evolution_type=evo.evolution_type,
        evolution_date=evo.evolution_date,
        changelog=json.loads(evo.changelog_json or "[]"),
        techniques_added=json.loads(evo.techniques_added_json or "[]"),
        techniques_removed=json.loads(evo.techniques_removed_json or "[]"),
        ingredients_swapped=json.loads(evo.ingredients_swapped_json or "[]"),
        performance_delta=json.loads(evo.performance_delta_json or "{}"),
        evolved_by=evo.evolved_by,
        created_at=evo.created_at,
    )


def _affinity_to_read(aff) -> IngredientAffinityRead:
    return IngredientAffinityRead(
        id=aff.id,
        ingredient_a_id=aff.ingredient_a_id,
        ingredient_b_id=aff.ingredient_b_id,
        ingredient_a_name=aff.ingredient_a.name if aff.ingredient_a else None,
        ingredient_b_name=aff.ingredient_b.name if aff.ingredient_b else None,
        strength_score=aff.strength_score,
        notes=aff.notes,
        created_at=aff.created_at,
    )
