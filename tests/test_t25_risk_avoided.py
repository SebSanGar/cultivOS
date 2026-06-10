"""T2.5 — Risk avoided: perdida potencial evitada, NEVER summed into total_savings.

Tests verify:
  - Backend: risk_avoided_mxn field present on EconomicImpactOut
  - With treatments → risk_avoided_mxn > 0
  - Without treatments → risk_avoided_mxn is None
  - total_savings_mxn = water + fert + yield only (risk NOT summed)
  - assumptions.py has risk_per_treatment_mxn entry
  - Frontend HTML has the risk-avoided section with "not included" disclaimer
  - JS has updateRiskAvoided function called from loadEconomicImpact
"""

import re
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cultivos.app import create_app
from cultivos.db.models import Base, Farm, Field, HealthScore, TreatmentRecord
from cultivos.db.session import get_db


# ------------------------------------------------------------------ fixtures

SQLALCHEMY_DATABASE_URL = "sqlite://"


@pytest.fixture()
def db_session():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session):
    app = create_app()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def _seed_farm_with_treatments(db_session, n_treatments: int):
    """Seed one farm + one field + n health scores + n_treatments."""
    farm = Farm(name="Test Farm T25", municipality="Guadalajara", total_hectares=20.0, tier="basic")
    db_session.add(farm)
    db_session.flush()

    field = Field(farm_id=farm.id, name="Field A", hectares=20.0, crop_type="maize")
    db_session.add(field)
    db_session.flush()

    # Always add a health score so has_real_data = True
    hs = HealthScore(field_id=field.id, score=75.0)
    db_session.add(hs)

    for i in range(n_treatments):
        tr = TreatmentRecord(
            field_id=field.id,
            health_score_used=75.0,
            problema="plagas",
            causa_probable="humedad alta",
            tratamiento="compost organico",
            costo_estimado_mxn=500,
            urgencia="media",
            prevencion="monitoreo semanal",
        )
        db_session.add(tr)

    db_session.commit()
    return farm.id


# ------------------------------------------------------------------ backend tests

def test_risk_avoided_field_in_response_with_treatments(client, db_session):
    """risk_avoided_mxn key must be present in response when treatments exist."""
    farm_id = _seed_farm_with_treatments(db_session, n_treatments=3)
    resp = client.get(f"/api/farms/{farm_id}/economic-impact")
    assert resp.status_code == 200
    data = resp.json()
    assert "risk_avoided_mxn" in data


def test_risk_avoided_positive_when_treatments_exist(client, db_session):
    """With treatments present, risk_avoided_mxn should be > 0."""
    farm_id = _seed_farm_with_treatments(db_session, n_treatments=4)
    resp = client.get(f"/api/farms/{farm_id}/economic-impact")
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_avoided_mxn"] is not None
    assert data["risk_avoided_mxn"] > 0


def test_risk_avoided_none_when_no_treatments(client, db_session):
    """With zero treatments, risk_avoided_mxn must be None."""
    farm_id = _seed_farm_with_treatments(db_session, n_treatments=0)
    resp = client.get(f"/api/farms/{farm_id}/economic-impact")
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_avoided_mxn"] is None


def test_total_savings_does_not_include_risk(client, db_session):
    """Honesty rule 8: total_savings_mxn = water + fert + yield only. Risk never summed."""
    farm_id = _seed_farm_with_treatments(db_session, n_treatments=5)
    resp = client.get(f"/api/farms/{farm_id}/economic-impact")
    assert resp.status_code == 200
    data = resp.json()
    expected_total = (
        data["water_savings_mxn"]
        + data["fertilizer_savings_mxn"]
        + data["yield_improvement_mxn"]
    )
    assert data["total_savings_mxn"] == expected_total, (
        f"total_savings_mxn {data['total_savings_mxn']} != "
        f"water+fert+yield {expected_total}: risk must not be summed in"
    )


