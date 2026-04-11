"""Tests for POST /api/intel/fertilizer-for-stress

Given a farm + field, reads stress composite and returns top 3 organic fertilizer
recommendations. Low/no stress returns a "no urgency" message instead.
"""

from datetime import datetime, timedelta

from cultivos.db.models import Farm, Field, Fertilizer, SoilAnalysis, ThermalResult


# ── Helpers ────────────────────────────────────────────────────────────────────

def _farm(db):
    f = Farm(name="Finca Test", municipality="Guadalajara", state="Jalisco", total_hectares=10.0)
    db.add(f)
    db.commit()
    return f


def _field(db, farm_id, crop_type="maiz"):
    f = Field(farm_id=farm_id, name="Lote A", crop_type=crop_type, hectares=5.0)
    db.add(f)
    db.commit()
    return f


def _fertilizer(db, name, suitable_crops=None, cost=2000):
    fert = Fertilizer(
        name=name,
        description_es=f"Descripcion de {name}",
        application_method=f"Aplicar {name} segun instrucciones.",
        cost_per_ha_mxn=cost,
        nutrient_profile="N-P-K balanceado",
        suitable_crops=suitable_crops if suitable_crops is not None else [],
    )
    db.add(fert)
    db.commit()
    return fert


def _seed_high_stress(db, field_id):
    """Seed SoilAnalysis + ThermalResult to trigger severe composite stress."""
    # Low soil moisture → water stress
    db.add(SoilAnalysis(
        field_id=field_id,
        moisture_pct=10.0,
        ph=6.5,
        organic_matter_pct=2.0,
        nitrogen_ppm=20.0,
        sampled_at=datetime.utcnow() - timedelta(hours=1),
    ))
    # High thermal stress
    db.add(ThermalResult(
        field_id=field_id,
        stress_pct=80.0,
        temp_mean=38.0, temp_std=3.0, temp_min=30.0, temp_max=42.0,
        pixels_total=1000,
        analyzed_at=datetime.utcnow() - timedelta(hours=1),
    ))
    db.commit()


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_404_unknown_farm(client, db):
    r = client.post("/api/intel/fertilizer-for-stress", json={"farm_id": 99999, "field_id": 1})
    assert r.status_code == 404


def test_404_unknown_field(client, db):
    farm = _farm(db)
    r = client.post("/api/intel/fertilizer-for-stress", json={"farm_id": farm.id, "field_id": 99999})
    assert r.status_code == 404


def test_field_not_on_farm(client, db):
    """field_id from a different farm returns 404."""
    farm1 = _farm(db)
    farm2 = _farm(db)
    field2 = _field(db, farm2.id)
    r = client.post("/api/intel/fertilizer-for-stress", json={"farm_id": farm1.id, "field_id": field2.id})
    assert r.status_code == 404


def test_low_stress_returns_message(client, db):
    """Field with no stress data (all sensors absent → defaults to low) returns message_es."""
    farm = _farm(db)
    field = _field(db, farm.id)

    r = client.post("/api/intel/fertilizer-for-stress", json={"farm_id": farm.id, "field_id": field.id})
    assert r.status_code == 200
    data = r.json()
    assert "message_es" in data
    assert "recommendations" not in data


def test_response_schema_when_stressed(client, db):
    """Stressed field returns field_id, crop_type, stress_level, recommendations list."""
    farm = _farm(db)
    field = _field(db, farm.id, crop_type="maiz")
    _seed_high_stress(db, field.id)
    _fertilizer(db, "Compost X", suitable_crops=[], cost=1000)

    r = client.post("/api/intel/fertilizer-for-stress", json={"farm_id": farm.id, "field_id": field.id})
    assert r.status_code == 200
    data = r.json()
    assert data["field_id"] == field.id
    assert data["crop_type"] == "maiz"
    assert "stress_level" in data
    assert "recommendations" in data


def test_at_most_3_recommendations(client, db):
    """Never returns more than 3 recommendations even with many fertilizers seeded."""
    farm = _farm(db)
    field = _field(db, farm.id, crop_type="maiz")
    _seed_high_stress(db, field.id)
    for i in range(6):
        _fertilizer(db, f"Fertilizante {i}", suitable_crops=[], cost=1000 + i * 100)

    r = client.post("/api/intel/fertilizer-for-stress", json={"farm_id": farm.id, "field_id": field.id})
    assert r.status_code == 200
    assert len(r.json()["recommendations"]) <= 3


def test_recommendation_item_keys(client, db):
    """Each recommendation has fertilizer_name, why_now_es, application_es."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _seed_high_stress(db, field.id)
    _fertilizer(db, "Bocashi Test", suitable_crops=[], cost=2000)

    r = client.post("/api/intel/fertilizer-for-stress", json={"farm_id": farm.id, "field_id": field.id})
    assert r.status_code == 200
    recs = r.json()["recommendations"]
    if recs:
        item = recs[0]
        assert "fertilizer_name" in item
        assert "why_now_es" in item
        assert "application_es" in item


def test_sorted_cheapest_first(client, db):
    """Recommendations sorted by cost ascending (cheapest organic option first)."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _seed_high_stress(db, field.id)
    _fertilizer(db, "Caro", suitable_crops=[], cost=5000)
    _fertilizer(db, "Barato", suitable_crops=[], cost=1000)
    _fertilizer(db, "Medio", suitable_crops=[], cost=3000)

    r = client.post("/api/intel/fertilizer-for-stress", json={"farm_id": farm.id, "field_id": field.id})
    recs = r.json()["recommendations"]
    assert recs[0]["fertilizer_name"] == "Barato"


def test_crop_specific_fertilizers_included(client, db):
    """Fertilizers matching field crop_type and universal ones both included."""
    farm = _farm(db)
    field = _field(db, farm.id, crop_type="agave")
    _seed_high_stress(db, field.id)
    _fertilizer(db, "Universal", suitable_crops=[], cost=1000)
    _fertilizer(db, "AgaveSpecific", suitable_crops=["agave"], cost=2000)

    r = client.post("/api/intel/fertilizer-for-stress", json={"farm_id": farm.id, "field_id": field.id})
    recs = r.json()["recommendations"]
    names = [rec["fertilizer_name"] for rec in recs]
    assert "AgaveSpecific" in names
    assert "Universal" in names
