"""T2.3 — Per-hectare breakdown table + total alongside ("$20,700/ha · $414,000 total").

RED tests — must FAIL before implementation.
GREEN after:
  - EconomicImpactOut gains savings_per_ha_mxn, water_savings_per_ha_mxn,
    fertilizer_savings_per_ha_mxn, yield_improvement_per_ha_mxn
  - API computes per-ha values = round(total / hectares) when hectares > 0
  - None when no fields (hectares == 0)
  - Frontend: #econ-per-ha-table section exists in HTML
  - Frontend: row ids for each category (econ-per-ha-total, econ-per-ha-water, etc.)
  - JS: updatePerHaTable() function reads savings_per_ha_mxn from data
"""
import pytest

from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def farm_20ha(client, db):
    """Farm with 20ha field + health scores + treatments."""
    farm = Farm(name="T23 Farm 20ha", municipality="Zapopan", tier="standard")
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="North Field", hectares=20.0)
    db.add(field)
    db.flush()
    for score_val in [60, 65, 70]:
        db.add(HealthScore(field_id=field.id, score=score_val))
    for _ in range(3):
        db.add(TreatmentRecord(
            field_id=field.id, health_score_used=65, problema="test",
            causa_probable="test", tratamiento="Composta", urgencia="media",
            prevencion="rotacion", organic=True, costo_estimado_mxn=500,
        ))
    db.commit()
    return farm


@pytest.fixture
def farm_no_fields(client, db):
    """Farm with no fields — hectares == 0."""
    farm = Farm(name="T23 Empty Farm", municipality="Guadalajara")
    db.add(farm)
    db.commit()
    return farm


# ---------------------------------------------------------------------------
# API — per-ha fields present in response
# ---------------------------------------------------------------------------

class TestT23PerHaFieldsPresent:
    """economic-impact endpoint must return per-ha breakdown fields."""

    def test_savings_per_ha_mxn_present(self, client, farm_20ha):
        r = client.get(f"/api/farms/{farm_20ha.id}/economic-impact")
        assert r.status_code == 200
        assert "savings_per_ha_mxn" in r.json()

    def test_water_savings_per_ha_present(self, client, farm_20ha):
        r = client.get(f"/api/farms/{farm_20ha.id}/economic-impact")
        assert r.status_code == 200
        assert "water_savings_per_ha_mxn" in r.json()

    def test_fertilizer_savings_per_ha_present(self, client, farm_20ha):
        r = client.get(f"/api/farms/{farm_20ha.id}/economic-impact")
        assert r.status_code == 200
        assert "fertilizer_savings_per_ha_mxn" in r.json()

    def test_yield_improvement_per_ha_present(self, client, farm_20ha):
        r = client.get(f"/api/farms/{farm_20ha.id}/economic-impact")
        assert r.status_code == 200
        assert "yield_improvement_per_ha_mxn" in r.json()


# ---------------------------------------------------------------------------
# API — per-ha computation correctness
# ---------------------------------------------------------------------------

class TestT23PerHaValues:
    """Per-ha values = round(total / hectares)."""

    def test_savings_per_ha_equals_total_divided_by_hectares(self, client, farm_20ha):
        r = client.get(f"/api/farms/{farm_20ha.id}/economic-impact")
        assert r.status_code == 200
        data = r.json()
        total = data["total_savings_mxn"]
        ha = data["hectares"]
        expected_per_ha = round(total / ha)
        assert data["savings_per_ha_mxn"] == expected_per_ha

    def test_water_per_ha_equals_water_divided_by_hectares(self, client, farm_20ha):
        r = client.get(f"/api/farms/{farm_20ha.id}/economic-impact")
        data = r.json()
        ha = data["hectares"]
        expected = round(data["water_savings_mxn"] / ha)
        assert data["water_savings_per_ha_mxn"] == expected

    def test_fertilizer_per_ha_equals_fertilizer_divided_by_hectares(self, client, farm_20ha):
        r = client.get(f"/api/farms/{farm_20ha.id}/economic-impact")
        data = r.json()
        ha = data["hectares"]
        expected = round(data["fertilizer_savings_mxn"] / ha)
        assert data["fertilizer_savings_per_ha_mxn"] == expected

    def test_yield_per_ha_equals_yield_divided_by_hectares(self, client, farm_20ha):
        r = client.get(f"/api/farms/{farm_20ha.id}/economic-impact")
        data = r.json()
        ha = data["hectares"]
        expected = round(data["yield_improvement_mxn"] / ha)
        assert data["yield_improvement_per_ha_mxn"] == expected

    def test_per_ha_is_positive_when_savings_positive(self, client, farm_20ha):
        r = client.get(f"/api/farms/{farm_20ha.id}/economic-impact")
        data = r.json()
        assert data["savings_per_ha_mxn"] > 0


# ---------------------------------------------------------------------------
# API — null when no fields (zero hectares)
# ---------------------------------------------------------------------------

class TestT23PerHaNullNoData:
    """Per-ha fields must be None when farm has no fields (hectares == 0)."""

    def test_savings_per_ha_null_when_no_fields(self, client, farm_no_fields):
        r = client.get(f"/api/farms/{farm_no_fields.id}/economic-impact")
        assert r.status_code == 200
        assert r.json()["savings_per_ha_mxn"] is None

    def test_water_per_ha_null_when_no_fields(self, client, farm_no_fields):
        r = client.get(f"/api/farms/{farm_no_fields.id}/economic-impact")
        assert r.json()["water_savings_per_ha_mxn"] is None

    def test_fertilizer_per_ha_null_when_no_fields(self, client, farm_no_fields):
        r = client.get(f"/api/farms/{farm_no_fields.id}/economic-impact")
        assert r.json()["fertilizer_savings_per_ha_mxn"] is None


# ---------------------------------------------------------------------------
# Frontend HTML — per-ha table section
# ---------------------------------------------------------------------------

class TestT23FrontendHTML:
    """economic-impact.html must have per-ha breakdown table elements."""

    def test_per_ha_table_section_exists(self, client):
        r = client.get("/impacto-economico")
        assert r.status_code == 200
        assert 'id="econ-per-ha-table"' in r.text

    def test_per_ha_total_row_id_exists(self, client):
        r = client.get("/impacto-economico")
        assert 'id="econ-per-ha-total"' in r.text

    def test_per_ha_water_row_id_exists(self, client):
        r = client.get("/impacto-economico")
        assert 'id="econ-per-ha-water"' in r.text

    def test_per_ha_fertilizer_row_id_exists(self, client):
        r = client.get("/impacto-economico")
        assert 'id="econ-per-ha-fertilizer"' in r.text

    def test_per_ha_yield_row_id_exists(self, client):
        r = client.get("/impacto-economico")
        assert 'id="econ-per-ha-yield"' in r.text


# ---------------------------------------------------------------------------
# Frontend JS — updatePerHaTable function
# ---------------------------------------------------------------------------

class TestT23FrontendJS:
    """economic-impact.js must contain updatePerHaTable function."""

    def _js(self, client):
        r = client.get("/economic-impact.js")
        assert r.status_code == 200
        return r.text

    def test_update_per_ha_table_function_exists(self, client):
        assert "updatePerHaTable" in self._js(client)

    def test_js_reads_savings_per_ha_from_data(self, client):
        assert "savings_per_ha_mxn" in self._js(client)

    def test_update_per_ha_table_called_from_load(self, client):
        js = self._js(client)
        assert "updatePerHaTable" in js
        assert "loadEconomicImpact" in js
