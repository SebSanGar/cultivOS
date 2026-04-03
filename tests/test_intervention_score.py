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


# --- Ancestral method matching tests (#110) ---


def test_ancestral_treatment_ranked_higher():
    """A treatment linked to an ancestral method should rank higher than identical without."""
    base = {
        "problema": "Materia organica baja",
        "tratamiento": "Composta",
        "costo_estimado_mxn": 2000,
        "urgencia": "media",
        "health_score_used": 50.0,
    }
    treatments = [
        {**base, "tratamiento": "Composta convencional"},
        {
            **base,
            "tratamiento": "Composta milpa (ancestral)",
            "ancestral_method_name": "Milpa intercropping",
            "ancestral_base_cientifica": "Polyculture nitrogen fixation",
        },
    ]
    results = score_treatments(treatments, feedback={}, hectares=5.0)
    # Ancestral treatment should rank first due to boost
    assert results[0]["tratamiento"] == "Composta milpa (ancestral)"
    assert results[0]["intervention_score"] > results[1]["intervention_score"]


def test_ancestral_fields_present_in_response():
    """Scored treatments should include metodo_ancestral and scientific_basis fields."""
    treatments = [
        {
            "problema": "pH alcalino",
            "tratamiento": "Azufre elemental",
            "costo_estimado_mxn": 800,
            "urgencia": "media",
            "health_score_used": 50.0,
            "ancestral_method_name": "Xok k'iin calendar",
            "ancestral_base_cientifica": "3500 years of Yucatec Maya practice",
        },
    ]
    results = score_treatments(treatments, feedback={}, hectares=5.0)
    assert results[0]["metodo_ancestral"] == "Xok k'iin calendar"
    assert results[0]["scientific_basis"] == "3500 years of Yucatec Maya practice"


def test_no_ancestral_fields_are_none():
    """Treatments without ancestral data should have None for ancestral fields."""
    treatments = [
        {
            "problema": "Test",
            "tratamiento": "Tratamiento",
            "costo_estimado_mxn": 1000,
            "urgencia": "media",
            "health_score_used": 50.0,
        },
    ]
    results = score_treatments(treatments, feedback={}, hectares=5.0)
    assert results[0]["metodo_ancestral"] is None
    assert results[0]["scientific_basis"] is None


def test_api_ancestral_fields_in_response(client, db, farm_and_field):
    """API should return metodo_ancestral and scientific_basis for ancestral treatments."""
    farm, field = farm_and_field

    tr = TreatmentRecord(
        field_id=field.id,
        health_score_used=45.0,
        problema="Materia organica baja",
        causa_probable="Suelo degradado",
        tratamiento="Milpa companion planting",
        costo_estimado_mxn=1500,
        urgencia="alta",
        prevencion="Mantener cobertura vegetal",
        organic=True,
        ancestral_method_name="Milpa intercropping",
        ancestral_base_cientifica="Polyculture nitrogen fixation validated by FAO",
    )
    db.add(tr)
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intervention-scores")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["metodo_ancestral"] == "Milpa intercropping"
    assert data[0]["scientific_basis"] == "Polyculture nitrogen fixation validated by FAO"


def test_api_ancestral_treatment_ranked_higher(client, db, farm_and_field):
    """API: ancestral-linked treatment should rank above identical non-ancestral."""
    farm, field = farm_and_field

    # Non-ancestral treatment
    tr1 = TreatmentRecord(
        field_id=field.id,
        health_score_used=50.0,
        problema="Deficiencia de nitrogeno",
        causa_probable="Suelo agotado",
        tratamiento="Te de composta generico",
        costo_estimado_mxn=2000,
        urgencia="media",
        prevencion="Rotar cultivos",
        organic=True,
    )
    # Ancestral treatment (same cost, urgencia, health)
    tr2 = TreatmentRecord(
        field_id=field.id,
        health_score_used=50.0,
        problema="Deficiencia de nitrogeno",
        causa_probable="Suelo agotado",
        tratamiento="Milpa frijol-maiz (ancestral)",
        costo_estimado_mxn=2000,
        urgencia="media",
        prevencion="Intercalado tradicional",
        organic=True,
        ancestral_method_name="Milpa intercropping",
        ancestral_base_cientifica="Legume nitrogen fixation — 3500 years practice",
    )
    db.add_all([tr1, tr2])
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intervention-scores")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    # Ancestral should be first
    assert data[0]["metodo_ancestral"] == "Milpa intercropping"
    assert data[1]["metodo_ancestral"] is None


