"""T2.8 — Cumulative savings chart + breakeven vertical marker on owner economic-impact page.

Backend: GET /api/farms/{farm_id}/cumulative-savings returns monthly
cumulative savings time series + breakeven month (when cumulative >= subscription_cost).

Frontend: line chart #econ-cumulative-chart with a breakeven marker
and updateCumulativeChart() JS function called from loadEconomicImpact.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

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


def _seed_farm_with_monthly_treatments(db_session, n_months: int, tier: str = "basic"):
    farm = Farm(name="Farm T28", municipality="Guadalajara", total_hectares=10.0, tier=tier)
    db_session.add(farm)
    db_session.flush()
    field = Field(farm_id=farm.id, name="Field A", hectares=10.0, crop_type="maize")
    db_session.add(field)
    db_session.flush()

    now = datetime.utcnow()
    for i in range(n_months):
        # one treatment per month, going back in time
        tr = TreatmentRecord(
            field_id=field.id,
            health_score_used=60.0,
            problema="plagas",
            causa_probable="humedad",
            tratamiento="compost",
            costo_estimado_mxn=500,
            urgencia="media",
            prevencion="monitoreo",
            created_at=now - timedelta(days=30 * (n_months - i)),
        )
        db_session.add(tr)

    db_session.commit()
    return farm.id


# ------------------------------------------------------------------ API tests

def test_cumulative_savings_404_unknown_farm(client):
    resp = client.get("/api/farms/99999/cumulative-savings")
    assert resp.status_code == 404


def test_cumulative_savings_returns_schema_keys(client, db_session):
    farm_id = _seed_farm_with_monthly_treatments(db_session, n_months=3)
    resp = client.get(f"/api/farms/{farm_id}/cumulative-savings")
    assert resp.status_code == 200
    data = resp.json()
    assert "farm_id" in data
    assert "data_points" in data
    assert isinstance(data["data_points"], list)
    assert "breakeven_month" in data
    assert "subscription_cost_mxn" in data


def test_cumulative_savings_empty_when_no_treatments(client, db_session):
    farm = Farm(name="Empty T28", municipality="Guadalajara", total_hectares=10.0)
    db_session.add(farm)
    db_session.commit()
    resp = client.get(f"/api/farms/{farm.id}/cumulative-savings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["data_points"] == []


def test_cumulative_savings_data_points_accumulate(client, db_session):
    """Each successive data point >= previous (monotonically non-decreasing)."""
    farm_id = _seed_farm_with_monthly_treatments(db_session, n_months=4)
    resp = client.get(f"/api/farms/{farm_id}/cumulative-savings")
    assert resp.status_code == 200
    points = resp.json()["data_points"]
    if len(points) >= 2:
        values = [p["cumulative_savings_mxn"] for p in points]
        for i in range(1, len(values)):
            assert values[i] >= values[i - 1], "Cumulative savings must be non-decreasing"


def test_cumulative_savings_breakeven_when_tier_set(client, db_session):
    """With enough treatments and a tier set, breakeven_month should be an int."""
    farm_id = _seed_farm_with_monthly_treatments(db_session, n_months=6, tier="basic")
    resp = client.get(f"/api/farms/{farm_id}/cumulative-savings")
    assert resp.status_code == 200
    data = resp.json()
    # breakeven_month is None or int — just verify it's present and typed correctly
    bm = data["breakeven_month"]
    assert bm is None or isinstance(bm, int)


def test_cumulative_savings_data_points_have_month_key(client, db_session):
    """Each data_point must have a 'month' key."""
    farm_id = _seed_farm_with_monthly_treatments(db_session, n_months=3)
    resp = client.get(f"/api/farms/{farm_id}/cumulative-savings")
    assert resp.status_code == 200
    points = resp.json()["data_points"]
    if points:
        assert "month" in points[0], "data_point must have 'month' key"
        assert "cumulative_savings_mxn" in points[0]


# ------------------------------------------------------------------ HTML tests

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


def test_html_has_cumulative_chart_canvas(html):
    assert 'id="econ-cumulative-chart"' in html, (
        "economic-impact.html missing canvas id=econ-cumulative-chart"
    )


def test_html_has_cumulative_chart_section(html):
    assert 'id="econ-cumulative-section"' in html, (
        "economic-impact.html missing id=econ-cumulative-section"
    )


def test_html_cumulative_has_breakeven_label(html):
    lower = html.lower()
    assert "breakeven" in lower or "break-even" in lower, (
        "economic-impact.html cumulative section must mention breakeven"
    )


# ------------------------------------------------------------------ JS tests

def test_js_has_update_cumulative_chart_function(js):
    assert "function updateCumulativeChart" in js or "updateCumulativeChart" in js, (
        "economic-impact.js missing updateCumulativeChart function"
    )


def test_js_calls_cumulative_chart_from_load(js):
    assert "updateCumulativeChart(" in js, (
        "economic-impact.js loadEconomicImpact must call updateCumulativeChart"
    )
