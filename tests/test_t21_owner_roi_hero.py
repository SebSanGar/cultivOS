"""T2.1 — Owner net-ROI hero: net_savings, roi_multiple, payback_months on economic-impact endpoint.

RED tests — must FAIL before implementation.
GREEN after: backend computes net_savings_mxn/roi_multiple/payback_months, frontend has #econ-roi-hero.
"""
import pytest

from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord


@pytest.fixture
def farm_with_tier(client, db):
    """Farm with standard tier + fields + health scores + treatments."""
    farm = Farm(name="ROI Test Farm", municipality="Guadalajara", tier="standard")
    db.add(farm)
    db.flush()

    field = Field(farm_id=farm.id, name="Field A", hectares=20.0)
    db.add(field)
    db.flush()

    for score_val in [60, 65, 70, 75, 80]:
        db.add(HealthScore(field_id=field.id, score=score_val))

    for _ in range(5):
        db.add(TreatmentRecord(field_id=field.id, health_score_used=70, problema="test", causa_probable="test", tratamiento="Composta", urgencia="media", prevencion="rotacion", organic=True, costo_estimado_mxn=500))

    db.commit()
    return farm


@pytest.fixture
def farm_no_tier(client, db):
    """Farm with no tier set + some fields."""
    farm = Farm(name="No Tier Farm", municipality="Guadalajara", tier=None)
    db.add(farm)
    db.flush()

    field = Field(farm_id=farm.id, name="Field B", hectares=10.0)
    db.add(field)
    db.flush()

    for score_val in [55, 65, 70]:
        db.add(HealthScore(field_id=field.id, score=score_val))

    db.commit()
    return farm


@pytest.fixture
def farm_no_data(client, db):
    """New farm with tier but NO health scores (no day-one ROI)."""
    farm = Farm(name="New Farm No Data", municipality="Zapopan", tier="basic")
    db.add(farm)
    db.flush()

    field = Field(farm_id=farm.id, name="Field C", hectares=5.0)
    db.add(field)
    db.commit()
    return farm


class TestT21NetROIFields:
    """API must return net_savings_mxn, roi_multiple, payback_months."""

    def test_response_has_net_savings_field(self, client, farm_with_tier):
        r = client.get(f"/api/farms/{farm_with_tier.id}/economic-impact")
        assert r.status_code == 200
        data = r.json()
        assert "net_savings_mxn" in data

    def test_response_has_roi_multiple_field(self, client, farm_with_tier):
        r = client.get(f"/api/farms/{farm_with_tier.id}/economic-impact")
        assert r.status_code == 200
        data = r.json()
        assert "roi_multiple" in data

    def test_response_has_payback_months_field(self, client, farm_with_tier):
        r = client.get(f"/api/farms/{farm_with_tier.id}/economic-impact")
        assert r.status_code == 200
        data = r.json()
        assert "payback_months" in data


class TestT21NetROIComputation:
    """Correct computation of net ROI fields."""

    def test_net_savings_equals_total_minus_subscription(self, client, farm_with_tier):
        r = client.get(f"/api/farms/{farm_with_tier.id}/economic-impact")
        assert r.status_code == 200
        data = r.json()
        sub = data["subscription_cost_mxn"]
        total = data["total_savings_mxn"]
        if sub is not None:
            assert data["net_savings_mxn"] == total - sub

    def test_roi_multiple_is_savings_over_cost(self, client, farm_with_tier):
        r = client.get(f"/api/farms/{farm_with_tier.id}/economic-impact")
        assert r.status_code == 200
        data = r.json()
        sub = data["subscription_cost_mxn"]
        total = data["total_savings_mxn"]
        if sub and sub > 0:
            expected_roi = round(total / sub, 1)
            assert data["roi_multiple"] == expected_roi

    def test_payback_months_derived_from_roi(self, client, farm_with_tier):
        r = client.get(f"/api/farms/{farm_with_tier.id}/economic-impact")
        assert r.status_code == 200
        data = r.json()
        roi = data["roi_multiple"]
        if roi and roi > 0:
            expected_payback = round(12 / roi)
            assert data["payback_months"] == expected_payback


class TestT21NullCases:
    """No day-one ROI; no ROI without tier."""

    def test_no_roi_without_tier(self, client, farm_no_tier):
        r = client.get(f"/api/farms/{farm_no_tier.id}/economic-impact")
        assert r.status_code == 200
        data = r.json()
        assert data["roi_multiple"] is None
        assert data["net_savings_mxn"] is None
        assert data["payback_months"] is None

    def test_no_day_one_roi_for_new_farm(self, client, farm_no_data):
        """Farm with tier but no health scores must not show ROI (honesty rule 6)."""
        r = client.get(f"/api/farms/{farm_no_data.id}/economic-impact")
        assert r.status_code == 200
        data = r.json()
        assert data["roi_multiple"] is None, "No day-one ROI — no health data yet"


class TestT21FrontendHero:
    """Frontend economic-impact page must have net-ROI hero block (English-first)."""

    def test_page_has_roi_hero_element(self, client):
        r = client.get("/impacto-economico")
        assert r.status_code == 200
        assert 'id="econ-roi-hero"' in r.text

    def test_page_has_estimate_badge(self, client):
        r = client.get("/impacto-economico")
        assert r.status_code == 200
        assert "estimate-badge" in r.text

    def test_page_title_is_english(self, client):
        r = client.get("/impacto-economico")
        assert r.status_code == 200
        assert "Economic Impact" in r.text
