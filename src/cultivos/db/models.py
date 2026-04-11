"""
SQLAlchemy ORM models for cultivOS.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    owner_name = Column(String(100))
    location_lat = Column(Float)
    location_lon = Column(Float)
    total_hectares = Column(Float, default=0)
    municipality = Column(String(100))
    state = Column(String(50), default="Jalisco")
    country = Column(String(10), default="MX")
    cooperative_id = Column(Integer, ForeignKey("cooperatives.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    fields = relationship("Field", back_populates="farm", cascade="all, delete-orphan")
    weather_records = relationship("WeatherRecord", back_populates="farm", cascade="all, delete-orphan")
    cooperative = relationship("Cooperative", back_populates="farms")


class Field(Base):
    __tablename__ = "fields"

    id = Column(Integer, primary_key=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    name = Column(String(100), nullable=False)
    crop_type = Column(String(50))  # maiz, agave, aguacate, etc.
    hectares = Column(Float, default=0)
    planted_at = Column(DateTime, nullable=True)  # when crop was planted (for phenology)
    boundary_coordinates = Column(JSON)  # [[lon, lat], ...] polygon vertices
    computed_area_hectares = Column(Float)  # auto-computed from boundary polygon
    created_at = Column(DateTime, default=datetime.utcnow)

    farm = relationship("Farm", back_populates="fields")
    flights = relationship("FlightLog", back_populates="field", cascade="all, delete-orphan")
    health_scores = relationship("HealthScore", back_populates="field", cascade="all, delete-orphan")
    soil_analyses = relationship("SoilAnalysis", back_populates="field", cascade="all, delete-orphan")
    ndvi_results = relationship("NDVIResult", back_populates="field", cascade="all, delete-orphan")
    treatments = relationship("TreatmentRecord", back_populates="field", cascade="all, delete-orphan")
    thermal_results = relationship("ThermalResult", back_populates="field", cascade="all, delete-orphan")
    microbiome_records = relationship("MicrobiomeRecord", back_populates="field", cascade="all, delete-orphan")
    harvest_records = relationship("HarvestRecord", back_populates="field", cascade="all, delete-orphan")
    carbon_baselines = relationship("CarbonBaseline", back_populates="field", cascade="all, delete-orphan")
    observations = relationship("FarmerObservation", back_populates="field", cascade="all, delete-orphan")


class FlightLog(Base):
    __tablename__ = "flight_logs"

    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False)
    drone_type = Column(String(50))  # mavic_multispectral, mavic_thermal, agras_t100
    mission_type = Column(String(50))  # health_scan, thermal_check, spray
    flight_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Float)
    altitude_m = Column(Float)
    images_count = Column(Integer, default=0)
    coverage_pct = Column(Float, default=0)
    s3_path = Column(String(500))  # path to processed imagery
    status = Column(String(20), default="pending")  # pending, processing, complete, failed
    created_at = Column(DateTime, default=datetime.utcnow)

    field = relationship("Field", back_populates="flights")


class HealthScore(Base):
    __tablename__ = "health_scores"
    __table_args__ = (
        Index("ix_health_scores_field_scored", "field_id", "scored_at"),
    )

    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False)
    flight_id = Column(Integer, ForeignKey("flight_logs.id"))
    score = Column(Float, nullable=False)  # 0-100
    ndvi_mean = Column(Float)
    ndvi_std = Column(Float)
    thermal_max = Column(Float)
    thermal_min = Column(Float)
    stress_pct = Column(Float)  # % of field under stress
    soil_ph = Column(Float)
    soil_organic_matter_pct = Column(Float)
    trend = Column(String(20))  # improving, stable, declining
    sources = Column(JSON, nullable=False, default=list)  # ["ndvi", "soil"]
    breakdown = Column(JSON, nullable=False, default=dict)  # component → sub-score
    scored_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    field = relationship("Field", back_populates="health_scores")


class SoilAnalysis(Base):
    __tablename__ = "soil_analyses"
    __table_args__ = (
        Index("ix_soil_analyses_field_sampled", "field_id", "sampled_at"),
    )

    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False)
    ph = Column(Float)  # 0-14 scale
    organic_matter_pct = Column(Float)  # percentage
    nitrogen_ppm = Column(Float)  # parts per million
    phosphorus_ppm = Column(Float)
    potassium_ppm = Column(Float)
    texture = Column(String(50))  # clay, loam, sand, silt, etc.
    moisture_pct = Column(Float)  # percentage
    electrical_conductivity = Column(Float)  # dS/m (salinity indicator)
    depth_cm = Column(Float)  # sampling depth
    notes = Column(Text)
    recommendations = Column(Text)  # regenerative treatment suggestions
    sampled_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    field = relationship("Field", back_populates="soil_analyses")


class NDVIResult(Base):
    __tablename__ = "ndvi_results"
    __table_args__ = (
        Index("ix_ndvi_results_field_analyzed", "field_id", "analyzed_at"),
    )

    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False)
    flight_id = Column(Integer, ForeignKey("flight_logs.id"))
    ndvi_mean = Column(Float, nullable=False)
    ndvi_std = Column(Float, nullable=False)
    ndvi_min = Column(Float, nullable=False)
    ndvi_max = Column(Float, nullable=False)
    pixels_total = Column(Integer, nullable=False)
    stress_pct = Column(Float, nullable=False)  # % of pixels below 0.4
    zones = Column(JSON, nullable=False)  # list of zone dicts
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    field = relationship("Field", back_populates="ndvi_results")


class TreatmentRecord(Base):
    __tablename__ = "treatment_records"
    __table_args__ = (
        Index("ix_treatment_records_field_applied", "field_id", "applied_at"),
    )

    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False)
    health_score_used = Column(Float, nullable=False)
    problema = Column(String(200), nullable=False)
    causa_probable = Column(String(300), nullable=False)
    tratamiento = Column(Text, nullable=False)
    costo_estimado_mxn = Column(Integer, nullable=False, default=0)
    urgencia = Column(String(20), nullable=False)  # alta, media, baja
    prevencion = Column(Text, nullable=False)
    organic = Column(Boolean, nullable=False, default=True)
    ancestral_method_name = Column(String(100), nullable=True)  # linked ancestral method
    ancestral_base_cientifica = Column(Text, nullable=True)  # scientific validation
    ancestral_razon_match = Column(String(300), nullable=True)  # why this method matches
    timing_consejo = Column(Text, nullable=True)  # weather-based timing advice
    applied_at = Column(DateTime, nullable=True)  # when the farmer applied the treatment
    applied_notes = Column(Text, nullable=True)  # farmer's notes on application
    created_at = Column(DateTime, default=datetime.utcnow)

    field = relationship("Field", back_populates="treatments")


class ThermalResult(Base):
    __tablename__ = "thermal_results"
    __table_args__ = (
        Index("ix_thermal_results_field_analyzed", "field_id", "analyzed_at"),
    )

    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False)
    flight_id = Column(Integer, ForeignKey("flight_logs.id"))
    temp_mean = Column(Float, nullable=False)
    temp_std = Column(Float, nullable=False)
    temp_min = Column(Float, nullable=False)
    temp_max = Column(Float, nullable=False)
    pixels_total = Column(Integer, nullable=False)
    stress_pct = Column(Float, nullable=False)
    irrigation_deficit = Column(Boolean, nullable=False, default=False)
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    field = relationship("Field", back_populates="thermal_results")


class MicrobiomeRecord(Base):
    __tablename__ = "microbiome_records"

    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False)
    respiration_rate = Column(Float, nullable=False)  # mg CO2/kg/day
    microbial_biomass_carbon = Column(Float, nullable=False)  # mg C/kg soil
    fungi_bacteria_ratio = Column(Float, nullable=False)
    classification = Column(String(20), nullable=False)  # healthy, moderate, degraded
    sampled_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    field = relationship("Field", back_populates="microbiome_records")


class AncestralMethod(Base):
    __tablename__ = "ancestral_methods"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description_es = Column(Text, nullable=False)
    region = Column(String(100), nullable=False)  # e.g. "Jalisco", "Mesoamerica"
    practice_type = Column(String(50), nullable=False)  # soil_management, intercropping, water_management, etc.
    crops = Column(JSON, nullable=False, default=list)  # ["maiz", "frijol", ...]
    benefits_es = Column(Text, nullable=False)
    scientific_basis = Column(Text)  # modern scientific validation
    problems = Column(JSON, nullable=True, default=list)  # ["erosion", "compaction", ...]
    applicable_months = Column(JSON, nullable=True, default=None)  # [1, 2, ..., 12]
    timing_rationale = Column(Text, nullable=True)  # Spanish — why this season
    ecological_benefit = Column(Integer, nullable=True)  # 1-5 scale


class Fertilizer(Base):
    __tablename__ = "fertilizers"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description_es = Column(Text, nullable=False)
    application_method = Column(Text, nullable=False)
    cost_per_ha_mxn = Column(Integer, nullable=False, default=0)
    nutrient_profile = Column(String(200), nullable=False)
    suitable_crops = Column(JSON, nullable=False, default=list)  # ["maiz", "agave", ...]


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False, unique=True)
    hashed_password = Column(String(200), nullable=False)
    role = Column(String(20), nullable=False, default="farmer")  # admin, researcher, farmer
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=True)  # only for farmer role
    created_at = Column(DateTime, default=datetime.utcnow)

    farm = relationship("Farm")


class Disease(Base):
    __tablename__ = "diseases"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description_es = Column(Text, nullable=False)
    symptoms = Column(JSON, nullable=False, default=list)  # ["hojas amarillas", "manchas", ...]
    affected_crops = Column(JSON, nullable=False, default=list)  # ["maiz", "frijol", ...]
    treatments = Column(JSON, nullable=False, default=list)  # [{"name": ..., "description_es": ..., "organic": True}, ...]
    region = Column(String(100), nullable=False, default="Jalisco")
    severity = Column(String(20), nullable=False, default="media")  # alta, media, baja


class CropType(Base):
    __tablename__ = "crop_types"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    family = Column(String(100), nullable=False)  # e.g. "Poaceae", "Fabaceae"
    growing_season = Column(String(100), nullable=False)  # e.g. "temporal (Jun-Oct)"
    water_needs = Column(String(50), nullable=False)  # alta, media, baja
    regions = Column(JSON, nullable=False, default=list)  # ["Jalisco", "Ontario"]
    companions = Column(JSON, nullable=False, default=list)  # companion plants for intercropping
    days_to_harvest = Column(Integer)  # approximate days from sowing
    optimal_temp_min = Column(Float)  # degrees C
    optimal_temp_max = Column(Float)
    description_es = Column(Text, nullable=False)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)  # low_health, irrigation, pest
    message = Column(Text, nullable=False)
    phone_number = Column(String(20))  # recipient phone (E.164 format)
    status = Column(String(20), default="pending")  # pending, sent, failed
    sent_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    farm = relationship("Farm")
    field = relationship("Field")


class FarmerFeedback(Base):
    __tablename__ = "farmer_feedback"

    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False)
    treatment_id = Column(Integer, ForeignKey("treatment_records.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    worked = Column(Boolean, nullable=False)
    farmer_notes = Column(Text, nullable=True)
    alternative_method = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    field = relationship("Field")
    treatment = relationship("TreatmentRecord")


class WeatherRecord(Base):
    __tablename__ = "weather_records"
    __table_args__ = (
        Index("ix_weather_records_farm_recorded", "farm_id", "recorded_at"),
    )

    id = Column(Integer, primary_key=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    temp_c = Column(Float, nullable=False)
    humidity_pct = Column(Float, nullable=False)
    wind_kmh = Column(Float, nullable=False)
    rainfall_mm = Column(Float, nullable=False, default=0.0)
    description = Column(String(200), nullable=False)
    forecast_3day = Column(JSON, nullable=False, default=list)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    farm = relationship("Farm", back_populates="weather_records")


class AlertLog(Base):
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=True)
    alert_type = Column(String(50), nullable=False)  # health, irrigation, pest, recommendation
    message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, default="info")  # info, warning, critical
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    farm = relationship("Farm")
    field = relationship("Field")


class AlertConfig(Base):
    __tablename__ = "alert_configs"

    id = Column(Integer, primary_key=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False, unique=True)
    health_score_floor = Column(Float, nullable=False, default=40.0)
    ndvi_minimum = Column(Float, nullable=False, default=0.3)
    temp_max_c = Column(Float, nullable=False, default=45.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    farm = relationship("Farm")


class PredictionSnapshot(Base):
    __tablename__ = "prediction_snapshots"
    __table_args__ = (
        Index("ix_prediction_snapshots_field_type", "field_id", "prediction_type"),
    )

    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False)
    prediction_type = Column(String(30), nullable=False)  # yield, health
    predicted_value = Column(Float, nullable=False)
    actual_value = Column(Float, nullable=True)
    predicted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    field = relationship("Field")


class Cooperative(Base):
    __tablename__ = "cooperatives"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    state = Column(String(50), default="Jalisco")
    contact_name = Column(String(100), nullable=True)
    contact_phone = Column(String(30), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    farms = relationship("Farm", back_populates="cooperative")


class FieldPhoto(Base):
    __tablename__ = "field_photos"

    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(50), default="image/jpeg")
    size_bytes = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    analysis_json = Column(JSON, nullable=True)

    field = relationship("Field")


class CropVariety(Base):
    __tablename__ = "crop_varieties"

    id = Column(Integer, primary_key=True)
    crop_name = Column(String(50), nullable=False)  # e.g. "maiz", "agave"
    name = Column(String(100), nullable=False, unique=True)  # e.g. "Maiz Azul Criollo"
    region = Column(String(100), nullable=False)  # e.g. "Jalisco", "Altos de Jalisco"
    altitude_m = Column(Integer, nullable=True)  # optimal altitude in metres
    water_mm = Column(Integer, nullable=True)  # annual water needs in mm
    diseases = Column(JSON, nullable=False, default=list)  # ["corn_smut", "rust", ...]
    adaptation_notes = Column(Text, nullable=True)  # Spanish-language notes


class HarvestRecord(Base):
    __tablename__ = "harvest_records"
    __table_args__ = (
        Index("ix_harvest_records_field_date", "field_id", "harvest_date"),
    )

    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False)
    crop_type = Column(String(50), nullable=False)
    harvest_date = Column(DateTime, nullable=False)
    actual_yield_kg = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    field = relationship("Field", back_populates="harvest_records")


class AgronomistTip(Base):
    __tablename__ = "agronomist_tips"

    id = Column(Integer, primary_key=True)
    crop = Column(String(50), nullable=False)        # maiz, agave, frijol, chile, tomate, etc.
    problem = Column(String(100), nullable=False)    # drought, disease, nutrient_deficiency, water_stress, etc.
    tip_text_es = Column(Text, nullable=False)       # advice in Spanish
    source = Column(String(150), nullable=True)      # CIMMYT, INIFAP, agronomist name, etc.
    region = Column(String(100), nullable=True)      # jalisco, mexico, latam
    season = Column(String(50), nullable=True)       # dry, wet, all


class CarbonBaseline(Base):
    """Explicit SOC baseline measurement for carbon finance and grant reporting."""
    __tablename__ = "carbon_baselines"

    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False)
    soc_percent = Column(Float, nullable=False)           # soil organic carbon %
    measurement_date = Column(String(10), nullable=False) # YYYY-MM-DD
    lab_method = Column(String(100), nullable=False)      # dry_combustion, loss_on_ignition, wet_oxidation, etc.
    recorded_at = Column(DateTime, default=datetime.utcnow)

    field = relationship("Field", back_populates="carbon_baselines")


class FarmerVocabulary(Base):
    """Jalisco farmer colloquial phrases mapped to formal agronomic terms + actions."""
    __tablename__ = "farmer_vocabulary"

    id = Column(Integer, primary_key=True)
    phrase = Column(String(200), nullable=False)         # colloquial phrase (e.g. "se está petateando")
    formal_term_es = Column(String(150), nullable=False) # formal agronomic term (e.g. "marchitamiento")
    likely_cause = Column(String(200), nullable=False)   # most probable cause in Spanish
    recommended_action = Column(Text, nullable=False)    # organic-first action in Spanish
    crop = Column(String(50), nullable=True)             # optional crop scope (maiz, agave, etc.)
    symptom = Column(String(100), nullable=True)         # symptom category (yellowing, pest, drought, dying, etc.)


class FarmerObservation(Base):
    """Ground-truth observations logged by farmers — completes the data loop (drone + sensor + farmer eyes)."""
    __tablename__ = "farmer_observations"
    __table_args__ = (
        Index("ix_farmer_observations_field_created", "field_id", "created_at"),
    )

    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False)
    observation_es = Column(Text, nullable=False)           # farmer's observation in Spanish
    observation_type = Column(String(20), nullable=False)   # problem | success | neutral
    crop_stage = Column(String(100), nullable=True)         # e.g. germinacion, floracion, cosecha
    created_at = Column(DateTime, default=datetime.utcnow)

    field = relationship("Field", back_populates="observations")
