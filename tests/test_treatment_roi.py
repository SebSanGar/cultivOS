"""Tests for GET /api/farms/{farm_id}/treatment-roi endpoint (#203).

Groups TreatmentRecords by tratamiento, links to 30-day HealthScore followup,
computes cost_per_health_point (total_cost / total_positive_delta).
Returns best/worst ROI treatment types with Spanish recommendations.
"""

from datetime import datetime, timedelta

from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord


def _make_farm(db, name="Rancho ROI"):
    farm = Farm(name=name, state="Jalisco", total_hectares=10.0)
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo ROI", crop_type="maiz"):
    field = Field(farm_id=farm_id, name=name, crop_type=crop_type, hectares=5.0)
    db.add(field)
    db.commit()
    return field


def _add_treatment(
    db,
    field_id,
    tratamiento="Compostaje orgánico",
    problema="nutrientes",
    days_ago=20,
    health=60.0,
    costo=200,
):
    t = TreatmentRecord(
        field_id=field_id,
        health_score_used=health,
        problema=problema,
        causa_probable="Agotamiento detectado",
        tratamiento=tratamiento,
        costo_estimado_mxn=costo,
        urgencia="media",
        prevencion="Rotación anual",
        organic=True,
        created_at=datetime.utcnow() - timedelta(days=days_ago),
    )
    db.add(t)
    db.commit()
    return t


def _add_health_score(db, field_id, score, days_ago=0):
    hs = HealthScore(
        field_id=field_id,
        score=score,
        scored_at=datetime.utcnow() - timedelta(days=days_ago),
    )
    db.add(hs)
    db.commit()
    return hs


def test_treatment_roi_404(client, db):
    r = client.get("/api/farms/9999/treatment-roi")
    assert r.status_code == 404


def test_treatment_roi_empty(client, db):
    """Farm with no treatments returns empty treatments + null best/worst."""
    farm = _make_farm(db)
    _make_field(db, farm.id)
    r = client.get(f"/api/farms/{farm.id}/treatment-roi")
    assert r.status_code == 200
    data = r.json()
    assert data["farm_id"] == farm.id
    assert data["period_days"] == 90
    assert data["treatments"] == []
    assert data["best_roi_treatment"] is None
    assert data["worst_roi_treatment"] is None


def test_treatment_roi_basic(client, db):
    """One treatment: 200 MXN cost, +20 health delta → cost_per_health_point = 10.0."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_treatment(
        db, field.id, tratamiento="Compostaje", days_ago=20, health=60.0, costo=200
    )
    _add_health_score(db, field.id, score=80.0, days_ago=10)

    r = client.get(f"/api/farms/{farm.id}/treatment-roi")
    assert r.status_code == 200
    data = r.json()
    assert len(data["treatments"]) == 1
    item = data["treatments"][0]
    assert item["treatment_type"] == "Compostaje"
    assert item["count"] == 1
    assert item["total_cost_mxn"] == 200
    assert item["avg_health_delta"] == 20.0
    assert item["cost_per_health_point"] == 10.0
    assert "recommendation_es" in item
    assert len(item["recommendation_es"]) > 5


def test_treatment_roi_no_cost_data(client, db):
    """Zero cost treatment → cost_per_health_point is None, Spanish says sin datos."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_treatment(
        db, field.id, tratamiento="Té de plátano", days_ago=15, health=55.0, costo=0
    )
    _add_health_score(db, field.id, score=70.0, days_ago=5)

    r = client.get(f"/api/farms/{farm.id}/treatment-roi")
    assert r.status_code == 200
    item = r.json()["treatments"][0]
    assert item["total_cost_mxn"] == 0
    assert item["cost_per_health_point"] is None
    assert "costo" in item["recommendation_es"].lower()


def test_treatment_roi_negative_delta(client, db):
    """Negative health delta → cost_per_health_point is None, Spanish says sin mejora."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_treatment(
        db, field.id, tratamiento="Aplicación fallida", days_ago=15, health=70.0, costo=300
    )
    _add_health_score(db, field.id, score=55.0, days_ago=5)  # worsened

    r = client.get(f"/api/farms/{farm.id}/treatment-roi")
    assert r.status_code == 200
    item = r.json()["treatments"][0]
    assert item["avg_health_delta"] < 0
    assert item["cost_per_health_point"] is None
    assert "mejora" in item["recommendation_es"].lower()


def test_treatment_roi_best_worst(client, db):
    """Two treatment types: lower cost_per_health_point wins best, higher wins worst."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # Compostaje: 100 MXN, +20 delta → 5.0 per point (BEST)
    _add_treatment(
        db, field.id, tratamiento="Compostaje", days_ago=25, health=50.0, costo=100
    )
    _add_health_score(db, field.id, score=70.0, days_ago=15)
    # Jabón potásico: 500 MXN, +10 delta → 50.0 per point (WORST)
    _add_treatment(
        db, field.id, tratamiento="Jabón potásico", days_ago=40, health=60.0, costo=500
    )
    _add_health_score(db, field.id, score=70.0, days_ago=30)

    r = client.get(f"/api/farms/{farm.id}/treatment-roi")
    assert r.status_code == 200
    data = r.json()
    assert len(data["treatments"]) == 2
    assert data["best_roi_treatment"] == "Compostaje"
    assert data["worst_roi_treatment"] == "Jabón potásico"
