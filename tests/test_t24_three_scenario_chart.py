"""T2.4 — Three-scenario ghosted Sin/Con cultivOS baseline in the bar chart.

RED tests — must FAIL before implementation.
GREEN after:
  - EconomicImpactOut gains water_potential_mxn, fertilizer_potential_mxn, yield_potential_mxn
  - API computes potential = round(CATEGORY_PER_HA × hectares) (100%-efficiency ceiling)
  - potential fields are None when no fields (hectares == 0)
  - potential values are >= corresponding savings values (ceiling >= current)
  - Frontend: updateChart() renders 3 datasets in #econ-chart
  - Frontend HTML: chart section title updated to reference scenario comparison
"""
import re

import pytest

from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def farm_20ha(client, db):
    """Farm with 20ha field + health scores + treatments."""
    farm = Farm(name="T24 Farm 20ha", municipality="Zapopan", tier="standard")
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="North Field", hectares=20.0)
    db.add(field)
    db.flush()
    for score_val in [70, 75, 80]:
        db.add(HealthScore(field_id=field.id, score=score_val))
    for _ in range(4):
        db.add(TreatmentRecord(
            field_id=field.id, health_score_used=75, problema="test",
            causa_probable="test", tratamiento="Composta", urgencia="media",
            prevencion="rotacion", organic=True, costo_estimado_mxn=500,
        ))
    db.commit()
    return farm


@pytest.fixture
def farm_no_fields(client, db):
    """Farm with no fields."""
    farm = Farm(name="T24 Empty Farm", municipality="Guadalajara")
    db.add(farm)
    db.commit()
    return farm


# ---------------------------------------------------------------------------
# Backend: new potential fields exist in model response
# ---------------------------------------------------------------------------

def test_potential_fields_present_in_response(client, farm_20ha):
    resp = client.get(f"/api/farms/{farm_20ha.id}/economic-impact")
    assert resp.status_code == 200
    data = resp.json()
    assert "water_potential_mxn" in data, "Missing water_potential_mxn"
    assert "fertilizer_potential_mxn" in data, "Missing fertilizer_potential_mxn"
    assert "yield_potential_mxn" in data, "Missing yield_potential_mxn"


def test_potential_fields_are_integers(client, farm_20ha):
    resp = client.get(f"/api/farms/{farm_20ha.id}/economic-impact")
    data = resp.json()
    assert isinstance(data["water_potential_mxn"], int), "water_potential_mxn must be int"
    assert isinstance(data["fertilizer_potential_mxn"], int), "fertilizer_potential_mxn must be int"
    assert isinstance(data["yield_potential_mxn"], int), "yield_potential_mxn must be int"


def test_potential_fields_positive_for_farm_with_fields(client, farm_20ha):
    resp = client.get(f"/api/farms/{farm_20ha.id}/economic-impact")
    data = resp.json()
    assert data["water_potential_mxn"] > 0
    assert data["fertilizer_potential_mxn"] > 0
    assert data["yield_potential_mxn"] > 0


def test_potential_equals_per_ha_rate_times_hectares(client, farm_20ha):
    """water_potential = water_savings_per_ha (8000) × 20ha = 160,000."""
    resp = client.get(f"/api/farms/{farm_20ha.id}/economic-impact")
    data = resp.json()
    # From assumptions.py: water_savings_per_ha=8000, fertilizer_savings_per_ha=5000, yield_baseline_per_ha=7700
    assert data["water_potential_mxn"] == 160_000, f"Expected 160000, got {data['water_potential_mxn']}"
    assert data["fertilizer_potential_mxn"] == 100_000, f"Expected 100000, got {data['fertilizer_potential_mxn']}"
    assert data["yield_potential_mxn"] == 154_000, f"Expected 154000, got {data['yield_potential_mxn']}"


def test_potential_gte_savings(client, farm_20ha):
    """Ceiling must always be >= current estimate (savings ≤ potential)."""
    resp = client.get(f"/api/farms/{farm_20ha.id}/economic-impact")
    data = resp.json()
    assert data["water_potential_mxn"] >= data["water_savings_mxn"]
    assert data["fertilizer_potential_mxn"] >= data["fertilizer_savings_mxn"]
    assert data["yield_potential_mxn"] >= data["yield_improvement_mxn"]


def test_potential_none_when_no_fields(client, farm_no_fields):
    """No fields → no hectares → potential fields are None."""
    resp = client.get(f"/api/farms/{farm_no_fields.id}/economic-impact")
    assert resp.status_code == 200
    data = resp.json()
    assert data["water_potential_mxn"] is None
    assert data["fertilizer_potential_mxn"] is None
    assert data["yield_potential_mxn"] is None


