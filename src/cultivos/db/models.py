"""
SQLAlchemy ORM models for Kitchen Intelligence.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


def _utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Multi-tenant
# ---------------------------------------------------------------------------

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    address = Column(String(300))
    timezone = Column(String(50), default="America/Toronto")
    currency = Column(String(3), default="CAD")
    created_at = Column(DateTime, default=_utcnow)
    deleted_at = Column(DateTime)

    users = relationship("User", back_populates="location", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(200))
    role = Column(String(20), default="staff")  # staff, lead, manager, admin
    pin_hash = Column(String(200))
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    deleted_at = Column(DateTime)

    location = relationship("Location", back_populates="users")


# ---------------------------------------------------------------------------
# Recipe domain
# ---------------------------------------------------------------------------

class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    category = Column(String(50))  # protein, vegetable, grain, dairy, spice, other
    default_unit = Column(String(20), default="g")
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    deleted_at = Column(DateTime)

    prices = relationship("IngredientPrice", back_populates="ingredient", cascade="all, delete-orphan")


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    category = Column(String(50))  # appetizer, main, dessert, sauce, base, beverage
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    base_yield = Column(Integer, nullable=False, default=1)
    prep_time_minutes = Column(Integer)
    cook_time_minutes = Column(Integer)
    total_time_minutes = Column(Integer)
    shelf_life_hours = Column(Integer)
    allergens_json = Column(Text, default="[]")  # JSON array
    tags_json = Column(Text, default="[]")  # JSON array
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    deleted_at = Column(DateTime)

    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    steps = relationship("RecipeStep", back_populates="recipe", cascade="all, delete-orphan")
    scaling_rules = relationship("ScalingRule", back_populates="recipe", cascade="all, delete-orphan")


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    amount = Column(Numeric(10, 4), nullable=False)
    unit = Column(String(20), nullable=False, default="g")
    scaling_type = Column(String(20), default="linear")  # linear, sublinear, stepped, fixed, logarithmic
    created_at = Column(DateTime, default=_utcnow)

    recipe = relationship("Recipe", back_populates="ingredients")
    ingredient = relationship("Ingredient")


class RecipeStep(Base):
    __tablename__ = "recipe_steps"

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    step_order = Column(Integer, nullable=False)
    instruction = Column(Text, nullable=False)
    time_minutes = Column(Integer)
    temperature_c = Column(Integer)
    created_at = Column(DateTime, default=_utcnow)

    recipe = relationship("Recipe", back_populates="steps")


class ScalingRule(Base):
    __tablename__ = "scaling_rules"

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    rule_type = Column(String(20), nullable=False, default="linear")
    exponent = Column(Numeric(4, 2), default=1.0)  # 1.0=linear, 0.8=sublinear, etc.
    step_size = Column(Numeric(10, 4))  # for stepped scaling
    custom_curve_json = Column(Text)  # JSON for custom rules
    created_at = Column(DateTime, default=_utcnow)

    __table_args__ = (
        UniqueConstraint("recipe_id", "ingredient_id", name="uq_scaling_recipe_ingredient"),
    )

    recipe = relationship("Recipe", back_populates="scaling_rules")
    ingredient = relationship("Ingredient")


# ---------------------------------------------------------------------------
# Supplier / pricing domain
# ---------------------------------------------------------------------------

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    contact_name = Column(String(100))
    contact_email = Column(String(200))
    contact_phone = Column(String(30))
    address = Column(String(300))
    categories_json = Column(Text, default="[]")  # JSON array
    reliability_score = Column(Numeric(3, 1))  # 1-10
    quality_rating = Column(Numeric(3, 1))  # 1-10
    price_competitiveness = Column(Numeric(3, 1))  # 1-10
    payment_terms = Column(String(30))  # net_15, net_30, cod
    minimum_order = Column(Numeric(10, 2))
    delivery_schedule_json = Column(Text, default="[]")  # JSON
    relationship_status = Column(String(20), default="active")  # active, trial, dormant, blacklisted
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    deleted_at = Column(DateTime)

    prices = relationship("IngredientPrice", back_populates="supplier", cascade="all, delete-orphan")


class IngredientPrice(Base):
    __tablename__ = "ingredient_prices"

    id = Column(Integer, primary_key=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    price_per_unit = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(20), nullable=False, default="kg")
    effective_date = Column(DateTime, default=_utcnow)
    quoted_price = Column(Numeric(10, 2))
    invoice_price = Column(Numeric(10, 2))
    volume_tier = Column(String(50))
    delivery_terms = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=_utcnow)

    ingredient = relationship("Ingredient", back_populates="prices")
    supplier = relationship("Supplier", back_populates="prices")


# ---------------------------------------------------------------------------
# Production domain
# ---------------------------------------------------------------------------

class ProductionCalendar(Base):
    __tablename__ = "production_calendars"

    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    week_start_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    entries = relationship("ProductionEntry", back_populates="calendar", cascade="all, delete-orphan")


class ProductionEntry(Base):
    __tablename__ = "production_entries"

    id = Column(Integer, primary_key=True)
    calendar_id = Column(Integer, ForeignKey("production_calendars.id"), nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    planned_quantity = Column(Integer, nullable=False)
    actual_quantity = Column(Integer)
    scheduled_date = Column(DateTime, nullable=False)
    slot = Column(String(20))  # early_prep, morning_prep, mid_prep, service_prep, pm_prep
    assigned_to = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="planned")  # planned, in_progress, completed, cancelled
    notes = Column(Text)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    calendar = relationship("ProductionCalendar", back_populates="entries")
    recipe = relationship("Recipe")


class ParLevel(Base):
    __tablename__ = "par_levels"

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    base_par = Column(Integer, nullable=False)
    safety_buffer = Column(Integer, default=0)
    effective_par = Column(Integer, nullable=False)  # base_par + safety_buffer
    review_frequency = Column(String(20), default="weekly")  # weekly, monthly
    last_reviewed = Column(DateTime)
    auto_adjusted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    recipe = relationship("Recipe")

    __table_args__ = (
        UniqueConstraint("recipe_id", "location_id", name="uq_par_recipe_location"),
    )


class DemandForecast(Base):
    __tablename__ = "demand_forecasts"

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    predicted_demand = Column(Integer)
    actual_demand = Column(Integer)
    day_of_week_factor = Column(Numeric(5, 3), default=1.0)
    seasonal_factor = Column(Numeric(5, 3), default=1.0)
    event_factor = Column(Numeric(5, 3), default=1.0)
    created_at = Column(DateTime, default=_utcnow)

    recipe = relationship("Recipe")


# ---------------------------------------------------------------------------
# Waste domain
# ---------------------------------------------------------------------------

class WasteLog(Base):
    __tablename__ = "waste_logs"

    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    logged_by = Column(Integer, ForeignKey("users.id"))
    logged_at = Column(DateTime, default=_utcnow)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))  # nullable: might be raw ingredient waste
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"))  # nullable: might be finished product
    category = Column(String(30), nullable=False)  # overproduction, spoilage, trim, plate, cooking_loss, damaged
    quantity = Column(Numeric(10, 4), nullable=False)
    unit = Column(String(20), nullable=False, default="kg")
    cost_estimate = Column(Numeric(10, 2))  # auto-calculated from ingredient/recipe cost
    reason = Column(Text)
    photo_url = Column(String(500))
    created_at = Column(DateTime, default=_utcnow)


class ShelfLifeTracker(Base):
    __tablename__ = "shelf_life_tracker"

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    produced_at = Column(DateTime, nullable=False, default=_utcnow)
    expires_at = Column(DateTime, nullable=False)
    quantity_produced = Column(Integer, nullable=False)
    quantity_remaining = Column(Integer, nullable=False)
    status = Column(String(20), default="fresh")  # fresh, use_soon, expired, consumed
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    recipe = relationship("Recipe")


# ---------------------------------------------------------------------------
# Culinary intelligence domain (elBulli)
# ---------------------------------------------------------------------------

class Technique(Base):
    __tablename__ = "techniques"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(30), nullable=False)  # Heat, Cold, Texture, Flavor, Preservation, Assembly, Preparation
    subcategory = Column(String(50))
    description = Column(Text)
    difficulty_level = Column(Integer, default=1)  # 1-5
    equipment_required_json = Column(Text, default="[]")
    time_profile = Column(String(20))  # quick, medium, long
    best_for_json = Column(Text, default="[]")  # proteins, vegetables, grains, etc.
    season_affinity_json = Column(Text, default="[]")  # summer, winter, year-round
    flavor_impact = Column(String(200))
    texture_impact = Column(String(200))
    related_techniques_json = Column(Text, default="[]")
    in_use = Column(Boolean, default=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    deleted_at = Column(DateTime)


class RecipeTechnique(Base):
    __tablename__ = "recipe_techniques"

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    technique_id = Column(Integer, ForeignKey("techniques.id"), nullable=False)
    step_order = Column(Integer)
    created_at = Column(DateTime, default=_utcnow)

    __table_args__ = (
        UniqueConstraint("recipe_id", "technique_id", name="uq_recipe_technique"),
    )

    recipe = relationship("Recipe")
    technique = relationship("Technique")


class DishDNA(Base):
    __tablename__ = "dish_dna"

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False, unique=True)
    technique_fingerprint_json = Column(Text, default="[]")  # ordered list of technique IDs
    flavor_profile_json = Column(Text, default="{}")  # {savory, sweet, acid, bitter, umami} 0-10
    texture_profile_json = Column(Text, default="{}")  # {crispy, creamy, chewy, tender} 0-10
    cuisine_influences_json = Column(Text, default="[]")
    seasonal_peak = Column(String(20))  # spring, summer, fall, winter
    complexity_score = Column(Integer, default=1)  # 1-10
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    recipe = relationship("Recipe")


class DishEvolution(Base):
    __tablename__ = "dish_evolutions"

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    parent_recipe_id = Column(Integer, ForeignKey("recipes.id"))
    generation = Column(Integer, default=1)
    evolution_type = Column(String(30))  # refinement, seasonal_swap, cost_optimization, technique_change, fusion, customer_feedback
    evolution_date = Column(DateTime, default=_utcnow)
    changelog_json = Column(Text, default="[]")
    techniques_added_json = Column(Text, default="[]")
    techniques_removed_json = Column(Text, default="[]")
    ingredients_swapped_json = Column(Text, default="[]")  # [{old, new, reason}]
    performance_delta_json = Column(Text, default="{}")  # {margin_change, popularity_change, waste_change}
    evolved_by = Column(String(100))
    created_at = Column(DateTime, default=_utcnow)

    recipe = relationship("Recipe", foreign_keys=[recipe_id])
    parent_recipe = relationship("Recipe", foreign_keys=[parent_recipe_id])


class IngredientAffinity(Base):
    __tablename__ = "ingredient_affinities"

    id = Column(Integer, primary_key=True)
    ingredient_a_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    ingredient_b_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    strength_score = Column(Numeric(3, 1), nullable=False)  # 0-10
    notes = Column(Text)
    created_at = Column(DateTime, default=_utcnow)

    __table_args__ = (
        UniqueConstraint("ingredient_a_id", "ingredient_b_id", name="uq_ingredient_affinity"),
    )

    ingredient_a = relationship("Ingredient", foreign_keys=[ingredient_a_id])
    ingredient_b = relationship("Ingredient", foreign_keys=[ingredient_b_id])


class IngredientSeason(Base):
    __tablename__ = "ingredient_seasons"

    id = Column(Integer, primary_key=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    season = Column(String(20), nullable=False)  # spring, summer, fall, winter
    is_peak = Column(Boolean, default=False)
    months_json = Column(Text, default="[]")  # array of month numbers
    created_at = Column(DateTime, default=_utcnow)

    ingredient = relationship("Ingredient")
