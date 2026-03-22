"""
SQLAlchemy ORM models for cultivOS.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
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
    trend = Column(String(20))  # improving, stable, declining, critical
    scored_at = Column(DateTime, default=datetime.utcnow)

    field = relationship("Field", back_populates="health_scores")
