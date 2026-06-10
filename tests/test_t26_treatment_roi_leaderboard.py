"""T2.6 — Treatment ROI leaderboard on the owner economic-impact page.

The backend endpoint already exists (/api/farms/{id}/treatment-roi).
These tests cover the frontend wiring: the leaderboard section in
economic-impact.html and the updateTreatmentRoiLeaderboard JS function.

Also verifies the API returns 200 with expected schema when called from
the economic-impact context.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.pool import StaticPool

from cultivos.app import create_app
from cultivos.db.models import Base, Farm, Field, HealthScore, TreatmentRecord
from cultivos.db.session import get_db


# ------------------------------------------------------------------ fixtures

@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
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


@pytest.fixture()
def html():
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "economic-impact.html")
    with open(path) as f:
        return f.read()


@pytest.fixture()
def js():
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "economic-impact.js")
    with open(path) as f:
        return f.read()


# ------------------------------------------------------------------ API tests

def test_treatment_roi_endpoint_404_unknown_farm(client):
    resp = client.get("/api/farms/99999/treatment-roi")
    assert resp.status_code == 404


def test_treatment_roi_endpoint_returns_schema_keys(client, db_session):
    farm = Farm(name="Farm T26", municipality="Guadalajara", total_hectares=10.0)
    db_session.add(farm)
    db_session.commit()
    resp = client.get(f"/api/farms/{farm.id}/treatment-roi")
    assert resp.status_code == 200
    data = resp.json()
    assert "farm_id" in data
    assert "treatments" in data
    assert isinstance(data["treatments"], list)


def test_treatment_roi_empty_when_no_treatments(client, db_session):
    farm = Farm(name="Farm T26 Empty", municipality="Guadalajara", total_hectares=10.0)
    db_session.add(farm)
    db_session.commit()
    resp = client.get(f"/api/farms/{farm.id}/treatment-roi")
    assert resp.status_code == 200
    assert resp.json()["treatments"] == []


# ------------------------------------------------------------------ HTML tests

def test_html_has_treatment_roi_section(html):
    assert 'id="econ-treatment-roi-section"' in html, (
        "economic-impact.html missing id=econ-treatment-roi-section"
    )


def test_html_has_treatment_roi_table(html):
    assert 'id="econ-treatment-roi-table"' in html, (
        "economic-impact.html missing id=econ-treatment-roi-table"
    )


def test_html_treatment_roi_section_has_title(html):
    lower = html.lower()
    assert "treatment roi" in lower or "best investments" in lower or "treatment return" in lower, (
        "economic-impact.html treatment-roi section needs a descriptive title"
    )


def test_html_treatment_roi_has_empty_state(html):
    assert 'id="econ-treatment-roi-empty"' in html, (
        "economic-impact.html missing id=econ-treatment-roi-empty for empty state"
    )


# ------------------------------------------------------------------ JS tests

def test_js_has_update_treatment_roi_function(js):
    assert "function updateTreatmentRoiLeaderboard" in js or "updateTreatmentRoiLeaderboard" in js, (
        "economic-impact.js missing updateTreatmentRoiLeaderboard function"
    )


def test_js_calls_treatment_roi_from_load(js):
    assert "updateTreatmentRoiLeaderboard(" in js, (
        "economic-impact.js loadEconomicImpact must call updateTreatmentRoiLeaderboard"
    )
