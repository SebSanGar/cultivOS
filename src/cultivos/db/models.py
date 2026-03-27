"""
SQLAlchemy ORM models for cultivOS.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
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
    created_at = Column(DateTime, default=datetime.utcnow)

    fields = relationship("Field", back_populates="farm", cascade="all, delete-orphan")
    weather_records = relationship("WeatherRecord", back_populates="farm", cascade="all, delete-orphan")


class Field(Base):
    __tablename__ = "fields"

    id = Column(Integer, primary_key=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    name = Column(String(100), nullable=False)
    crop_type = Column(String(50))  # maiz, agave, aguacate, etc.
    hectares = Column(Float, default=0)
    boundary_geojson = Column(Text)  # GeoJSON polygon
    created_at = Column(DateTime, default=datetime.utcnow)

    farm = relationship("Farm", back_populates="fields")
    flights = relationship("FlightLog", back_populates="field", cascade="all, delete-orphan")
    health_scores = relationship("HealthScore", back_populates="field", cascade="all, delete-orphan")
    soil_analyses = relationship("SoilAnalysis", back_populates="field", cascade="all, delete-orphan")
    ndvi_results = relationship("NDVIResult", back_populates="field", cascade="all, delete-orphan")
    treatments = relationship("TreatmentRecord", back_populates="field", cascade="all, delete-orphan")
    thermal_results = relationship("ThermalResult", back_populates="field", cascade="all, delete-orphan")
    microbiome_records = relationship("MicrobiomeRecord", back_populates="field", cascade="all, delete-orphan")


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
    created_at = Column(DateTime, default=datetime.utcnow)

    field = relationship("Field", back_populates="treatments")


class ThermalResult(Base):
    __tablename__ = "thermal_results"

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


class WeatherRecord(Base):
    __tablename__ = "weather_records"

    id = Column(Integer, primary_key=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    temp_c = Column(Float, nullable=False)
    humidity_pct = Column(Float, nullable=False)
    wind_kmh = Column(Float, nullable=False)
    description = Column(String(200), nullable=False)
    forecast_3day = Column(JSON, nullable=False, default=list)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    farm = relationship("Farm", back_populates="weather_records")
