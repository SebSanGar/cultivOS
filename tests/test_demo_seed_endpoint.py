"""Tests for the POST /api/demo/seed endpoint and demo seeding via API."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import (
    Base, Farm, Field, HealthScore, NDVIResult, FlightLog,
    MicrobiomeRecord, Alert, AlertLog, AlertConfig, FarmerFeedback,
    TreatmentRecord, SoilAnalysis, ThermalResult, WeatherRecord,
)


@pytest.fixture
def client(db):
    app = create_app()
    from cultivos.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app, raise_server_exceptions=False)


class TestDemoSeedEndpoint:
    """POST /api/demo/seed triggers demo data seeding."""

    def test_seed_returns_201_with_counts(self, client):
        resp = client.post("/api/demo/seed")
        assert resp.status_code == 201
        data = resp.json()
        assert data["farms"] == 8  # 5 Jalisco + 3 Ontario
        assert data["fields"] >= 18  # 8 farms with 2-3 fields each

    def test_seed_creates_farms_in_db(self, client, db):
        client.post("/api/demo/seed")
        farms = db.query(Farm).filter(Farm.name.contains("[DEMO]")).all()
        assert len(farms) == 8  # 5 Jalisco + 3 Ontario

    def test_seed_creates_fields_with_data(self, client, db):
        client.post("/api/demo/seed")
        fields = db.query(Field).all()
        assert len(fields) >= 12
        # Each field should have NDVI + health data
        for f in fields:
            assert db.query(NDVIResult).filter_by(field_id=f.id).count() >= 24
            assert db.query(HealthScore).filter_by(field_id=f.id).count() >= 24

    def test_seed_is_idempotent(self, client):
        resp1 = client.post("/api/demo/seed")
        assert resp1.status_code == 201
        resp2 = client.post("/api/demo/seed")
        assert resp2.status_code == 200
        assert resp2.json()["message"] == "Demo data already exists"

    def test_seed_idempotent_no_duplicates(self, client, db):
        client.post("/api/demo/seed")
        count1 = db.query(Farm).count()
        client.post("/api/demo/seed")
        count2 = db.query(Farm).count()
        assert count1 == count2

    def test_get_demo_farms_returns_seeded_data(self, client):
        client.post("/api/demo/seed")
        resp = client.get("/api/demo/farms")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 8  # 5 Jalisco + 3 Ontario
        # Each farm should have fields
        for farm in data:
            assert len(farm["fields"]) >= 2


class TestDemoSeedFlightLogs:
    """Verify seed creates FlightLog records for drone operations pages."""

    def test_flight_logs_created_per_field(self, client, db):
        client.post("/api/demo/seed")
        fields = db.query(Field).all()
        for f in fields:
            flights = db.query(FlightLog).filter_by(field_id=f.id).all()
            assert len(flights) >= 2, f"Field {f.name} has < 2 flights"

    def test_flight_logs_have_complete_data(self, client, db):
        client.post("/api/demo/seed")
        flight = db.query(FlightLog).first()
        assert flight.drone_type in ("mavic_multispectral", "mavic_thermal", "agras_t100")
        assert flight.mission_type in ("health_scan", "thermal_check", "spray")
        assert flight.status == "complete"
        assert flight.duration_minutes > 0
        assert flight.altitude_m > 0
        assert flight.images_count > 0
        assert flight.coverage_pct > 0


class TestDemoSeedMicrobiome:
    """Verify seed creates MicrobiomeRecord data."""

    def test_microbiome_records_created_per_field(self, client, db):
        client.post("/api/demo/seed")
        fields = db.query(Field).all()
        for f in fields:
            records = db.query(MicrobiomeRecord).filter_by(field_id=f.id).all()
            assert len(records) >= 2, f"Field {f.name} has < 2 microbiome records"

    def test_microbiome_shows_improvement_arc(self, client, db):
        """Earlier records should be more degraded than later ones."""
        client.post("/api/demo/seed")
        field = db.query(Field).first()
        records = (db.query(MicrobiomeRecord)
                   .filter_by(field_id=field.id)
                   .order_by(MicrobiomeRecord.sampled_at)
                   .all())
        assert records[0].microbial_biomass_carbon < records[-1].microbial_biomass_carbon


class TestDemoSeedAlerts:
    """Verify seed creates Alert/AlertLog/AlertConfig data."""

    def test_alerts_created_per_farm(self, client, db):
        client.post("/api/demo/seed")
        farms = db.query(Farm).filter(Farm.name.contains("[DEMO]")).all()
        for farm in farms:
            alerts = db.query(Alert).filter_by(farm_id=farm.id).all()
            assert len(alerts) >= 2, f"Farm {farm.name} has < 2 alerts"

    def test_alert_logs_created(self, client, db):
        client.post("/api/demo/seed")
        total = db.query(AlertLog).count()
        assert total >= 10, f"Only {total} alert logs, expected >= 10"

    def test_alert_configs_per_farm(self, client, db):
        client.post("/api/demo/seed")
        farms = db.query(Farm).filter(Farm.name.contains("[DEMO]")).all()
        for farm in farms:
            config = db.query(AlertConfig).filter_by(farm_id=farm.id).first()
            assert config is not None, f"Farm {farm.name} has no alert config"


class TestDemoSeedFarmerFeedback:
    """Verify seed creates FarmerFeedback data for trust scores page."""

    def test_feedback_exists(self, client, db):
        client.post("/api/demo/seed")
        total = db.query(FarmerFeedback).count()
        assert total >= 8, f"Only {total} feedback records, expected >= 8"

    def test_feedback_has_ratings(self, client, db):
        client.post("/api/demo/seed")
        fb = db.query(FarmerFeedback).first()
        assert 1 <= fb.rating <= 5
        assert fb.worked is not None
        assert fb.farmer_notes is not None


class TestDemoSeedNewFarms:
    """Verify the 2 new farms (Arandas + Lagos) are present."""

    def test_arandas_farm_exists(self, client, db):
        client.post("/api/demo/seed")
        farm = db.query(Farm).filter(Farm.municipality == "Arandas").first()
        assert farm is not None

    def test_lagos_farm_exists(self, client, db):
        client.post("/api/demo/seed")
        farm = db.query(Farm).filter(Farm.municipality == "Lagos de Moreno").first()
        assert farm is not None

    def test_new_farms_have_boundary_coordinates(self, client, db):
        """New farms should have fields with boundary coordinates for map page."""
        client.post("/api/demo/seed")
        fields = db.query(Field).all()
        fields_with_boundaries = [f for f in fields if f.boundary_coordinates]
        assert len(fields_with_boundaries) >= 6, \
            f"Only {len(fields_with_boundaries)} fields have boundaries, expected >= 6"
