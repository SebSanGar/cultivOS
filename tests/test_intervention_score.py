"""Tests for predictive intervention scoring — TDD: tests first."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import (
    Base,
    Farm,
    FarmerFeedback,
    Field,
    HealthScore,
    SoilAnalysis,
    TreatmentRecord,
)
from cultivos.db.session import get_db
from cultivos.services.intelligence.intervention_score import (
    FeedbackSummary,
    ScoredTreatment,
    score_treatments,
)


@pytest.fixture()
def db(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture()
def client(db):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


@pytest.fixture()
def farm_and_field(db):
    farm = Farm(name="Rancho Test", location_lat=20.6, location_lon=-103.3)
    db.add(farm)
    db.commit()
    db.refresh(farm)
    field = Field(farm_id=farm.id, name="Parcela A", crop_type="maiz", hectares=5.0)
    db.add(field)
    db.commit()
    db.refresh(field)
    return farm, field


# --- Pure function tests ---


def test_treatments_ranked_by_score():
    """Treatments should be ranked by composite intervention score (highest first)."""
    treatments = [
        {
            "problema": "Materia organica baja",
            "tratamiento": "Incorporar composta madura",
            "costo_estimado_mxn": 3000,
            "urgencia": "alta",
            "health_score_used": 40.0,
        },
        {
            "problema": "Deficiencia de nitrogeno",
            "tratamiento": "Aplicar te de composta",
            "costo_estimado_mxn": 1200,
            "urgencia": "media",
            "health_score_used": 60.0,
        },
    ]
    results = score_treatments(treatments, feedback={}, hectares=5.0)
    assert len(results) == 2
    # All results should have intervention_score
    assert all(r["intervention_score"] > 0 for r in results)
    # Results should be sorted descending by intervention_score
    assert results[0]["intervention_score"] >= results[1]["intervention_score"]


def test_feedback_backed_treatments_rank_higher():
    """Treatments with positive feedback should rank higher than similar without."""
    treatments = [
        {
            "problema": "Deficiencia de fosforo",
            "tratamiento": "Aplicar harina de hueso",
            "costo_estimado_mxn": 2000,
            "urgencia": "media",
            "health_score_used": 50.0,
        },
        {
            "problema": "Deficiencia de nitrogeno",
            "tratamiento": "Aplicar te de composta",
            "costo_estimado_mxn": 2000,
            "urgencia": "media",
            "health_score_used": 50.0,
        },
    ]
    # Nitrogen treatment has positive feedback
    feedback = {
        "Deficiencia de nitrogeno": FeedbackSummary(
            avg_rating=4.5, positive_ratio=0.9, count=5
        ),
    }
    results = score_treatments(treatments, feedback=feedback, hectares=5.0)
    # The nitrogen treatment (with feedback) should rank first
    assert results[0]["problema"] == "Deficiencia de nitrogeno"
    assert results[0]["success_probability"] > results[1]["success_probability"]


def test_cost_efficiency_calculated():
    """Cost efficiency should be MXN per hectare."""
    treatments = [
        {
            "problema": "Humedad baja",
            "tratamiento": "Acolchado organico",
            "costo_estimado_mxn": 2500,
            "urgencia": "alta",
            "health_score_used": 30.0,
        },
    ]
    results = score_treatments(treatments, feedback={}, hectares=10.0)
    assert len(results) == 1
    assert results[0]["cost_per_hectare"] == 250.0  # 2500 / 10


def test_graceful_no_feedback():
    """When no feedback data exists, score still works with defaults."""
    treatments = [
        {
            "problema": "pH alcalino",
            "tratamiento": "Azufre elemental",
            "costo_estimado_mxn": 800,
            "urgencia": "alta",
            "health_score_used": 45.0,
        },
    ]
    results = score_treatments(treatments, feedback={}, hectares=5.0)
    assert len(results) == 1
    assert results[0]["intervention_score"] > 0
    assert results[0]["success_probability"] == 0.5  # default when no feedback


def test_urgency_affects_score():
    """Alta urgency should boost expected health delta more than media/baja."""
    treatments_alta = [
        {
            "problema": "Test alta",
            "tratamiento": "Tratamiento A",
            "costo_estimado_mxn": 1000,
            "urgencia": "alta",
            "health_score_used": 40.0,
        },
    ]
    treatments_baja = [
        {
            "problema": "Test baja",
            "tratamiento": "Tratamiento B",
            "costo_estimado_mxn": 1000,
            "urgencia": "baja",
            "health_score_used": 40.0,
        },
    ]
    result_alta = score_treatments(treatments_alta, feedback={}, hectares=5.0)
    result_baja = score_treatments(treatments_baja, feedback={}, hectares=5.0)
    assert result_alta[0]["expected_health_delta"] > result_baja[0]["expected_health_delta"]


def test_zero_hectares_defaults():
    """Zero hectares should default to 1.0 to avoid division by zero."""
    treatments = [
        {
            "problema": "Test",
            "tratamiento": "Tratamiento",
            "costo_estimado_mxn": 1000,
            "urgencia": "media",
            "health_score_used": 50.0,
        },
    ]
    results = score_treatments(treatments, feedback={}, hectares=0.0)
    assert results[0]["cost_per_hectare"] == 1000.0  # defaults to 1 ha


# --- API endpoint tests ---


def test_api_returns_scored_treatments(client, db, farm_and_field):
    """GET endpoint returns scored treatments for a field."""
    farm, field = farm_and_field

    # Create health score and treatment records
    hs = HealthScore(field_id=field.id, score=45.0, scored_at=datetime.utcnow())
    db.add(hs)
    db.commit()

    tr = TreatmentRecord(
        field_id=field.id,
        health_score_used=45.0,
        problema="Materia organica baja",
        causa_probable="Suelo degradado",
        tratamiento="Composta madura",
        costo_estimado_mxn=3000,
        urgencia="alta",
        prevencion="No quemar rastrojo",
        organic=True,
    )
    db.add(tr)
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intervention-scores")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert "intervention_score" in data[0]
    assert "cost_per_hectare" in data[0]
    assert "success_probability" in data[0]
    assert "expected_health_delta" in data[0]


def test_api_includes_feedback_in_scoring(client, db, farm_and_field):
    """When feedback exists for a treatment type, it should affect the score."""
    farm, field = farm_and_field

    hs = HealthScore(field_id=field.id, score=40.0, scored_at=datetime.utcnow())
    db.add(hs)
    db.commit()

    tr = TreatmentRecord(
        field_id=field.id,
        health_score_used=40.0,
        problema="Deficiencia de nitrogeno",
        causa_probable="Suelo agotado",
        tratamiento="Te de composta",
        costo_estimado_mxn=1200,
        urgencia="alta",
        prevencion="Rotar con leguminosas",
        organic=True,
        applied_at=datetime.utcnow() - timedelta(days=30),
    )
    db.add(tr)
    db.commit()
    db.refresh(tr)

    # Add positive feedback
    fb = FarmerFeedback(
        field_id=field.id,
        treatment_id=tr.id,
        rating=5,
        worked=True,
    )
    db.add(fb)
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intervention-scores")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    # With positive feedback, success_probability should be > default 0.5
    assert data[0]["success_probability"] > 0.5


def test_api_no_treatments_returns_empty(client, db, farm_and_field):
    """No treatments → empty list, not an error."""
    farm, field = farm_and_field
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intervention-scores")
    assert resp.status_code == 200
    assert resp.json() == []
