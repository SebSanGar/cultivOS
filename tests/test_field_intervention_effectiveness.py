"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/intervention-effectiveness (#206).

Per-field intervention effectiveness — for each TreatmentRecord with applied_at in
the window, find HealthScore at applied_at±3d (baseline) and applied_at+30d
(followup), compute delta, classify effective/neutral/counterproductive, and
return best/worst treatment by avg delta.
"""

from datetime import datetime, timedelta

from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord


def _make_farm(db, name="Rancho Intervención"):
    farm = Farm(name=name, state="Jalisco", total_hectares=10.0)
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo A", crop_type="maiz"):
    field = Field(farm_id=farm_id, name=name, crop_type=crop_type, hectares=5.0)
    db.add(field)
    db.commit()
    return field


def _add_treatment(db, field_id, tratamiento, applied_days_ago, health=60.0):
    t = TreatmentRecord(
        field_id=field_id,
        health_score_used=health,
        problema="nutrientes",
        causa_probable="Agotamiento",
        tratamiento=tratamiento,
        costo_estimado_mxn=100,
        urgencia="media",
        prevencion="Rotación",
        organic=True,
        applied_at=datetime.utcnow() - timedelta(days=applied_days_ago),
    )
    db.add(t)
    db.commit()
    return t


def _add_health_score(db, field_id, score, days_ago):
    hs = HealthScore(
        field_id=field_id,
        score=score,
        scored_at=datetime.utcnow() - timedelta(days=days_ago),
        sources=[],
        breakdown={},
    )
    db.add(hs)
    db.commit()
    return hs


def test_intervention_effectiveness_404_farm(client, db):
    r = client.get("/api/farms/9999/fields/1/intervention-effectiveness")
    assert r.status_code == 404


def test_intervention_effectiveness_404_field(client, db):
    farm = _make_farm(db)
    r = client.get(f"/api/farms/{farm.id}/fields/9999/intervention-effectiveness")
    assert r.status_code == 404


def test_intervention_effectiveness_no_treatments(client, db):
    """Field with no treatments returns zero counts and null best/worst."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    r = client.get(
        f"/api/farms/{farm.id}/fields/{field.id}/intervention-effectiveness"
    )
    assert r.status_code == 200
    data = r.json()
    assert data["field_id"] == field.id
    assert data["treatments_evaluated"] == 0
    assert data["effective_count"] == 0
    assert data["neutral_count"] == 0
    assert data["counterproductive_count"] == 0
    assert data["effectiveness_rate_pct"] == 0.0
    assert data["best_treatment"] is None
    assert data["worst_treatment"] is None
    assert "recommendation_es" in data


def test_intervention_effectiveness_no_health_data(client, db):
    """Treatment exists but no surrounding HealthScores → not evaluated."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_treatment(db, field.id, "Compostaje", applied_days_ago=40)
    r = client.get(
        f"/api/farms/{farm.id}/fields/{field.id}/intervention-effectiveness"
    )
    assert r.status_code == 200
    data = r.json()
    assert data["treatments_evaluated"] == 0
    assert data["best_treatment"] is None


def test_intervention_effectiveness_basic(client, db):
    """One treatment with baseline + followup → effective classification."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_treatment(db, field.id, "Compostaje", applied_days_ago=40)
    # baseline at applied_at (40 days ago) — within ±3d
    _add_health_score(db, field.id, score=55.0, days_ago=40)
    # followup at applied_at + 30d = 10 days ago — within +27..33
    _add_health_score(db, field.id, score=70.0, days_ago=10)

    r = client.get(
        f"/api/farms/{farm.id}/fields/{field.id}/intervention-effectiveness"
    )
    assert r.status_code == 200
    data = r.json()
    assert data["treatments_evaluated"] == 1
    assert data["effective_count"] == 1
    assert data["neutral_count"] == 0
    assert data["counterproductive_count"] == 0
    assert data["effectiveness_rate_pct"] == 100.0
    assert data["best_treatment"]["name"] == "Compostaje"
    assert data["best_treatment"]["avg_delta"] == 15.0
    assert data["worst_treatment"]["name"] == "Compostaje"


def test_intervention_effectiveness_best_worst(client, db):
    """Two treatments: Compostaje +20 (effective), Poda fallida -10 (counterproductive)."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    # Compostaje: applied 50d ago, baseline 50.0 at 50d ago, followup 70.0 at 20d ago
    _add_treatment(db, field.id, "Compostaje", applied_days_ago=50)
    _add_health_score(db, field.id, score=50.0, days_ago=50)
    _add_health_score(db, field.id, score=70.0, days_ago=20)

    # Poda fallida: applied 100d ago, baseline 60.0 at 100d ago, followup 50.0 at 70d ago
    _add_treatment(db, field.id, "Poda fallida", applied_days_ago=100)
    _add_health_score(db, field.id, score=60.0, days_ago=100)
    _add_health_score(db, field.id, score=50.0, days_ago=70)

    r = client.get(
        f"/api/farms/{farm.id}/fields/{field.id}/intervention-effectiveness?days=180"
    )
    assert r.status_code == 200
    data = r.json()
    assert data["treatments_evaluated"] == 2
    assert data["effective_count"] == 1
    assert data["counterproductive_count"] == 1
    assert data["neutral_count"] == 0
    assert data["effectiveness_rate_pct"] == 50.0
    assert data["best_treatment"]["name"] == "Compostaje"
    assert data["best_treatment"]["avg_delta"] == 20.0
    assert data["worst_treatment"]["name"] == "Poda fallida"
    assert data["worst_treatment"]["avg_delta"] == -10.0
