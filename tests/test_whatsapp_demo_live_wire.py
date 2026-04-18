"""Contract tests for D8 — WhatsApp demo live-data wiring.

Ensure frontend/whatsapp-demo.js targets the right API paths and that the
/intelligence endpoint still returns the keys the JS consumes. These
contract tests prevent silent drift: if either side changes without the
other, grant reviewers would see an empty-state demo instead of live data.
"""

from datetime import datetime, timedelta


class TestWhatsAppDemoJSWiring:
    """The shipped JS file must reference the live-data endpoints."""

    def test_demo_js_fetches_farms_api(self, client):
        resp = client.get("/whatsapp-demo.js")
        assert resp.status_code == 200
        assert "/api/farms" in resp.text

    def test_demo_js_fetches_fields_under_farm(self, client):
        resp = client.get("/whatsapp-demo.js")
        assert "/fields" in resp.text
        # Must build the farm-scoped fields path dynamically, not hard-code an id.
        assert "farm.id" in resp.text

    def test_demo_js_fetches_intelligence_endpoint(self, client):
        resp = client.get("/whatsapp-demo.js")
        assert "/intelligence" in resp.text

    def test_demo_js_has_empty_state_fallback(self, client):
        """If no farm/field/intel exists, the demo must degrade gracefully."""
        resp = client.get("/whatsapp-demo.js")
        assert "emptyStateScript" in resp.text

    def test_demo_js_consumes_treatments_from_intelligence(self, client):
        """treatmentsReport() reads intel.treatments — single intelligence call populates chat."""
        resp = client.get("/whatsapp-demo.js")
        assert "intel.treatments" in resp.text or "intel[\"treatments\"]" in resp.text


class TestIntelligenceContractForDemo:
    """The /intelligence endpoint must return the exact keys whatsapp-demo.js reads."""

    def _seed(self, db):
        from cultivos.db.models import (
            Farm, Field, HealthScore, NDVIResult, ThermalResult,
            WeatherRecord, TreatmentRecord,
        )
        farm = Farm(
            name="Demo Live", owner_name="Don Manuel",
            location_lat=20.6, location_lon=-103.3,
            total_hectares=10, municipality="Zapopan", state="Jalisco",
        )
        db.add(farm); db.flush()
        field = Field(
            farm_id=farm.id, name="Milpa Demo", crop_type="maiz",
            hectares=5, planted_at=datetime.utcnow() - timedelta(days=30),
        )
        db.add(field); db.flush()
        db.add(HealthScore(
            field_id=field.id, score=68, trend="improving",
            sources=["ndvi"], breakdown={"ndvi": 68}, scored_at=datetime.utcnow(),
        ))
        db.add(NDVIResult(
            field_id=field.id, ndvi_mean=0.6, ndvi_std=0.1,
            ndvi_min=0.3, ndvi_max=0.8, pixels_total=1000,
            stress_pct=10.0, zones=[], analyzed_at=datetime.utcnow(),
        ))
        db.add(ThermalResult(
            field_id=field.id, temp_mean=27, temp_std=2, temp_min=22, temp_max=32,
            pixels_total=1000, stress_pct=8, irrigation_deficit=False,
            analyzed_at=datetime.utcnow(),
        ))
        db.add(WeatherRecord(
            farm_id=farm.id, temp_c=26, humidity_pct=60, wind_kmh=10,
            rainfall_mm=0, description="soleado", forecast_3day=[],
            recorded_at=datetime.utcnow(),
        ))
        db.add(TreatmentRecord(
            field_id=field.id, health_score_used=68,
            problema="Estres leve", causa_probable="poca humedad",
            tratamiento="Aumentar riego", costo_estimado_mxn=300,
            urgencia="baja", prevencion="monitoreo", organic=True,
        ))
        db.commit()
        return farm, field

    def test_intelligence_returns_keys_demo_consumes(self, client, db):
        farm, field = self._seed(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intelligence")
        assert resp.status_code == 200
        data = resp.json()
        # Keys whatsapp-demo.js reads in healthReport() + treatmentsReport():
        for key in ("field_name", "health", "ndvi", "thermal", "weather", "treatments"):
            assert key in data, f"intelligence response missing '{key}' — demo JS would break"
        assert data["field_name"] == "Milpa Demo"
        assert data["health"]["score"] == 68
        assert data["ndvi"]["ndvi_mean"] == 0.6
        assert data["thermal"]["temp_mean"] == 27
        assert data["weather"]["humidity_pct"] == 60
        assert isinstance(data["treatments"], list) and len(data["treatments"]) == 1
