"""Tests for GET /api/cooperatives/{coop_id}/health-prediction

Task #195: Cooperative 30-day health prediction aggregate.
Composes compute_health_prediction per field across member farms.
"""

from datetime import datetime, timedelta

from cultivos.db.models import Cooperative, Farm, Field, HealthScore


def _coop(db, name="Coop Pred"):
    c = Cooperative(name=name, state="Jalisco")
    db.add(c)
    db.flush()
    return c


def _farm(db, coop_id=None, name="Farm"):
    f = Farm(name=name, state="Jalisco", total_hectares=10.0, cooperative_id=coop_id)
    db.add(f)
    db.flush()
    return f


def _field(db, farm_id, name="Lote"):
    fld = Field(farm_id=farm_id, name=name, hectares=5.0, crop_type="maiz")
    db.add(fld)
    db.flush()
    return fld


def _health_series(db, field_id, values, start_days_ago=60):
    """Seed N health scores spanning start_days_ago..0."""
    n = len(values)
    for idx, v in enumerate(values):
        offset = start_days_ago - int(idx * (start_days_ago / max(n - 1, 1)))
        when = datetime.utcnow() - timedelta(days=max(offset, 0))
        db.add(HealthScore(field_id=field_id, score=float(v), scored_at=when))
    db.flush()


def test_404_unknown_cooperative(client):
    resp = client.get("/api/cooperatives/9999/health-prediction")
    assert resp.status_code == 404


def test_empty_cooperative(client, db):
    c = _coop(db)
    db.commit()
    resp = client.get(f"/api/cooperatives/{c.id}/health-prediction")
    assert resp.status_code == 200
    body = resp.json()
    assert body["cooperative_id"] == c.id
    assert body["fields_count"] == 0
    assert body["fields_with_data"] == 0
    assert body["avg_current_health"] == 0.0
    assert body["avg_predicted_health_30d"] == 0.0
    assert body["projected_delta"] == 0.0
    assert body["fields_at_risk_count"] == 0
    assert body["trend_distribution"] == {"improving": 0, "stable": 0, "declining": 0}
    assert body["top_declining_farm"] is None
    assert body["farms"] == []


def test_single_farm_single_field_improving(client, db):
    c = _coop(db)
    f = _farm(db, coop_id=c.id, name="Finca Uno")
    fld = _field(db, f.id)
    # Improving series: 40 → 90 over 60 days, strongly positive slope
    _health_series(db, fld.id, [40, 50, 60, 70, 80, 85, 88, 90, 92, 95])
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/health-prediction")
    body = resp.json()
    assert body["fields_count"] == 1
    assert body["fields_with_data"] == 1
    assert body["avg_current_health"] > 60  # mean of seeded values
    assert body["avg_predicted_health_30d"] > body["avg_current_health"]  # improving
    assert body["projected_delta"] > 0
    assert body["fields_at_risk_count"] == 0
    assert body["trend_distribution"]["improving"] >= 1
    assert len(body["farms"]) == 1
    farm_entry = body["farms"][0]
    assert farm_entry["farm_id"] == f.id
    assert farm_entry["farm_name"] == "Finca Uno"
    assert farm_entry["fields_with_data"] == 1
    assert farm_entry["fields_at_risk"] == 0
    assert farm_entry["trend"] == "improving"


def test_multi_farm_avg_computation(client, db):
    c = _coop(db)
    f1 = _farm(db, coop_id=c.id, name="F1")
    f2 = _farm(db, coop_id=c.id, name="F2")
    fld1 = _field(db, f1.id)
    fld2 = _field(db, f2.id)
    # Farm 1: stable high (80 all)
    _health_series(db, fld1.id, [80] * 10)
    # Farm 2: stable low (30 all)
    _health_series(db, fld2.id, [30] * 10)
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/health-prediction")
    body = resp.json()
    assert body["fields_count"] == 2
    assert body["fields_with_data"] == 2
    # Avg of 80 and 30 = 55
    assert abs(body["avg_current_health"] - 55.0) < 1.0
    assert abs(body["avg_predicted_health_30d"] - 55.0) < 2.0  # stable
    assert len(body["farms"]) == 2


def test_at_risk_count(client, db):
    """Field with predicted < 40 → fields_at_risk_count >= 1."""
    c = _coop(db)
    f = _farm(db, coop_id=c.id, name="Finca Riesgo")
    fld_risk = _field(db, f.id, name="Lote Riesgo")
    fld_safe = _field(db, f.id, name="Lote Seguro")
    # Declining series ending low → predicted below 40
    _health_series(db, fld_risk.id, [60, 55, 50, 45, 40, 35, 30, 25, 22, 20])
    _health_series(db, fld_safe.id, [80] * 10)
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/health-prediction")
    body = resp.json()
    assert body["fields_at_risk_count"] >= 1
    farm_entry = body["farms"][0]
    assert farm_entry["fields_at_risk"] >= 1


def test_trend_distribution(client, db):
    c = _coop(db)
    f = _farm(db, coop_id=c.id)
    fld_up = _field(db, f.id, name="Up")
    fld_flat = _field(db, f.id, name="Flat")
    fld_down = _field(db, f.id, name="Down")
    _health_series(db, fld_up.id, [40, 50, 60, 70, 75, 80, 85, 88, 92, 95])
    _health_series(db, fld_flat.id, [70] * 10)
    _health_series(db, fld_down.id, [90, 85, 80, 75, 70, 65, 60, 55, 50, 45])
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/health-prediction")
    body = resp.json()
    dist = body["trend_distribution"]
    assert dist["improving"] >= 1
    assert dist["stable"] >= 1
    assert dist["declining"] >= 1


def test_top_declining_farm(client, db):
    c = _coop(db)
    f_stable = _farm(db, coop_id=c.id, name="Estable")
    f_drop = _farm(db, coop_id=c.id, name="Cayendo")
    fld_stable = _field(db, f_stable.id)
    fld_drop = _field(db, f_drop.id)
    _health_series(db, fld_stable.id, [80] * 10)
    _health_series(db, fld_drop.id, [90, 85, 80, 75, 70, 65, 60, 55, 50, 45])
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/health-prediction")
    body = resp.json()
    top = body["top_declining_farm"]
    assert top is not None
    assert top["farm_name"] == "Cayendo"
    assert top["delta"] < 0


def test_unaffiliated_farm_excluded(client, db):
    c = _coop(db)
    member = _farm(db, coop_id=c.id, name="Member")
    outsider = _farm(db, coop_id=None, name="Outsider")
    mf = _field(db, member.id)
    of = _field(db, outsider.id)
    _health_series(db, mf.id, [80] * 10)
    _health_series(db, of.id, [10] * 10)
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/health-prediction")
    body = resp.json()
    assert body["fields_count"] == 1
    assert len(body["farms"]) == 1
    assert body["farms"][0]["farm_name"] == "Member"
    assert abs(body["avg_current_health"] - 80.0) < 1.0


def test_field_without_health_data_graceful(client, db):
    c = _coop(db)
    f = _farm(db, coop_id=c.id)
    _field(db, f.id)  # no health scores
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/health-prediction")
    assert resp.status_code == 200
    body = resp.json()
    assert body["fields_count"] == 1
    assert body["fields_with_data"] == 0
    assert body["avg_current_health"] == 0.0
    assert body["avg_predicted_health_30d"] == 0.0
    assert len(body["farms"]) == 1
    assert body["farms"][0]["fields_with_data"] == 0
