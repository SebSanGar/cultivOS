"""Tests for cooperative data completeness aggregate.

GET /api/cooperatives/{coop_id}/data-completeness
Composes compute_data_completeness per member farm.
"""

from datetime import datetime

import pytest

from cultivos.db.models import (
    Cooperative,
    Farm,
    Field,
    NDVIResult,
    SoilAnalysis,
    ThermalResult,
    TreatmentRecord,
    WeatherRecord,
)


@pytest.fixture
def coop(db):
    c = Cooperative(name="Cooperativa Completitud", state="Jalisco")
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _farm(db, coop, name="Rancho"):
    f = Farm(name=name, owner_name="Test", state="Jalisco",
             total_hectares=50.0, cooperative_id=coop.id)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def _field(db, farm, name="Parcela"):
    fld = Field(farm_id=farm.id, name=name, crop_type="maiz", hectares=5.0)
    db.add(fld)
    db.commit()
    db.refresh(fld)
    return fld


def _attach(db, farm, field, types: set):
    """Attach listed data types: subset of {soil, ndvi, thermal, treatments, weather}."""
    if "soil" in types:
        db.add(SoilAnalysis(field_id=field.id, ph=6.5, sampled_at=datetime.utcnow()))
    if "ndvi" in types:
        db.add(NDVIResult(
            field_id=field.id, ndvi_mean=0.7, ndvi_std=0.1, ndvi_min=0.3,
            ndvi_max=0.9, pixels_total=1000, stress_pct=10, zones=[],
            analyzed_at=datetime.utcnow(),
        ))
    if "thermal" in types:
        db.add(ThermalResult(
            field_id=field.id, temp_mean=28, temp_std=2, temp_min=22,
            temp_max=35, pixels_total=500, stress_pct=5,
            analyzed_at=datetime.utcnow(),
        ))
    if "treatments" in types:
        db.add(TreatmentRecord(
            field_id=field.id, health_score_used=75.0, problema="plaga",
            causa_probable="humedad", tratamiento="neem", urgencia="baja",
            prevencion="rotacion", organic=True,
        ))
    if "weather" in types:
        db.add(WeatherRecord(
            farm_id=farm.id, temp_c=25, humidity_pct=60, wind_kmh=10,
            rainfall_mm=0, description="clear",
        ))
    db.commit()


def test_coop_completeness_basic(client, db, coop):
    """Two farms: one with all 5 (100), one with 3/5 (60). Avg = 80."""
    f1 = _farm(db, coop, name="Completo")
    f2 = _farm(db, coop, name="Parcial")
    fld1 = _field(db, f1, name="A")
    fld2 = _field(db, f2, name="B")
    _attach(db, f1, fld1, {"soil", "ndvi", "thermal", "treatments", "weather"})
    _attach(db, f2, fld2, {"soil", "ndvi", "thermal"})

    resp = client.get(f"/api/cooperatives/{coop.id}/data-completeness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cooperative_id"] == coop.id
    assert data["total_farms"] == 2
    assert data["overall_completeness_pct"] == pytest.approx(80.0, abs=0.1)
    assert data["worst_farm"] is not None
    assert data["worst_farm"]["farm_name"] == "Parcial"
    assert data["worst_farm"]["farm_score"] == pytest.approx(60.0, abs=0.1)


def test_coop_completeness_all_grades(client, db, coop):
    """Four farms at each grade: A (100), B (60), C (40), D (20)."""
    fa = _farm(db, coop, name="A_farm")
    _attach(db, fa, _field(db, fa), {"soil", "ndvi", "thermal", "treatments", "weather"})
    fb = _farm(db, coop, name="B_farm")
    _attach(db, fb, _field(db, fb), {"soil", "ndvi", "thermal"})
    fc = _farm(db, coop, name="C_farm")
    _attach(db, fc, _field(db, fc), {"soil", "ndvi"})
    fd = _farm(db, coop, name="D_farm")
    _attach(db, fd, _field(db, fd), {"soil"})

    resp = client.get(f"/api/cooperatives/{coop.id}/data-completeness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_farms"] == 4
    assert data["farms_by_grade"] == {"A": 1, "B": 1, "C": 1, "D": 1}
    # (100 + 60 + 40 + 20) / 4 = 55.0
    assert data["overall_completeness_pct"] == pytest.approx(55.0, abs=0.1)


def test_coop_completeness_worst_farm(client, db, coop):
    """worst_farm picks the farm with the lowest farm_score."""
    f_good = _farm(db, coop, name="Bueno")
    f_bad = _farm(db, coop, name="Malo")
    f_mid = _farm(db, coop, name="Medio")
    _attach(db, f_good, _field(db, f_good),
            {"soil", "ndvi", "thermal", "treatments", "weather"})
    _attach(db, f_bad, _field(db, f_bad), {"soil"})  # 20
    _attach(db, f_mid, _field(db, f_mid), {"soil", "ndvi", "thermal"})  # 60

    resp = client.get(f"/api/cooperatives/{coop.id}/data-completeness")
    data = resp.json()
    assert data["worst_farm"]["farm_name"] == "Malo"
    assert data["worst_farm"]["farm_score"] == pytest.approx(20.0, abs=0.1)


def test_coop_completeness_empty(client, db, coop):
    """Cooperative with no member farms → zeros, worst_farm=null."""
    resp = client.get(f"/api/cooperatives/{coop.id}/data-completeness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cooperative_id"] == coop.id
    assert data["total_farms"] == 0
    assert data["overall_completeness_pct"] == 0.0
    assert data["worst_farm"] is None
    assert data["farms_by_grade"] == {"A": 0, "B": 0, "C": 0, "D": 0}


def test_coop_completeness_404(client):
    """Unknown cooperative returns 404."""
    resp = client.get("/api/cooperatives/99999/data-completeness")
    assert resp.status_code == 404
