"""Tests for field risk heatmap endpoint.

GET /api/farms/{farm_id}/fields/risk-map
Returns per-field risk scores combining health, weather, disease, and thermal data.
"""

from cultivos.db.models import Farm, Field, HealthScore, NDVIResult, ThermalResult, WeatherRecord


VALID_DOMINANT_FACTORS = {"health", "weather", "disease", "thermal"}


def _mk_farm(db, name="Rancho Test", lat=20.5, lon=-103.3):
    farm = Farm(name=name, state="Jalisco", total_hectares=50.0,
                location_lat=lat, location_lon=lon)
    db.add(farm)
    db.flush()
    return farm


def _mk_field(db, farm_id, name="Parcela 1", crop_type="maiz"):
    field = Field(farm_id=farm_id, name=name, hectares=10.0, crop_type=crop_type)
    db.add(field)
    db.flush()
    return field


def _mk_health(db, field_id, score=75.0):
    hs = HealthScore(
        field_id=field_id, score=score,
        sources=["ndvi"], breakdown={},
    )
    db.add(hs)
    db.flush()
    return hs


def _mk_weather(db, farm_id, temp_c=22.0, wind_kmh=10.0, rainfall_mm=5.0):
    wr = WeatherRecord(
        farm_id=farm_id, temp_c=temp_c, humidity_pct=55.0,
        wind_kmh=wind_kmh, rainfall_mm=rainfall_mm,
        description="sunny", forecast_3day=[],
    )
    db.add(wr)
    db.flush()
    return wr


def _mk_ndvi(db, field_id, ndvi_mean=0.6, stress_pct=10.0, ndvi_std=0.05):
    ndvi = NDVIResult(
        field_id=field_id, ndvi_mean=ndvi_mean, ndvi_std=ndvi_std,
        ndvi_min=0.3, ndvi_max=0.9,
        pixels_total=1000, stress_pct=stress_pct,
        zones=[],
    )
    db.add(ndvi)
    db.flush()
    return ndvi


def _mk_thermal(db, field_id, stress_pct=15.0):
    tr = ThermalResult(
        field_id=field_id, temp_mean=28.0, temp_std=2.0,
        temp_min=24.0, temp_max=34.0,
        pixels_total=1000, stress_pct=stress_pct,
        irrigation_deficit=False,
    )
    db.add(tr)
    db.flush()
    return tr


class TestFieldRiskHeatmapEndpoint:

    def test_unknown_farm_returns_404(self, client):
        resp = client.get("/api/farms/9999/fields/risk-map")
        assert resp.status_code == 404

    def test_farm_with_no_fields_returns_empty_list(self, client, db):
        farm = _mk_farm(db)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/risk-map")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_field_with_no_sensor_data_returns_null_risk(self, client, db):
        farm = _mk_farm(db)
        _mk_field(db, farm.id)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/risk-map")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["risk_score"] is None
        assert data[0]["dominant_factor"] is None

    def test_response_includes_required_fields(self, client, db):
        farm = _mk_farm(db)
        field = _mk_field(db, farm.id)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/risk-map")
        assert resp.status_code == 200
        item = resp.json()[0]
        assert "field_id" in item
        assert "name" in item
        assert "lat" in item
        assert "lon" in item
        assert "risk_score" in item
        assert "dominant_factor" in item
        assert item["field_id"] == field.id
        assert item["name"] == "Parcela 1"

    def test_lat_lon_fallback_to_farm_coordinates(self, client, db):
        farm = _mk_farm(db, lat=20.5, lon=-103.3)
        _mk_field(db, farm.id)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/risk-map")
        item = resp.json()[0]
        assert item["lat"] == 20.5
        assert item["lon"] == -103.3

    def test_risk_score_is_bounded_0_to_100(self, client, db):
        farm = _mk_farm(db)
        field = _mk_field(db, farm.id)
        # Seed worst-case scenario: very unhealthy field
        _mk_health(db, field.id, score=2.0)  # near-zero health
        _mk_weather(db, farm.id, temp_c=1.0, wind_kmh=70.0)  # frost + high wind
        _mk_ndvi(db, field.id, ndvi_mean=0.2, stress_pct=80.0, ndvi_std=0.3)
        _mk_thermal(db, field.id, stress_pct=90.0)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/risk-map")
        assert resp.status_code == 200
        score = resp.json()[0]["risk_score"]
        assert score is not None
        assert 0.0 <= score <= 100.0

    def test_dominant_factor_is_valid_enum(self, client, db):
        farm = _mk_farm(db)
        field = _mk_field(db, farm.id)
        _mk_health(db, field.id, score=30.0)
        _mk_weather(db, farm.id)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/risk-map")
        item = resp.json()[0]
        assert item["dominant_factor"] in VALID_DOMINANT_FACTORS

    def test_low_health_produces_health_dominant(self, client, db):
        """A field with very low health score and no other risk signals should report health as dominant."""
        farm = _mk_farm(db)
        field = _mk_field(db, farm.id)
        # health_risk = 100 - 5 = 95 → dominates
        _mk_health(db, field.id, score=5.0)
        # Benign weather — no alerts triggered
        _mk_weather(db, farm.id, temp_c=22.0, wind_kmh=10.0, rainfall_mm=5.0)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/risk-map")
        item = resp.json()[0]
        assert item["dominant_factor"] == "health"

    def test_critical_weather_contributes_to_risk(self, client, db):
        """Frost temperature should raise the risk score above zero."""
        farm = _mk_farm(db)
        field = _mk_field(db, farm.id)
        _mk_health(db, field.id, score=80.0)  # mostly healthy
        _mk_weather(db, farm.id, temp_c=0.5)  # frost — critica alert
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/risk-map")
        score = resp.json()[0]["risk_score"]
        assert score is not None
        assert score > 0.0

    def test_multiple_fields_all_included(self, client, db):
        farm = _mk_farm(db)
        _mk_field(db, farm.id, name="Campo Norte")
        _mk_field(db, farm.id, name="Campo Sur")
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/risk-map")
        assert resp.status_code == 200
        assert len(resp.json()) == 2
        names = {item["name"] for item in resp.json()}
        assert names == {"Campo Norte", "Campo Sur"}

    def test_healthy_field_has_lower_risk_than_sick_field(self, client, db):
        farm = _mk_farm(db)
        healthy = _mk_field(db, farm.id, name="Sano")
        sick = _mk_field(db, farm.id, name="Enfermo")
        _mk_health(db, healthy.id, score=90.0)
        _mk_health(db, sick.id, score=20.0)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/risk-map")
        items = {item["name"]: item for item in resp.json()}
        assert items["Sano"]["risk_score"] < items["Enfermo"]["risk_score"]

    def test_only_returns_fields_for_requested_farm(self, client, db):
        farm_a = _mk_farm(db, name="Granja A")
        farm_b = _mk_farm(db, name="Granja B")
        _mk_field(db, farm_a.id, name="Campo A")
        _mk_field(db, farm_b.id, name="Campo B")
        db.commit()
        resp = client.get(f"/api/farms/{farm_a.id}/fields/risk-map")
        names = [item["name"] for item in resp.json()]
        assert "Campo A" in names
        assert "Campo B" not in names
