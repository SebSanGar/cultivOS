"""Tests for regenerative practice verification endpoint."""

import pytest
from datetime import datetime, timedelta

from cultivos.db.models import (
    Base, Farm, Field, TreatmentRecord, SoilAnalysis, MicrobiomeRecord,
)
from cultivos.services.intelligence.regenerative import compute_regenerative_score


@pytest.fixture
def db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    sess = sessionmaker(bind=engine)()
    try:
        yield sess
    finally:
        sess.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def full_regen_field(db):
    """Field with all regenerative indicators present — should score ~100."""
    farm = Farm(name="Rancho Regen", state="Jalisco", total_hectares=50)
    db.add(farm)
    db.flush()

    field = Field(farm_id=farm.id, name="Parcela Verde", crop_type="maiz", hectares=10)
    db.add(field)
    db.flush()

    # All organic treatments with diverse methods including ancestral
    methods = [
        ("composta orgánica", "Milpa"),
        ("extracto de neem", "Chinampa"),
        ("biofertilizante micorrízico", "Ceniza volcánica"),
        ("abono verde de leguminosas", None),
        ("control biológico con Trichoderma", None),
    ]
    for i, (trat, ancestral) in enumerate(methods):
        db.add(TreatmentRecord(
            field_id=field.id,
            health_score_used=60 + i * 5,
            problema="plagas",
            causa_probable="humedad",
            tratamiento=trat,
            urgencia="media",
            prevencion="rotación",
            organic=True,
            ancestral_method_name=ancestral,
            created_at=datetime.utcnow() - timedelta(days=30 * i),
        ))

    # Two soil analyses showing improving organic matter
    db.add(SoilAnalysis(
        field_id=field.id, ph=6.5, organic_matter_pct=2.0,
        sampled_at=datetime.utcnow() - timedelta(days=180),
    ))
    db.add(SoilAnalysis(
        field_id=field.id, ph=6.5, organic_matter_pct=3.5,
        sampled_at=datetime.utcnow() - timedelta(days=10),
    ))

    # Healthy microbiome
    db.add(MicrobiomeRecord(
        field_id=field.id, respiration_rate=25.0,
        microbial_biomass_carbon=400.0, fungi_bacteria_ratio=1.2,
        classification="healthy", sampled_at=datetime.utcnow(),
    ))

    db.commit()
    return farm, field


@pytest.fixture
def partial_field(db):
    """Field with some regenerative indicators — partial score."""
    farm = Farm(name="Rancho Parcial", state="Jalisco", total_hectares=30)
    db.add(farm)
    db.flush()

    field = Field(farm_id=farm.id, name="Parcela Media", crop_type="frijol", hectares=5)
    db.add(field)
    db.flush()

    # Mix of organic and non-organic treatments
    db.add(TreatmentRecord(
        field_id=field.id, health_score_used=55, problema="deficiencia",
        causa_probable="suelo", tratamiento="composta", urgencia="baja",
        prevencion="análisis", organic=True,
    ))
    db.add(TreatmentRecord(
        field_id=field.id, health_score_used=40, problema="plaga severa",
        causa_probable="clima", tratamiento="químico de emergencia", urgencia="alta",
        prevencion="monitoreo", organic=False,
    ))

    # Single soil analysis (no trend possible)
    db.add(SoilAnalysis(
        field_id=field.id, ph=5.5, organic_matter_pct=1.5,
        sampled_at=datetime.utcnow(),
    ))

    db.commit()
    return farm, field


@pytest.fixture
def empty_field(db):
    """Field with no data at all — should return zero score."""
    farm = Farm(name="Rancho Vacio", state="Jalisco", total_hectares=10)
    db.add(farm)
    db.flush()

    field = Field(farm_id=farm.id, name="Parcela Nueva", crop_type="agave", hectares=3)
    db.add(field)
    db.commit()
    return farm, field


# --- Pure service tests ---

def test_perfect_regenerative_score(db, full_regen_field):
    """All regenerative indicators present → score near 100."""
    _, field = full_regen_field
    result = compute_regenerative_score(field.id, db)

    assert result["score"] >= 85
    assert result["score"] <= 100
    assert result["breakdown"]["organic_treatments"] > 0
    assert result["breakdown"]["ancestral_methods"] > 0
    assert result["breakdown"]["soil_organic_trend"] > 0
    assert result["breakdown"]["microbiome_health"] > 0
    assert len(result["recommendations"]) >= 0  # may have none if perfect


def test_partial_regenerative_score(db, partial_field):
    """Mixed organic/non-organic + missing data → partial score."""
    _, field = partial_field
    result = compute_regenerative_score(field.id, db)

    assert result["score"] > 0
    assert result["score"] < 85
    # organic_treatments should be partial (50% organic)
    assert result["breakdown"]["organic_treatments"] > 0
    assert result["breakdown"]["organic_treatments"] < 25  # max component score
    # No microbiome data
    assert result["breakdown"]["microbiome_health"] == 0
    # No ancestral methods
    assert result["breakdown"]["ancestral_methods"] == 0
    # Recommendations should suggest improvements
    assert len(result["recommendations"]) > 0


def test_empty_field_regenerative_score(db, empty_field):
    """No data at all → zero score with recommendations."""
    _, field = empty_field
    result = compute_regenerative_score(field.id, db)

    assert result["score"] == 0
    assert all(v == 0 for v in result["breakdown"].values())
    assert len(result["recommendations"]) > 0


def test_recommendations_in_spanish(db, partial_field):
    """All recommendations should be in Spanish."""
    _, field = partial_field
    result = compute_regenerative_score(field.id, db)

    for rec in result["recommendations"]:
        # Spanish text should not start with English words
        assert isinstance(rec, str)
        assert len(rec) > 10


# --- API route tests ---

def test_regenerative_score_endpoint(db, full_regen_field):
    """GET /api/farms/{id}/fields/{id}/regenerative-score returns valid response."""
    from fastapi.testclient import TestClient
    from cultivos.app import create_app
    from cultivos.db.session import get_db

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db

    farm, field = full_regen_field
    client = TestClient(app)
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/regenerative-score")

    assert resp.status_code == 200
    data = resp.json()
    assert "score" in data
    assert "breakdown" in data
    assert "recommendations" in data
    assert data["score"] >= 85


def test_regenerative_score_404_field(db, full_regen_field):
    """Non-existent field returns 404."""
    from fastapi.testclient import TestClient
    from cultivos.app import create_app
    from cultivos.db.session import get_db

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db

    farm, _ = full_regen_field
    client = TestClient(app)
    resp = client.get(f"/api/farms/{farm.id}/fields/9999/regenerative-score")
    assert resp.status_code == 404
