"""Tests for per-field treatment cost effectiveness — task #125."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord
from cultivos.db.session import get_db


@pytest.fixture()
def client(db):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db

    farm = Farm(name="Rancho Test")
    db.add(farm)
    db.flush()

    field = Field(name="Parcela Norte", farm_id=farm.id)
    db.add(field)
    db.flush()

    # Treatment with a subsequent health score — so delta is computable
    applied = datetime(2026, 3, 1, 8, 0)
    tr = TreatmentRecord(
        field_id=field.id,
        health_score_used=55.0,
        problema="Bajo nitrogeno",
        causa_probable="Suelo agotado",
        tratamiento="Lombricomposta 2 ton/ha",
        costo_estimado_mxn=3000,
        urgencia="media",
        prevencion="Rotar cultivos",
        organic=True,
        applied_at=applied,
    )
    db.add(tr)
    db.flush()

    # Health score AFTER the treatment
    hs = HealthScore(
        field_id=field.id,
        score=70.0,
        scored_at=applied + timedelta(days=15),
        sources=["soil"],
        breakdown={},
    )
    db.add(hs)
    db.commit()

    db.info["farm_id"] = farm.id
    db.info["field_id"] = field.id

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture()
def empty_client(db):
    """Farm + field with no treatments."""
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db

    farm = Farm(name="Rancho Vacio")
    db.add(farm)
    db.flush()
    field = Field(name="Parcela Vacia", farm_id=farm.id)
    db.add(field)
    db.commit()

    db.info["farm_id"] = farm.id
    db.info["field_id"] = field.id

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


def _url(farm_id, field_id):
    return f"/api/farms/{farm_id}/fields/{field_id}/treatment-cost-effectiveness"


def test_no_treatments_returns_empty(empty_client, db):
    fid = db.info["farm_id"]
    lid = db.info["field_id"]
    resp = empty_client.get(_url(fid, lid))
    assert resp.status_code == 200
    assert resp.json() == []


def test_treatment_with_health_delta(client, db):
    fid = db.info["farm_id"]
    lid = db.info["field_id"]
    resp = client.get(_url(fid, lid))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    item = data[0]
    assert item["cost_mxn"] == 3000
    assert item["health_before"] == 55.0
    assert item["health_after"] == 70.0
    assert item["health_delta"] == 15.0


def test_response_fields_present(client, db):
    fid = db.info["farm_id"]
    lid = db.info["field_id"]
    resp = client.get(_url(fid, lid))
    assert resp.status_code == 200
    item = resp.json()[0]
    assert "tratamiento" in item
    assert "cost_mxn" in item
    assert "health_before" in item
    assert "health_after" in item
    assert "health_delta" in item


def test_unknown_farm_returns_404(client):
    resp = client.get(_url(99999, 1))
    assert resp.status_code == 404


def test_unknown_field_returns_404(client, db):
    fid = db.info["farm_id"]
    resp = client.get(_url(fid, 99999))
    assert resp.status_code == 404
