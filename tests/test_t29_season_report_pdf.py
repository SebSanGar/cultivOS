"""T2.9 — Season Report Card: exportable PDF for owner economic-impact page.

GET /api/farms/{farm_id}/season-report-pdf returns application/pdf bytes.
Frontend has a "Download Season Report" button linking to the endpoint.

Tests verify:
  - Endpoint returns 200 + application/pdf for existing farm
  - Response is non-empty bytes
  - Content-Disposition header is present (attachment, .pdf filename)
  - 404 for unknown farm
  - Frontend HTML has download-report button/link
  - Frontend HTML button links to /season-report-pdf path
"""

import pytest
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


def _seed_farm(db_session):
    farm = Farm(name="Granja T29", municipality="Guadalajara", total_hectares=20.0, tier="basic")
    db_session.add(farm)
    db_session.flush()
    field = Field(farm_id=farm.id, name="Parcela A", hectares=20.0, crop_type="maize")
    db_session.add(field)
    db_session.flush()
    db_session.add(HealthScore(field_id=field.id, score=72.0))
    db_session.add(TreatmentRecord(
        field_id=field.id,
        health_score_used=65.0,
        problema="plagas",
        causa_probable="humedad alta",
        tratamiento="compost organico",
        costo_estimado_mxn=500,
        urgencia="media",
        prevencion="monitoreo",
    ))
    db_session.commit()
    return farm.id


# ------------------------------------------------------------------ API tests

def test_season_report_pdf_200_for_existing_farm(client, db_session):
    farm_id = _seed_farm(db_session)
    resp = client.get(f"/api/farms/{farm_id}/season-report-pdf")
    assert resp.status_code == 200


def test_season_report_pdf_content_type(client, db_session):
    farm_id = _seed_farm(db_session)
    resp = client.get(f"/api/farms/{farm_id}/season-report-pdf")
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers.get("content-type", "")


def test_season_report_pdf_non_empty_bytes(client, db_session):
    farm_id = _seed_farm(db_session)
    resp = client.get(f"/api/farms/{farm_id}/season-report-pdf")
    assert resp.status_code == 200
    assert len(resp.content) > 100, "PDF response must be non-trivial bytes"


def test_season_report_pdf_content_disposition(client, db_session):
    farm_id = _seed_farm(db_session)
    resp = client.get(f"/api/farms/{farm_id}/season-report-pdf")
    assert resp.status_code == 200
    cd = resp.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert ".pdf" in cd


def test_season_report_pdf_404_unknown_farm(client):
    resp = client.get("/api/farms/99999/season-report-pdf")
    assert resp.status_code == 404


def test_season_report_pdf_works_with_no_treatments(client, db_session):
    """PDF should generate even for farms with no treatment data."""
    farm = Farm(name="Empty Farm T29", municipality="Guadalajara", total_hectares=5.0)
    db_session.add(farm)
    db_session.commit()
    resp = client.get(f"/api/farms/{farm.id}/season-report-pdf")
    assert resp.status_code == 200
    assert len(resp.content) > 100


# ------------------------------------------------------------------ HTML tests

@pytest.fixture()
def html():
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "economic-impact.html")
    with open(path) as f:
        return f.read()


def test_html_has_download_report_button(html):
    """economic-impact.html must have a download report button/link."""
    assert 'id="econ-download-report"' in html, (
        "economic-impact.html missing id=econ-download-report button/link"
    )


def test_html_download_button_links_to_season_report(html):
    """Download link must reference the season-report-pdf endpoint."""
    assert "season-report-pdf" in html, (
        "economic-impact.html download button must link to season-report-pdf"
    )
