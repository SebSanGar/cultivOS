"""Tests for GET /api/system/health-detailed — system status for grant reviewers."""

import sys

import pytest
from cultivos.db.models import (
    Farm, Field, SoilAnalysis, NDVIResult, ThermalResult,
    TreatmentRecord, Alert, FlightLog, WeatherRecord,
)


class TestHealthDetailedEndpoint:
    """Tests for the detailed system health endpoint."""

    def test_returns_200(self, client):
        resp = client.get("/api/system/health-detailed")
        assert resp.status_code == 200

    def test_contains_api_version(self, client):
        data = client.get("/api/system/health-detailed").json()
        assert "api_version" in data
        assert data["api_version"] == "0.1.0"

    def test_contains_python_version(self, client):
        data = client.get("/api/system/health-detailed").json()
        assert "python_version" in data
        assert data["python_version"].startswith(f"{sys.version_info.major}.")

    def test_contains_fastapi_version(self, client):
        data = client.get("/api/system/health-detailed").json()
        assert "fastapi_version" in data
        assert len(data["fastapi_version"]) > 0

    def test_contains_uptime(self, client):
        data = client.get("/api/system/health-detailed").json()
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0

    def test_contains_database_counts(self, client):
        data = client.get("/api/system/health-detailed").json()
        assert "database" in data
        db_counts = data["database"]
        for key in ["farms", "fields", "soil_analyses", "ndvi_results",
                     "thermal_results", "treatments", "alerts",
                     "flight_logs", "weather_records"]:
            assert key in db_counts, f"Missing key: {key}"
            assert isinstance(db_counts[key], int)

    def test_empty_db_returns_zero_counts(self, client):
        data = client.get("/api/system/health-detailed").json()
        db_counts = data["database"]
        for key in db_counts:
            assert db_counts[key] == 0

    def test_counts_reflect_seeded_data(self, client, db):
        # Seed some data
        farm = Farm(name="Test Farm", location_lat=20.5, location_lon=-103.3, state="Jalisco")
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="Parcela 1", crop_type="maiz", hectares=5.0)
        db.add(field)
        db.flush()
        from datetime import datetime
        db.add(SoilAnalysis(field_id=field.id, ph=6.5, organic_matter_pct=3.0,
                            nitrogen_ppm=40, phosphorus_ppm=20, potassium_ppm=150,
                            sampled_at=datetime(2026, 3, 1)))
        db.add(NDVIResult(field_id=field.id, ndvi_mean=0.72, ndvi_std=0.1,
                          ndvi_min=0.4, ndvi_max=0.9, pixels_total=1000,
                          stress_pct=5.0, zones=[]))
        db.add(ThermalResult(field_id=field.id, temp_mean=28.0, temp_std=2.0,
                              temp_min=22.0, temp_max=35.0, pixels_total=1000,
                              stress_pct=10.0))
        db.commit()

        data = client.get("/api/system/health-detailed").json()
        assert data["database"]["farms"] == 1
        assert data["database"]["fields"] == 1
        assert data["database"]["soil_analyses"] == 1
        assert data["database"]["ndvi_results"] == 1
        assert data["database"]["thermal_results"] == 1

    def test_contains_latest_data_timestamps(self, client):
        data = client.get("/api/system/health-detailed").json()
        assert "latest_data" in data
        for key in ["soil", "ndvi", "thermal", "weather"]:
            assert key in data["latest_data"]

    def test_contains_endpoint_count(self, client):
        data = client.get("/api/system/health-detailed").json()
        assert "endpoint_count" in data
        assert isinstance(data["endpoint_count"], int)
        assert data["endpoint_count"] > 50  # We have 100+ endpoints

    def test_contains_test_count(self, client):
        data = client.get("/api/system/health-detailed").json()
        assert "test_count" in data
        assert isinstance(data["test_count"], int)
        assert data["test_count"] >= 2000  # We have 2271+ tests

    def test_contains_status_ok(self, client):
        data = client.get("/api/system/health-detailed").json()
        assert data["status"] == "operational"
