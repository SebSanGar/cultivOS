"""Pydantic schemas for culinary intelligence (elBulli layer)."""

from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Technique
# ---------------------------------------------------------------------------

class TechniqueCreate(BaseModel):
    name: str
    category: str  # Heat, Cold, Texture, Flavor, Preservation, Assembly, Preparation
    subcategory: str | None = None
    description: str | None = None
    difficulty_level: int = Field(default=1, ge=1, le=5)
    equipment_required: list[str] = []
    time_profile: str | None = None  # quick, medium, long
    best_for: list[str] = []
    season_affinity: list[str] = []
    flavor_impact: str | None = None
    texture_impact: str | None = None
    related_techniques: list[int] = []
    location_id: int


class TechniqueRead(BaseModel):
    id: int
    name: str
    category: str
    subcategory: str | None
    description: str | None
    difficulty_level: int
    equipment_required: list[str]
    time_profile: str | None
    best_for: list[str]
    season_affinity: list[str]
    flavor_impact: str | None
    texture_impact: str | None
    related_techniques: list[int]
    in_use: bool
    location_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# RecipeTechnique
# ---------------------------------------------------------------------------

class RecipeTechniqueCreate(BaseModel):
    technique_id: int
    step_order: int | None = None


class RecipeTechniqueRead(BaseModel):
    id: int
    recipe_id: int
    technique_id: int
    technique_name: str | None = None
    step_order: int | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# DishDNA
# ---------------------------------------------------------------------------

class DishDNARead(BaseModel):
    id: int
    recipe_id: int
    technique_fingerprint: list[int]
    flavor_profile: dict[str, float]
    texture_profile: dict[str, float]
    cuisine_influences: list[str]
    seasonal_peak: str | None
    complexity_score: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# DishEvolution
# ---------------------------------------------------------------------------

class DishEvolutionCreate(BaseModel):
    recipe_id: int
    parent_recipe_id: int | None = None
    generation: int = 1
    evolution_type: str  # refinement, seasonal_swap, cost_optimization, technique_change, fusion, customer_feedback
    changelog: list[str] = []
    techniques_added: list[int] = []
    techniques_removed: list[int] = []
    ingredients_swapped: list[dict] = []  # [{old, new, reason}]
    performance_delta: dict = {}  # {margin_change, popularity_change, waste_change}
    evolved_by: str | None = None


class DishEvolutionRead(BaseModel):
    id: int
    recipe_id: int
    parent_recipe_id: int | None
    generation: int
    evolution_type: str
    evolution_date: datetime
    changelog: list[str]
    techniques_added: list[int]
    techniques_removed: list[int]
    ingredients_swapped: list[dict]
    performance_delta: dict
    evolved_by: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Ingredient Affinity
# ---------------------------------------------------------------------------

class IngredientAffinityCreate(BaseModel):
    ingredient_a_id: int
    ingredient_b_id: int
    strength_score: Decimal = Field(ge=0, le=10)
    notes: str | None = None


class IngredientAffinityRead(BaseModel):
    id: int
    ingredient_a_id: int
    ingredient_b_id: int
    ingredient_a_name: str | None = None
    ingredient_b_name: str | None = None
    strength_score: Decimal
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Intelligence outputs
# ---------------------------------------------------------------------------

class TechniqueAuditResult(BaseModel):
    overall_score: float  # 0-10
    by_category: dict[str, float]  # category -> score 0-10
    total_techniques: int
    in_use_count: int
    underused: list[TechniqueRead]
    suggestions: list[str]


class DNAPair(BaseModel):
    recipe_a_id: int
    recipe_a_name: str | None = None
    recipe_b_id: int
    recipe_b_name: str | None = None
    similarity: float  # 0-1


class DNAComparisonResult(BaseModel):
    location_id: int
    pairs: list[DNAPair]
