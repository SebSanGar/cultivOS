"""Tests for GET /api/status — platform health check endpoint."""

from datetime import datetime, timedelta

from cultivos.db.models import (
    Farm, Field, SoilAnalysis, NDVIResult, ThermalResult, WeatherRecord,
)


class TestPlatformStatus:
    """GET /api/status returns platform overview with counts and timestamps."""

    def test_returns_200(self, client):
        resp = client.get("/api/status")
        assert resp.status_code == 200

    def test_contains_expected_keys(self, client):
        data = client.get("/api/status").json()
        assert "api_version" in data
        assert "total_farms" in data
        assert "total_fields" in data
        assert "latest_data" in data
        assert "uptime_seconds" in data

    def test_empty_db(self, client):
        data = client.get("/api/status").json()
        assert data["total_farms"] == 0
        assert data["total_fields"] == 0
        assert data["latest_data"]["soil"] is None
        assert data["latest_data"]["ndvi"] is None
        assert data["latest_data"]["thermal"] is None
        assert data["latest_data"]["weather"] is None

    def test_counts_with_data(self, client, db):
        farm = Farm(name="Rancho Status", owner_name="Test")
        db.add(farm)
        db.flush()
        f1 = Field(farm_id=farm.id, name="Campo A", crop_type="maiz")
        f2 = Field(farm_id=farm.id, name="Campo B", crop_type="agave")
        db.add_all([f1, f2])
        db.commit()

        data = client.get("/api/status").json()
        assert data["total_farms"] == 1
        assert data["total_fields"] == 2

    def test_latest_timestamps(self, client, db):
        farm = Farm(name="Rancho Tiempo", owner_name="Test")
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="Campo T", crop_type="maiz")
        db.add(field)
        db.flush()

        now = datetime.utcnow()
        old = now - timedelta(days=30)

        # Soil — two records, should return the latest
        db.add(SoilAnalysis(field_id=field.id, sampled_at=old))
        db.add(SoilAnalysis(field_id=field.id, sampled_at=now))

        # NDVI — one record
        db.add(NDVIResult(
            field_id=field.id, ndvi_mean=0.6, ndvi_std=0.1,
            ndvi_min=0.3, ndvi_max=0.9, pixels_total=1000,
            stress_pct=10.0, zones=[], analyzed_at=now,
        ))

        # Thermal — one record
        db.add(ThermalResult(
            field_id=field.id, temp_mean=28.0, temp_std=2.0,
            temp_min=24.0, temp_max=32.0, pixels_total=500,
            stress_pct=5.0, analyzed_at=now,
        ))

        # Weather — one record
        db.add(WeatherRecord(
            farm_id=farm.id, temp_c=25.0, humidity_pct=60.0,
            wind_kmh=10.0, rainfall_mm=0.0, description="Soleado",
            forecast_3day=[], recorded_at=now,
        ))
        db.commit()

        data = client.get("/api/status").json()
        latest = data["latest_data"]
        assert latest["soil"] is not None
        assert latest["ndvi"] is not None
        assert latest["thermal"] is not None
        assert latest["weather"] is not None

    def test_api_version_present(self, client):
        data = client.get("/api/status").json()
        assert data["api_version"] == "0.1.0"

    def test_uptime_is_positive(self, client):
        data = client.get("/api/status").json()
        assert data["uptime_seconds"] >= 0
