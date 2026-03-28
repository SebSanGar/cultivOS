"""Tests for Alert Configuration API — custom thresholds per farm."""

import pytest

from cultivos.db.models import Farm, Field, HealthScore, AlertConfig


class TestAlertConfigAPI:
    """POST/GET/PUT /api/farms/{farm_id}/alert-config."""

    def _create_farm(self, client, admin_headers):
        resp = client.post(
            "/api/farms",
            json={"name": "Finca Prueba", "state": "Jalisco"},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        return resp.json()["id"]

    # --- Default config auto-created with farm ---

    def test_get_default_config(self, client, admin_headers):
        """GET should return default thresholds even if never explicitly set."""
        farm_id = self._create_farm(client, admin_headers)
        resp = client.get(f"/api/farms/{farm_id}/alert-config", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["farm_id"] == farm_id
        assert data["health_score_floor"] == 40
        assert data["ndvi_minimum"] == 0.3
        assert data["temp_max_c"] == 45.0

    # --- Custom thresholds ---

    def test_update_config(self, client, admin_headers):
        """PUT should update thresholds."""
        farm_id = self._create_farm(client, admin_headers)
        resp = client.put(
            f"/api/farms/{farm_id}/alert-config",
            json={"health_score_floor": 50, "ndvi_minimum": 0.4},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["health_score_floor"] == 50
        assert data["ndvi_minimum"] == 0.4
        # Unchanged field keeps default
        assert data["temp_max_c"] == 45.0

    def test_create_config_explicitly(self, client, admin_headers):
        """POST should create a config with custom values."""
        farm_id = self._create_farm(client, admin_headers)
        resp = client.post(
            f"/api/farms/{farm_id}/alert-config",
            json={"health_score_floor": 60, "ndvi_minimum": 0.5, "temp_max_c": 40.0},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["health_score_floor"] == 60
        assert data["ndvi_minimum"] == 0.5
        assert data["temp_max_c"] == 40.0

    # --- Validation: invalid thresholds rejected ---

    def test_invalid_health_floor_above_100(self, client, admin_headers):
        """health_score_floor > 100 should be rejected."""
        farm_id = self._create_farm(client, admin_headers)
        resp = client.post(
            f"/api/farms/{farm_id}/alert-config",
            json={"health_score_floor": 101},
            headers=admin_headers,
        )
        assert resp.status_code == 422

    def test_invalid_health_floor_below_0(self, client, admin_headers):
        """health_score_floor < 0 should be rejected."""
        farm_id = self._create_farm(client, admin_headers)
        resp = client.post(
            f"/api/farms/{farm_id}/alert-config",
            json={"health_score_floor": -1},
            headers=admin_headers,
        )
        assert resp.status_code == 422

    def test_invalid_ndvi_above_1(self, client, admin_headers):
        """ndvi_minimum > 1.0 should be rejected."""
        farm_id = self._create_farm(client, admin_headers)
        resp = client.post(
            f"/api/farms/{farm_id}/alert-config",
            json={"ndvi_minimum": 1.5},
            headers=admin_headers,
        )
        assert resp.status_code == 422

    def test_invalid_temp_negative(self, client, admin_headers):
        """temp_max_c < -50 (unreasonable) should be rejected."""
        farm_id = self._create_farm(client, admin_headers)
        resp = client.post(
            f"/api/farms/{farm_id}/alert-config",
            json={"temp_max_c": -100},
            headers=admin_headers,
        )
        assert resp.status_code == 422

    # --- 404 for nonexistent farm ---

    def test_get_config_farm_not_found(self, client, admin_headers):
        resp = client.get("/api/farms/9999/alert-config", headers=admin_headers)
        assert resp.status_code == 404

    def test_put_config_farm_not_found(self, client, admin_headers):
        resp = client.put(
            "/api/farms/9999/alert-config",
            json={"health_score_floor": 50},
            headers=admin_headers,
        )
        assert resp.status_code == 404


class TestAlertCheckUsesConfig:
    """Alert check endpoints should respect custom thresholds from AlertConfig."""

    def _setup_farm_field_health(self, db, client, admin_headers, health_score=35):
        """Create farm + field + health score for alert testing."""
        resp = client.post(
            "/api/farms",
            json={"name": "Finca Config", "state": "Jalisco"},
            headers=admin_headers,
        )
        farm_id = resp.json()["id"]

        resp = client.post(
            f"/api/farms/{farm_id}/fields",
            json={"name": "Lote A", "crop_type": "maiz", "hectares": 5},
            headers=admin_headers,
        )
        field_id = resp.json()["id"]

        from datetime import datetime
        hs = HealthScore(
            field_id=field_id, score=health_score, scored_at=datetime.utcnow()
        )
        db.add(hs)
        db.commit()

        return farm_id, field_id

    def test_custom_threshold_triggers_alert(self, db, client, admin_headers):
        """Score 45 is above default (40) but below custom floor (50) — should alert."""
        farm_id, field_id = self._setup_farm_field_health(
            db, client, admin_headers, health_score=45
        )
        # Set custom floor to 50
        client.post(
            f"/api/farms/{farm_id}/alert-config",
            json={"health_score_floor": 50},
            headers=admin_headers,
        )
        resp = client.post(
            f"/api/farms/{farm_id}/alerts/check", headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["alerts_created"]) == 1

    def test_custom_threshold_suppresses_alert(self, db, client, admin_headers):
        """Score 35 is below default (40) but above custom floor (30) — should NOT alert."""
        farm_id, field_id = self._setup_farm_field_health(
            db, client, admin_headers, health_score=35
        )
        # Lower the floor to 30
        client.post(
            f"/api/farms/{farm_id}/alert-config",
            json={"health_score_floor": 30},
            headers=admin_headers,
        )
        resp = client.post(
            f"/api/farms/{farm_id}/alerts/check", headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["alerts_created"]) == 0