def test_risk_avoided_scales_with_treatment_count(client, db_session):
    """More treatments → higher risk_avoided_mxn (per-treatment model)."""
    farm_id_few = _seed_farm_with_treatments(db_session, n_treatments=2)
    resp_few = client.get(f"/api/farms/{farm_id_few}/economic-impact")

    farm = Farm(name="Farm Many T25", municipality="Guadalajara", total_hectares=20.0, tier="basic")
    db_session.add(farm)
    db_session.flush()
    field = Field(farm_id=farm.id, name="F", hectares=20.0, crop_type="maize")
    db_session.add(field)
    db_session.flush()
    hs = HealthScore(field_id=field.id, score=75.0)
    db_session.add(hs)
    for i in range(8):
        db_session.add(TreatmentRecord(
            field_id=field.id,
            health_score_used=75.0,
            problema="plagas",
            causa_probable="humedad alta",
            tratamiento="compost organico",
            costo_estimado_mxn=500,
            urgencia="media",
            prevencion="monitoreo semanal",
        ))
    db_session.commit()

    resp_many = client.get(f"/api/farms/{farm.id}/economic-impact")
    assert resp_few.status_code == 200
    assert resp_many.status_code == 200
    risk_few = resp_few.json()["risk_avoided_mxn"] or 0
    risk_many = resp_many.json()["risk_avoided_mxn"] or 0
    assert risk_many > risk_few


def test_assumption_registry_has_risk_per_treatment(client, db_session):
    """assumptions.py REGISTRY must have risk_per_treatment_mxn with source + status."""
    from cultivos.services.intelligence.assumptions import REGISTRY
    assert "risk_per_treatment_mxn" in REGISTRY, "assumptions.py missing risk_per_treatment_mxn"
    rec = REGISTRY["risk_per_treatment_mxn"]
    assert rec["source_url"], "risk_per_treatment_mxn must have non-empty source_url"
    assert rec["status"] in ("measured", "literature", "model_assumption")


# ------------------------------------------------------------------ frontend HTML tests

@pytest.fixture()
def html():
    path = __file__.replace("tests/test_t25_risk_avoided.py", "frontend/economic-impact.html")
    import os
    abs_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "frontend", "economic-impact.html"
    )
    with open(abs_path) as f:
        return f.read()


@pytest.fixture()
def js():
    import os
    abs_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "frontend", "economic-impact.js"
    )
    with open(abs_path) as f:
        return f.read()


def test_html_has_risk_avoided_section(html):
    """HTML must have a dedicated risk-avoided section div."""
    assert 'id="econ-risk-avoided-section"' in html, (
        "economic-impact.html missing id=econ-risk-avoided-section"
    )


def test_html_has_risk_avoided_value_element(html):
    """HTML must have an element to render the risk-avoided value."""
    assert 'id="econ-risk-avoided-value"' in html


def test_html_has_not_included_disclaimer(html):
    """HTML must state risk is NOT included in the total above (honesty)."""
    lower = html.lower()
    assert "not included" in lower or "separate from" in lower or "not summed" in lower, (
        "economic-impact.html must clarify risk-avoided is not included in total savings"
    )


def test_js_has_update_risk_avoided_function(js):
    """JS must define updateRiskAvoided() function."""
    assert "function updateRiskAvoided" in js or "updateRiskAvoided" in js


def test_js_calls_update_risk_avoided_from_load(js):
    """loadEconomicImpact must call updateRiskAvoided(data)."""
    assert "updateRiskAvoided(data)" in js, (
        "economic-impact.js loadEconomicImpact must call updateRiskAvoided(data)"
    )


def test_model_has_risk_avoided_field():
    """EconomicImpactOut Pydantic model must have risk_avoided_mxn Optional[int]."""
    from cultivos.models.economics import EconomicImpactOut
    import inspect
    fields = EconomicImpactOut.model_fields
    assert "risk_avoided_mxn" in fields, "EconomicImpactOut missing risk_avoided_mxn field"
