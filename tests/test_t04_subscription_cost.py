"""T0.4 — economics endpoint includes subscription_cost_mxn from Farm.tier.

Farm.tier drives hectares × tier_rate lookup. Missing tier → cost None.

Tests FAIL before T0.4 implementation, PASS after.
"""

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def farm_with_tier(db):
    """Farm with tier="standard", 10 ha, one field with health score."""
    from cultivos.db.models import Farm, Field, HealthScore

    farm = Farm(name="T04 Tiered Farm", municipality="Guadalajara", total_hectares=10.0, tier="standard")
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Norte", hectares=10.0, crop_type="maize")
    db.add(field)
    db.flush()
    db.add(HealthScore(field_id=field.id, score=70))
    db.commit()
    return farm.id


@pytest.fixture()
def farm_no_tier(db):
    """Farm with no tier set."""
    from cultivos.db.models import Farm, Field, HealthScore

    farm = Farm(name="T04 No-Tier Farm", municipality="Guadalajara", total_hectares=5.0)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Sur", hectares=5.0, crop_type="maize")
    db.add(field)
    db.flush()
    db.add(HealthScore(field_id=field.id, score=65))
    db.commit()
    return farm.id


# ---------------------------------------------------------------------------
# T1 — Farm.tier column exists on ORM model
# ---------------------------------------------------------------------------


class TestFarmTierColumn:
    def test_farm_has_tier_attribute(self, db):
        from cultivos.db.models import Farm
        assert hasattr(Farm, "tier"), "T0.4: Farm ORM model must have a 'tier' column"

    def test_tier_column_is_nullable(self, db):
        from cultivos.db.models import Farm
        col = Farm.__table__.columns["tier"]
        assert col.nullable, "T0.4: Farm.tier must be nullable (not all farms have a tier)"

    def test_farm_tier_can_be_set(self, db):
        from cultivos.db.models import Farm
        farm = Farm(name="T04 Tier Test", total_hectares=5.0, tier="basic")
        db.add(farm)
        db.commit()
        loaded = db.query(Farm).filter(Farm.name == "T04 Tier Test").first()
        assert loaded.tier == "basic"


# ---------------------------------------------------------------------------
# T2 — EconomicImpactOut has subscription_cost_mxn field
# ---------------------------------------------------------------------------


class TestSubscriptionCostField:
    def test_response_has_subscription_cost_field(self, client, farm_with_tier):
        r = client.get(f"/api/farms/{farm_with_tier}/economic-impact")
        assert r.status_code == 200
        body = r.json()
        assert "subscription_cost_mxn" in body, (
            "T0.4: EconomicImpactOut must include subscription_cost_mxn"
        )

    def test_tiered_farm_cost_is_positive(self, client, farm_with_tier):
        r = client.get(f"/api/farms/{farm_with_tier}/economic-impact")
        body = r.json()
        cost = body.get("subscription_cost_mxn")
        assert cost is not None, "T0.4: tiered farm must have non-None subscription_cost_mxn"
        assert cost > 0, f"T0.4: tiered farm cost should be > 0, got {cost}"

    def test_tiered_farm_cost_equals_hectares_times_rate(self, client, farm_with_tier):
        from cultivos.services.intelligence.assumptions import get_value
        r = client.get(f"/api/farms/{farm_with_tier}/economic-impact")
        body = r.json()
        # 10 ha × standard rate
        standard_rate = get_value("tier_rate_standard_mxn_ha")
        expected = round(10.0 * standard_rate)
        assert body["subscription_cost_mxn"] == expected, (
            f"T0.4: cost = 10ha × {standard_rate} = {expected}, got {body['subscription_cost_mxn']}"
        )


# ---------------------------------------------------------------------------
# T3 — Missing tier returns None + note
# ---------------------------------------------------------------------------


class TestMissingTier:
    def test_no_tier_cost_is_none(self, client, farm_no_tier):
        r = client.get(f"/api/farms/{farm_no_tier}/economic-impact")
        assert r.status_code == 200
        body = r.json()
        assert body.get("subscription_cost_mxn") is None, (
            f"T0.4: no-tier farm must have subscription_cost_mxn = None, got {body.get('subscription_cost_mxn')!r}"
        )

    def test_no_tier_has_nota_message(self, client, farm_no_tier):
        r = client.get(f"/api/farms/{farm_no_tier}/economic-impact")
        body = r.json()
        nota = body.get("nota", "")
        assert "tarifa" in nota.lower() or "tier" in nota.lower(), (
            f"T0.4: nota for no-tier farm must mention tarifa/tier. Got: {nota!r}"
        )


# ---------------------------------------------------------------------------
# T4 — assumptions.py has tier rate entries
# ---------------------------------------------------------------------------


class TestAssumptionsTierRates:
    def test_assumptions_has_standard_rate(self):
        from cultivos.services.intelligence.assumptions import get_value
        rate = get_value("tier_rate_standard_mxn_ha")
        assert rate > 0, "T0.4: tier_rate_standard_mxn_ha must be positive"

    def test_assumptions_has_basic_rate(self):
        from cultivos.services.intelligence.assumptions import get_value
        rate = get_value("tier_rate_basic_mxn_ha")
        assert rate > 0

    def test_basic_rate_lt_standard(self):
        from cultivos.services.intelligence.assumptions import get_value
        assert get_value("tier_rate_basic_mxn_ha") < get_value("tier_rate_standard_mxn_ha")
