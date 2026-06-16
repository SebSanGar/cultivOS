"""Ontario / Canada economics on the economic-impact endpoint.

SUPERSEDES the old T2.10 "coming soon" guard (2026-06-15, Canada-first): CA
farms now compute REAL savings from Ontario (CAD) assumptions instead of $0.
The model is rainfed — water savings is 0 — and subscription/ROI stay null
until CA pricing is configured. See services/intelligence/assumptions.py
(*_per_ha_ca records sourced from OMAFRA Pub 60 2025 + StatCan + GFO).
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Base, Farm, Field, HealthScore
from cultivos.db.session import get_db


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


def _seed_farm(db_session, country: str = "MX"):
    farm = Farm(name="Test Farm T210", municipality="Chatham-Kent" if country == "CA" else "Guadalajara",
                state="Ontario" if country == "CA" else "Jalisco",
                total_hectares=20.0, country=country, tier="basic")
    db_session.add(farm)
    db_session.flush()
    crop = "corn" if country == "CA" else "maize"
    field = Field(farm_id=farm.id, name="Field A", hectares=20.0, crop_type=crop)
    db_session.add(field)
    db_session.flush()
    db_session.add(HealthScore(field_id=field.id, score=70.0))
    db_session.commit()
    return farm.id


# ------------------------------------------------------------------ API tests

def test_mx_farm_returns_nonzero_savings(client, db_session):
    farm_id = _seed_farm(db_session, country="MX")
    resp = client.get(f"/api/farms/{farm_id}/economic-impact")
    assert resp.status_code == 200
    assert resp.json()["total_savings_mxn"] > 0


def test_ca_farm_returns_real_savings(client, db_session):
    """CA farm now computes real savings from Ontario (CAD) assumptions — not $0."""
    farm_id = _seed_farm(db_session, country="CA")
    resp = client.get(f"/api/farms/{farm_id}/economic-impact")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_savings_mxn"] > 0, "CA farm should compute real Ontario savings"


def test_ca_farm_has_no_water_savings(client, db_session):
    """Ontario field crops are rainfed — the water lever is 0."""
    farm_id = _seed_farm(db_session, country="CA")
    data = client.get(f"/api/farms/{farm_id}/economic-impact").json()
    assert data["water_savings_mxn"] == 0
    # the savings come from fertilizer + yield instead
    assert data["fertilizer_savings_mxn"] > 0 or data["yield_improvement_mxn"] > 0


def test_ca_farm_nota_is_ontario_not_coming_soon(client, db_session):
    farm_id = _seed_farm(db_session, country="CA")
    nota = client.get(f"/api/farms/{farm_id}/economic-impact").json().get("nota", "").lower()
    assert "ontario" in nota
    assert "coming soon" not in nota and "do not apply" not in nota and "proximamente" not in nota


def test_ca_farm_roi_null_until_pricing_configured(client, db_session):
    """No CA subscription pricing yet → ROI/net/payback null (never apply MX pricing)."""
    farm_id = _seed_farm(db_session, country="CA")
    data = client.get(f"/api/farms/{farm_id}/economic-impact").json()
    assert data["subscription_cost_mxn"] is None
    assert data["roi_multiple"] is None
    assert data["net_savings_mxn"] is None
    assert data["payback_months"] is None


def test_ca_season_report_pdf_generates(client, db_session):
    farm_id = _seed_farm(db_session, country="CA")
    resp = client.get(f"/api/farms/{farm_id}/season-report-pdf")
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers.get("content-type", "")


# ------------------------------------------------------------------ no-currency-leak + obsolete-banner-gone

@pytest.fixture()
def page_files():
    import os
    base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
    with open(os.path.join(base, "economic-impact.html")) as f:
        html = f.read()
    with open(os.path.join(base, "economic-impact.js")) as f:
        js = f.read()
    return html, js


def test_obsolete_coming_soon_banner_removed(page_files):
    html, js = page_files
    assert "econ-ontario-soon" not in html
    assert "do not apply" not in html.lower()
    assert "updateOntarioSoonBanner" not in js


def test_no_currency_code_in_user_facing_strings(page_files):
    """Currency-neutral rule: never print MXN/CAD/pesos in displayed text."""
    html, js = page_files
    # field-name reads like data.total_savings_mxn are fine; a displayed " MXN" suffix is not
    assert "' MXN'" not in js and '" MXN"' not in js