# --- Cost-benefit analysis tests (D3) ---


def test_roi_calculated():
    """Expected ROI should reflect benefit-to-cost ratio in percentage."""
    treatments = [
        {
            "problema": "Materia organica baja",
            "tratamiento": "Composta madura",
            "costo_estimado_mxn": 2500,
            "urgencia": "alta",
            "health_score_used": 40.0,
        },
    ]
    results = score_treatments(treatments, feedback={}, hectares=5.0)
    assert len(results) == 1
    assert "expected_roi" in results[0]
    # With cost 2500 over 5ha = 500 MXN/ha, and alta urgency with room to improve,
    # ROI should be positive (benefit exceeds cost)
    assert results[0]["expected_roi"] > 0


def test_payback_days_calculated():
    """Payback days should reflect time to recover treatment cost."""
    treatments = [
        {
            "problema": "Humedad baja",
            "tratamiento": "Acolchado organico",
            "costo_estimado_mxn": 2000,
            "urgencia": "alta",
            "health_score_used": 30.0,
        },
    ]
    results = score_treatments(treatments, feedback={}, hectares=10.0)
    assert len(results) == 1
    assert "payback_days" in results[0]
    # Cost is low (200 MXN/ha), alta urgency with low health = high benefit
    # Payback should be relatively fast (< 90 days)
    assert results[0]["payback_days"] > 0
    assert results[0]["payback_days"] < 90


def test_zero_cost_roi():
    """Zero-cost treatments should have 100% ROI and 0 payback days."""
    treatments = [
        {
            "problema": "Compactacion",
            "tratamiento": "Arado con traccion animal",
            "costo_estimado_mxn": 0,
            "urgencia": "media",
            "health_score_used": 50.0,
        },
    ]
    results = score_treatments(treatments, feedback={}, hectares=5.0)
    assert results[0]["expected_roi"] == 100.0
    assert results[0]["payback_days"] == 0


def test_high_cost_negative_roi():
    """Very expensive treatments with low impact should have negative ROI."""
    treatments = [
        {
            "problema": "Test",
            "tratamiento": "Expensive low impact",
            "costo_estimado_mxn": 50000,
            "urgencia": "baja",
            "health_score_used": 90.0,  # high health = low room for improvement
        },
    ]
    results = score_treatments(treatments, feedback={}, hectares=1.0)
    # 50000 MXN on 1 ha, baja urgency, health already at 90 — ROI should be negative
    assert results[0]["expected_roi"] < 0


def test_roi_higher_with_feedback():
    """Treatments with positive feedback should have higher ROI via success probability."""
    treatments = [
        {
            "problema": "Deficiencia de nitrogeno",
            "tratamiento": "Te de composta",
            "costo_estimado_mxn": 2000,
            "urgencia": "media",
            "health_score_used": 50.0,
        },
    ]
    feedback = {
        "Deficiencia de nitrogeno": FeedbackSummary(
            avg_rating=4.5, positive_ratio=0.9, count=5
        ),
    }
    with_fb = score_treatments(treatments, feedback=feedback, hectares=5.0)
    without_fb = score_treatments(treatments, feedback={}, hectares=5.0)
    # Higher success probability → higher benefit → higher ROI
    assert with_fb[0]["expected_roi"] > without_fb[0]["expected_roi"]


def test_payback_days_capped():
    """When benefit is near zero, payback should be capped at 999 days."""
    treatments = [
        {
            "problema": "Test",
            "tratamiento": "Expensive no gain",
            "costo_estimado_mxn": 10000,
            "urgencia": "baja",
            "health_score_used": 99.0,  # almost perfect — minimal delta
        },
    ]
    results = score_treatments(treatments, feedback={}, hectares=1.0)
    # Very low benefit, high cost — payback should be capped
    assert results[0]["payback_days"] <= 999


def test_api_returns_roi_fields(client, db, farm_and_field):
    """API response should include expected_roi and payback_days."""
    farm, field = farm_and_field

    tr = TreatmentRecord(
        field_id=field.id,
        health_score_used=40.0,
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
    assert "expected_roi" in data[0]
    assert "payback_days" in data[0]
    assert isinstance(data[0]["expected_roi"], (int, float))
    assert isinstance(data[0]["payback_days"], int)
