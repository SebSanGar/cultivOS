"""Tests for Notification History API — alert log with acknowledge."""

import pytest

from cultivos.db.models import Farm, Field, AlertLog


class TestNotificationAPI:
    """GET /api/farms/{id}/notifications, POST acknowledge."""

    def _create_farm_and_field(self, client, admin_headers):
        resp = client.post(
            "/api/farms",
            json={"name": "Finca Prueba", "state": "Jalisco"},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        farm_id = resp.json()["id"]
        resp = client.post(
            f"/api/farms/{farm_id}/fields",
            json={"name": "Parcela A", "crop_type": "maiz", "hectares": 5.0},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        field_id = resp.json()["id"]
        return farm_id, field_id

    # --- Create and list notifications ---

    def test_create_notification(self, client, admin_headers, db):
        """POST creates a notification log entry."""
        farm_id, field_id = self._create_farm_and_field(client, admin_headers)
        resp = client.post(
            f"/api/farms/{farm_id}/notifications",
            json={
                "field_id": field_id,
                "alert_type": "health",
                "message": "NDVI bajo detectado en parcela A",
                "severity": "warning",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["farm_id"] == farm_id
        assert data["field_id"] == field_id
        assert data["alert_type"] == "health"
        assert data["severity"] == "warning"
        assert data["acknowledged"] is False

    def test_list_notifications(self, client, admin_headers, db):
        """GET returns all notifications for a farm."""
        farm_id, field_id = self._create_farm_and_field(client, admin_headers)
        # Create two notifications
        for msg in ["Alerta 1", "Alerta 2"]:
            client.post(
                f"/api/farms/{farm_id}/notifications",
                json={"alert_type": "health", "message": msg, "severity": "info"},
                headers=admin_headers,
            )
        resp = client.get(
            f"/api/farms/{farm_id}/notifications", headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    # --- Acknowledge ---

    def test_acknowledge_notification(self, client, admin_headers, db):
        """POST acknowledge flips acknowledged flag to true."""
        farm_id, field_id = self._create_farm_and_field(client, admin_headers)
        create_resp = client.post(
            f"/api/farms/{farm_id}/notifications",
            json={"alert_type": "irrigation", "message": "Riego necesario", "severity": "critical"},
            headers=admin_headers,
        )
        notif_id = create_resp.json()["id"]

        resp = client.post(
            f"/api/farms/{farm_id}/notifications/{notif_id}/acknowledge",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["acknowledged"] is True

    def test_acknowledge_nonexistent(self, client, admin_headers, db):
        """POST acknowledge for missing notification returns 404."""
        farm_id, _ = self._create_farm_and_field(client, admin_headers)
        resp = client.post(
            f"/api/farms/{farm_id}/notifications/9999/acknowledge",
            headers=admin_headers,
        )
        assert resp.status_code == 404

    # --- Filter by severity ---

    def test_filter_by_severity(self, client, admin_headers, db):
        """GET with severity param filters results."""
        farm_id, _ = self._create_farm_and_field(client, admin_headers)
        client.post(
            f"/api/farms/{farm_id}/notifications",
            json={"alert_type": "health", "message": "Info msg", "severity": "info"},
            headers=admin_headers,
        )
        client.post(
            f"/api/farms/{farm_id}/notifications",
            json={"alert_type": "pest", "message": "Critical msg", "severity": "critical"},
            headers=admin_headers,
        )
        resp = client.get(
            f"/api/farms/{farm_id}/notifications?severity=critical",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["severity"] == "critical"

    # --- Farm not found ---

    def test_list_nonexistent_farm(self, client, admin_headers):
        """GET for missing farm returns 404."""
        resp = client.get(
            "/api/farms/9999/notifications", headers=admin_headers
        )
        assert resp.status_code == 404