def test_potential_farm_not_found(client):
    resp = client.get("/api/farms/99999/economic-impact")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Backend: potential scales with hectares
# ---------------------------------------------------------------------------

def test_potential_scales_with_hectares(client, db):
    """10ha farm: potential = per_ha_rate × 10."""
    farm = Farm(name="T24 Farm 10ha", municipality="Zapopan", tier="basic")
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="South Field", hectares=10.0)
    db.add(field)
    db.flush()
    db.add(HealthScore(field_id=field.id, score=80))
    db.add(TreatmentRecord(
        field_id=field.id, health_score_used=80, problema="test",
        causa_probable="test", tratamiento="Composta", urgencia="media",
        prevencion="rotacion", organic=True, costo_estimado_mxn=300,
    ))
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/economic-impact")
    data = resp.json()
    assert data["water_potential_mxn"] == 80_000    # 8000 × 10
    assert data["fertilizer_potential_mxn"] == 50_000  # 5000 × 10
    assert data["yield_potential_mxn"] == 77_000    # 7700 × 10


def test_potential_sum_le_total_potential(client, farm_20ha):
    """Sum of per-category potentials should equal total potential at 100% efficiency."""
    resp = client.get(f"/api/farms/{farm_20ha.id}/economic-impact")
    data = resp.json()
    total_potential = data["water_potential_mxn"] + data["fertilizer_potential_mxn"] + data["yield_potential_mxn"]
    # 160000 + 100000 + 154000 = 414000 (the famous $414K/20ha baseline)
    assert total_potential == 414_000


# ---------------------------------------------------------------------------
# Frontend HTML: chart infrastructure
# ---------------------------------------------------------------------------

def test_econ_chart_canvas_exists():
    """HTML must contain #econ-chart canvas (already existed; regression check)."""
    with open("frontend/economic-impact.html") as f:
        html = f.read()
    assert 'id="econ-chart"' in html


def test_chart_section_has_scenario_title():
    """Chart section title should reference scenario comparison."""
    with open("frontend/economic-impact.html") as f:
        html = f.read()
    # Title should reference "scenario" or "Sin/Con" or "comparison"
    assert re.search(
        r'(scenario|Sin.*cultivOS|Con.*cultivOS|comparison|Scenario|Baseline)',
        html,
        re.IGNORECASE
    ), "Chart section title should mention scenario comparison"


# ---------------------------------------------------------------------------
# Frontend JS: three-dataset chart
# ---------------------------------------------------------------------------

def test_js_update_chart_has_three_datasets():
    """updateChart() must reference 3 datasets (Sin / Estimado / Conservador)."""
    with open("frontend/economic-impact.js") as f:
        js = f.read()
    # Look for at least 3 dataset definitions in updateChart
    # Each dataset has a 'data:' key — count occurrences inside updateChart function
    update_chart_match = re.search(
        r'function\s+updateChart\s*\(.*?\n}',
        js,
        re.DOTALL
    )
    assert update_chart_match, "updateChart function not found in economic-impact.js"
    fn_body = update_chart_match.group(0)
    dataset_count = fn_body.count('data:')
    assert dataset_count >= 3, f"Expected ≥3 datasets in updateChart, found {dataset_count}"


def test_js_update_chart_uses_potential_fields():
    """updateChart() must use water_potential_mxn / fertilizer_potential_mxn / yield_potential_mxn."""
    with open("frontend/economic-impact.js") as f:
        js = f.read()
    assert "water_potential_mxn" in js, "JS must reference water_potential_mxn"
    assert "fertilizer_potential_mxn" in js, "JS must reference fertilizer_potential_mxn"
    assert "yield_potential_mxn" in js, "JS must reference yield_potential_mxn"


def test_js_update_chart_ghosted_dataset():
    """Chart must include a ghosted/transparent dataset for the Sin cultivOS baseline."""
    with open("frontend/economic-impact.js") as f:
        js = f.read()
    # Look for rgba with low alpha or opacity in the chart datasets
    assert re.search(r'rgba\s*\(.*?,\s*0\.[0-3]\d*\)', js) or 'opacity' in js or 'ghosted' in js.lower() or '0.25' in js or '0.3' in js, \
        "updateChart must render a ghosted/semi-transparent Sin cultivOS dataset"


def test_js_no_scenario_regression_in_reset():
    """resetStats() must not break with new potential fields (regression guard)."""
    with open("frontend/economic-impact.js") as f:
        js = f.read()
    assert 'function resetStats' in js


def test_js_conservative_dataset_uses_0_6_factor():
    """Conservative scenario must use 0.6× factor on current savings."""
    with open("frontend/economic-impact.js") as f:
        js = f.read()
    assert '0.6' in js, "Conservative scenario must multiply by 0.6"
