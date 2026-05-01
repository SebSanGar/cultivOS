"""Tests for C5 cooperative agenda-semanal endpoint.

GET /api/cooperatives/{coop_id}/agenda-semanal

Composes field_priority across all member farms, flattens fields,
ranks by priority_score DESC, returns top 5 with Spanish action sentences.
Tests monkeypatch compute_field_priority for deterministic control.
"""

import pytest

from cultivos.db.models import Cooperative, Farm, Field
from cultivos.services.intelligence import coop_agenda_semanal as svc


@pytest.fixture
def coop(db):
    c = Cooperative(name="Cooperativa Agenda", state="Jalisco")
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _farm(db, coop, name="Rancho"):
    f = Farm(
        name=name,
        owner_name="Test",
        state="Jalisco",
        total_hectares=50.0,
        cooperative_id=coop.id,
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def _field(db, farm, name="Parcela", crop_type="maiz"):
    fld = Field(name=name, farm_id=farm.id, crop_type=crop_type, hectares=10.0)
    db.add(fld)
    db.commit()
    db.refresh(fld)
    return fld


def _patch_priority(monkeypatch, scores_by_farm):
    """Monkeypatch compute_field_priority to return deterministic data.

    scores_by_farm: {farm_id: [(field_id, name, crop_type, score, issue, action), ...]}
    """

    def fake_priority(farm, db):
        items = scores_by_farm.get(farm.id, [])
        fields = []
        for fid, fname, ctype, score, issue, action in items:
            fields.append({
                "field_id": fid,
                "name": fname,
                "crop_type": ctype,
                "priority_score": score,
                "top_issue": issue,
                "recommended_action": action,
            })
        fields.sort(key=lambda x: x["priority_score"], reverse=True)
        return {"farm_id": farm.id, "fields": fields}

    monkeypatch.setattr(svc, "compute_field_priority", fake_priority)


# --- Test cases ---


def test_schema_keys(db, coop, monkeypatch):
    """Response has all required keys."""
    farm = _farm(db, coop, "Finca A")
    fld = _field(db, farm, "Campo 1")
    _patch_priority(monkeypatch, {
        farm.id: [(fld.id, "Campo 1", "maiz", 75.0, "Estrés hídrico", "Revisar riego")],
    })
    result = svc.compute_coop_agenda_semanal(coop, db)
    assert "coop_name" in result
    assert "total_farms" in result
    assert "total_fields" in result
    assert "top_items" in result
    assert "resumen_es" in result
    item = result["top_items"][0]
    assert "farm_name" in item
    assert "field_name" in item
    assert "priority_score" in item
    assert "top_issue" in item
    assert "accion_es" in item


def test_happy_top5_ranked(db, coop, monkeypatch):
    """Top 5 fields returned ranked by priority_score DESC across farms."""
    farm_a = _farm(db, coop, "Finca A")
    farm_b = _farm(db, coop, "Finca B")
    fa1 = _field(db, farm_a, "A1")
    fa2 = _field(db, farm_a, "A2")
    fa3 = _field(db, farm_a, "A3")
    fb1 = _field(db, farm_b, "B1")
    fb2 = _field(db, farm_b, "B2")
    fb3 = _field(db, farm_b, "B3")

    _patch_priority(monkeypatch, {
        farm_a.id: [
            (fa1.id, "A1", "maiz", 90.0, "Estrés hídrico", "Riego urgente"),
            (fa2.id, "A2", "frijol", 40.0, "NDVI bajo", "Monitoreo"),
            (fa3.id, "A3", "maiz", 60.0, "Temperatura", "Revisar"),
        ],
        farm_b.id: [
            (fb1.id, "B1", "aguacate", 85.0, "Plaga", "Tratamiento"),
            (fb2.id, "B2", "maiz", 50.0, "Suelo ácido", "Encalar"),
            (fb3.id, "B3", "frijol", 20.0, "OK", "Sin acción"),
        ],
    })

    result = svc.compute_coop_agenda_semanal(coop, db)
    assert result["total_farms"] == 2
    assert result["total_fields"] == 6
    items = result["top_items"]
    assert len(items) == 5
    scores = [it["priority_score"] for it in items]
    assert scores == sorted(scores, reverse=True)
    assert scores[0] == 90.0
    assert items[0]["field_name"] == "A1"
    assert items[0]["farm_name"] == "Finca A"


def test_unknown_coop_404(client):
    """Unknown cooperative returns 404."""
    resp = client.get("/api/cooperatives/9999/agenda-semanal")
    assert resp.status_code == 404


def test_no_farms_empty(db, coop, monkeypatch):
    """Coop with no member farms → empty top_items."""
    result = svc.compute_coop_agenda_semanal(coop, db)
    assert result["total_farms"] == 0
    assert result["total_fields"] == 0
    assert result["top_items"] == []
    assert "sin fincas" in result["resumen_es"].lower()


def test_fewer_than_5(db, coop, monkeypatch):
    """Coop with fewer than 5 fields returns all of them."""
    farm = _farm(db, coop, "Finca Sola")
    f1 = _field(db, farm, "Lote 1")
    f2 = _field(db, farm, "Lote 2")
    _patch_priority(monkeypatch, {
        farm.id: [
            (f1.id, "Lote 1", "maiz", 70.0, "Temperatura", "Monitorear"),
            (f2.id, "Lote 2", "frijol", 30.0, "OK", "Sin acción"),
        ],
    })
    result = svc.compute_coop_agenda_semanal(coop, db)
    assert len(result["top_items"]) == 2
    assert result["total_fields"] == 2


def test_max_5_cap(db, coop, monkeypatch):
    """More than 5 fields across farms → returns exactly 5."""
    farms_data = {}
    for i in range(3):
        farm = _farm(db, coop, f"Finca {i}")
        fields_data = []
        for j in range(3):
            fld = _field(db, farm, f"Campo {i}-{j}")
            fields_data.append(
                (fld.id, f"Campo {i}-{j}", "maiz", float(10 + i * 10 + j * 5), "Stress", "Acción")
            )
        farms_data[farm.id] = fields_data

    _patch_priority(monkeypatch, farms_data)
    result = svc.compute_coop_agenda_semanal(coop, db)
    assert result["total_fields"] == 9
    assert len(result["top_items"]) == 5


def test_resumen_es_spanish(db, coop, monkeypatch):
    """Resumen is in Spanish and under 200 chars."""
    farm = _farm(db, coop, "Finca Sol")
    fld = _field(db, farm, "Milpa")
    _patch_priority(monkeypatch, {
        farm.id: [(fld.id, "Milpa", "maiz", 80.0, "Estrés hídrico", "Riego urgente")],
    })
    result = svc.compute_coop_agenda_semanal(coop, db)
    resumen = result["resumen_es"]
    assert len(resumen) <= 200
    assert result["coop_name"] in resumen
