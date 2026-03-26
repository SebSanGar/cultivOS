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
