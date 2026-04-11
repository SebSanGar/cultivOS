"""Tests for GET /api/farms/{farm_id}/regen-scorecard/export.pdf."""

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def farm(db):
    from cultivos.db.models import Farm
    f = Farm(name="Rancho PDF Test", state="Jalisco", total_hectares=10.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@pytest.fixture
def field(db, farm):
    from cultivos.db.models import Field
    f = Field(farm_id=farm.id, name="Parcela PDF", crop_type="maiz", hectares=5.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def _add_treatment(db, field_id, organic=True):
    from cultivos.db.models import TreatmentRecord
    t = TreatmentRecord(
        field_id=field_id,
        health_score_used=70.0,
        problema="Baja fertilidad",
        causa_probable="Suelo degradado",
        tratamiento="Composta organica",
        costo_estimado_mxn=500,
        urgencia="media",
        prevencion="Aplicar anualmente",
        organic=organic,
    )
    db.add(t)
    db.commit()


def _add_soil(db, field_id, organic_matter_pct=3.5):
    from cultivos.db.models import SoilAnalysis
    from datetime import datetime
    s = SoilAnalysis(
        field_id=field_id,
        organic_matter_pct=organic_matter_pct,
        sampled_at=datetime.utcnow(),
        ph=6.5,
    )
    db.add(s)
    db.commit()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_unknown_farm_returns_404(client):
    resp = client.get("/api/farms/9999/regen-scorecard/export.pdf")
    assert resp.status_code == 404


def test_returns_pdf_content_type(client, db, farm, field):
    _add_treatment(db, field.id)
    _add_soil(db, field.id)
    resp = client.get(f"/api/farms/{farm.id}/regen-scorecard/export.pdf")
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers["content-type"]


def test_returns_non_empty_bytes(client, db, farm, field):
    _add_treatment(db, field.id)
    resp = client.get(f"/api/farms/{farm.id}/regen-scorecard/export.pdf")
    assert resp.status_code == 200
    assert len(resp.content) > 100  # real PDF is kilobytes, not empty


def test_empty_farm_returns_pdf_not_error(client, farm):
    """Farm with no fields still returns a valid PDF (zero-value rows)."""
    resp = client.get(f"/api/farms/{farm.id}/regen-scorecard/export.pdf")
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers["content-type"]
    assert len(resp.content) > 100


def test_pdf_starts_with_pdf_magic_bytes(client, db, farm, field):
    """Response bytes should start with %PDF — valid PDF magic bytes."""
    resp = client.get(f"/api/farms/{farm.id}/regen-scorecard/export.pdf")
    assert resp.status_code == 200
    assert resp.content[:4] == b"%PDF"
