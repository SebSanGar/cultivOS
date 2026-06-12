"""T2.10 — CAD/Ontario guard on economic-impact endpoint.

When Farm.country == 'CA', the MXN Jalisco assumptions do NOT apply.
Endpoint must return a clear 'coming soon' message and null/zero for
all dollar figures instead of silently applying Mexico-only estimates.

Frontend economic-impact.html shows a "Proximamente" banner for CA farms.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Base, Farm, Field, HealthScore
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


def _seed_farm(db_session, country: str = "MX"):
    farm = Farm(name="Test Farm T210", municipality="Toronto" if country == "CA" else "Guadalajara",
                total_hectares=20.0, country=country, tier="basic")
    db_session.add(farm)
    db_session.flush()
    field = Field(farm_id=farm.id, name="Field A", hectares=20.0, crop_type="maize")
    db_session.add(field)
    db_session.flush()
    db_session.add(HealthScore(field_id=field.id, score=70.0))
    db_session.commit()
    return farm.id


# ------------------------------------------------------------------ API tests

def test_mx_farm_returns_nonzero_savings(client, db_session):
    """MX farm should return non-zero total_savings_mxn."""
    farm_id = _seed_farm(db_session, country="MX")
    resp = client.get(f"/api/farms/{farm_id}/economic-impact")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_savings_mxn"] > 0


def test_ca_farm_returns_zero_savings(client, db_session):
    """CA farm must return zero total_savings_mxn — Jalisco MXN assumptions do not apply."""
    farm_id = _seed_farm(db_session, country="CA")
    resp = client.get(f"/api/farms/{farm_id}/economic-impact")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_savings_mxn"] == 0, (
        f"CA farm must not apply MXN Jalisco assumptions; got {data['total_savings_mxn']}"
    )


def test_ca_farm_nota_says_coming_soon(client, db_session):
    """CA farm nota must mention coming soon / Proximamente / Ontario baseline."""
    farm_id = _seed_farm(db_session, country="CA")
    resp = client.get(f"/api/farms/{farm_id}/economic-impact")
    assert resp.status_code == 200
    nota = resp.json().get("nota", "").lower()
    assert any(kw in nota for kw in ["coming soon", "proximamente", "ontario", "ca baseline"]), (
        f"CA farm nota should mention Ontario/coming-soon, got: {nota!r}"
    )


def test_ca_farm_roi_fields_are_null(client, db_session):
    """CA farm: roi_multiple, net_savings_mxn, payback_months must all be null."""
    farm_id = _seed_farm(db_session, country="CA")
    resp = client.get(f"/api/farms/{farm_id}/economic-impact")
    assert resp.status_code == 200
    data = resp.json()
    assert data["roi_multiple"] is None
    assert data["net_savings_mxn"] is None
    assert data["payback_months"] is None


def test_ca_season_report_pdf_generates_without_mx_estimates(client, db_session):
    """Season report PDF must still generate for CA farms (returns 200, not 500)."""
    farm_id = _seed_farm(db_session, country="CA")
    resp = client.get(f"/api/farms/{farm_id}/season-report-pdf")
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers.get("content-type", "")


# ------------------------------------------------------------------ HTML tests

@pytest.fixture()
def html():
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "economic-impact.html")
    with open(path) as f:
        return f.read()


def test_html_has_ontario_coming_soon_element(html):
    """HTML must have an element shown for CA farms with 'coming soon' / Proximamente text."""
    assert 'id="econ-ontario-soon"' in html, (
        "economic-impact.html missing id=econ-ontario-soon element for CA farms"
    )


def test_html_ontario_element_contains_coming_soon_text(html):
    lower = html.lower()
    # Must have coming-soon text inside econ-ontario-soon element
    assert "coming soon" in lower or "proximamente" in lower, (
        "economic-impact.html must have coming-soon / Proximamente text for Ontario"
    )


@pytest.fixture()
def js():
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "economic-impact.js")
    with open(path) as f:
        return f.read()


def test_js_defines_update_ontario_soon_banner(js):
    """economic-impact.js must define updateOntarioSoonBanner function (called in loadEconomicImpact)."""
    assert "function updateOntarioSoonBanner" in js, (
        "economic-impact.js missing updateOntarioSoonBanner function definition — "
        "it is called on every farm load and will ReferenceError without a definition"
    )


def test_js_ontario_banner_checks_nota(js):
    """updateOntarioSoonBanner must check data.nota to detect Ontario farms."""
    assert "data.nota" in js or "nota" in js, (
        "updateOntarioSoonBanner should read data.nota to detect Ontario/CA farms"
    )


def test_js_ontario_banner_shows_element(js):
    """updateOntarioSoonBanner must show #econ-ontario-soon for Ontario farms."""
    assert "econ-ontario-soon" in js, (
        "updateOntarioSoonBanner must reference econ-ontario-soon element"
    )
