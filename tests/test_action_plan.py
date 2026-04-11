"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/action-plan"""

from datetime import date, datetime, timedelta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _add_farm(db):
    from cultivos.db.models import Farm
    farm = Farm(name="Rancho Test", owner_name="Agricultor", state="jalisco",
                total_hectares=10.0)
    db.add(farm)
    db.commit()
    return farm


def _add_field(db, farm_id, crop_type="maiz"):
    from cultivos.db.models import Field
    field = Field(farm_id=farm_id, name="Parcela 1", crop_type=crop_type,
                  hectares=2.0, planted_at=date.today() - timedelta(days=30))
    db.add(field)
    db.commit()
    return field


def _add_ancestral(db, name, month, crop_type="maiz"):
    from cultivos.db.models import AncestralMethod
    m = AncestralMethod(
        name=name,
        description_es="Practica ancestral para la temporada",
        region="jalisco",
        practice_type="soil_management",
        crops=[crop_type],
        benefits_es="Mejora el suelo",
        problems=[],
        applicable_months=[month],
        ecological_benefit=8,
    )
    db.add(m)
    db.commit()
    return m


def _add_thermal(db, field_id, stress_pct):
    from cultivos.db.models import ThermalResult
    r = ThermalResult(
        field_id=field_id,
        stress_pct=stress_pct,
        temp_mean=38.0,
        temp_std=2.0,
        temp_min=34.0,
        temp_max=42.0,
        pixels_total=1000,
        analyzed_at=datetime.utcnow(),
    )
    db.add(r)
    db.commit()
    return r


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_404_unknown_farm(client):
    resp = client.get("/api/farms/9999/fields/1/action-plan")
    assert resp.status_code == 404


def test_404_unknown_field(client, db):
    farm = _add_farm(db)
    resp = client.get(f"/api/farms/{farm.id}/fields/9999/action-plan")
    assert resp.status_code == 404


def test_response_schema_keys(client, db):
    farm = _add_farm(db)
    field = _add_field(db, farm.id)
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/action-plan")
    assert resp.status_code == 200
    data = resp.json()
    assert "field_id" in data
    assert "crop_type" in data
    assert "period_days" in data
    assert "actions" in data
    assert isinstance(data["actions"], list)


def test_action_item_schema_keys(client, db):
    farm = _add_farm(db)
    field = _add_field(db, farm.id)
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/action-plan")
    assert resp.status_code == 200
    actions = resp.json()["actions"]
    # compute_upcoming_treatments always returns generic schedule, so actions is non-empty
    if actions:
        item = actions[0]
        assert "priority" in item
        assert "category" in item
        assert "action_es" in item
        assert "source_es" in item


def test_no_sensor_data_returns_gracefully(client, db):
    """No stress/TEK data → only treatment actions, no crash."""
    farm = _add_farm(db)
    field = _add_field(db, farm.id)
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/action-plan")
    assert resp.status_code == 200
    data = resp.json()
    assert "actions" in data
    # treatment actions always present (generic schedule)
    categories = {a["category"] for a in data["actions"]}
    assert "treatment" in categories


def test_high_thermal_stress_generates_stress_action(client, db):
    """High thermal stress → stress action with category=stress."""
    farm = _add_farm(db)
    field = _add_field(db, farm.id)
    _add_thermal(db, field.id, stress_pct=80.0)
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/action-plan")
    assert resp.status_code == 200
    actions = resp.json()["actions"]
    categories = {a["category"] for a in actions}
    assert "stress" in categories


def test_tek_practice_for_month_generates_tek_action(client, db):
    """TEK practice applicable this month → action with category=tek."""
    farm = _add_farm(db)
    field = _add_field(db, farm.id, crop_type="maiz")
    current_month = date.today().month
    _add_ancestral(db, "Milpa Mensual", month=current_month, crop_type="maiz")
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/action-plan")
    assert resp.status_code == 200
    actions = resp.json()["actions"]
    categories = {a["category"] for a in actions}
    assert "tek" in categories


def test_combined_data_returns_multiple_categories(client, db):
    """High thermal + TEK practice → both stress and tek categories present."""
    farm = _add_farm(db)
    field = _add_field(db, farm.id, crop_type="maiz")
    current_month = date.today().month
    _add_thermal(db, field.id, stress_pct=75.0)
    _add_ancestral(db, "Milpa Mensual", month=current_month, crop_type="maiz")
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/action-plan")
    assert resp.status_code == 200
    actions = resp.json()["actions"]
    categories = {a["category"] for a in actions}
    assert len(categories) >= 2


def test_priority_values_are_valid(client, db):
    """All actions have priority in {high, medium, low}."""
    farm = _add_farm(db)
    field = _add_field(db, farm.id)
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/action-plan")
    assert resp.status_code == 200
    for action in resp.json()["actions"]:
        assert action["priority"] in {"high", "medium", "low"}


def test_category_values_are_valid(client, db):
    """All actions have category in {stress, treatment, tek}."""
    farm = _add_farm(db)
    field = _add_field(db, farm.id)
    current_month = date.today().month
    _add_ancestral(db, "Practica Test", month=current_month)
    _add_thermal(db, field.id, stress_pct=70.0)
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/action-plan")
    assert resp.status_code == 200
    for action in resp.json()["actions"]:
        assert action["category"] in {"stress", "treatment", "tek"}


def test_period_days_default_is_7(client, db):
    farm = _add_farm(db)
    field = _add_field(db, farm.id)
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/action-plan")
    assert resp.status_code == 200
    assert resp.json()["period_days"] == 7


def test_field_id_in_response(client, db):
    farm = _add_farm(db)
    field = _add_field(db, farm.id)
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/action-plan")
    assert resp.status_code == 200
    assert resp.json()["field_id"] == field.id
