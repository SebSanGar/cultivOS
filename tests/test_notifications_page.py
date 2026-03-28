"""Tests for /notificaciones — notification history page."""


class TestNotificationsPage:
    """Notification history page serves and contains expected elements."""

    def test_notificaciones_route_returns_200(self, client):
        resp = client.get("/notificaciones")
        assert resp.status_code == 200

    def test_notificaciones_returns_html(self, client):
        resp = client.get("/notificaciones")
        assert "text/html" in resp.headers.get("content-type", "")

    def test_page_contains_title(self, client):
        resp = client.get("/notificaciones")
        assert "Historial de Notificaciones" in resp.text

    def test_page_contains_filter_controls(self, client):
        resp = client.get("/notificaciones")
        body = resp.text
        assert "notif-filter-severity" in body
        assert "notif-filter-type" in body

    def test_page_contains_notification_list(self, client):
        resp = client.get("/notificaciones")
        assert "notif-list" in body if (body := resp.text) else False

    def test_page_contains_summary_strip(self, client):
        resp = client.get("/notificaciones")
        body = resp.text
        assert "notif-total" in body
        assert "notif-pending" in body
        assert "notif-critical" in body

    def test_page_loads_notifications_js(self, client):
        resp = client.get("/notificaciones")
        assert "notifications.js" in resp.text

    def test_page_has_nav_with_links(self, client):
        resp = client.get("/notificaciones")
        body = resp.text
        assert 'href="/"' in body
        assert 'href="/intel"' in body
        assert 'href="/notificaciones"' in body

    def test_notifications_js_accessible(self, client):
        resp = client.get("/notifications.js")
        assert resp.status_code == 200

    def test_notifications_js_has_fetch_logic(self, client):
        resp = client.get("/notifications.js")
        js = resp.text
        assert "fetchJSON" in js
        assert "/api/farms" in js

    def test_notifications_js_has_acknowledge(self, client):
        resp = client.get("/notifications.js")
        js = resp.text
        assert "acknowledge" in js

    def test_notifications_js_has_severity_filter(self, client):
        resp = client.get("/notifications.js")
        js = resp.text
        assert "severity" in js

    def test_notifications_js_handles_empty_state(self, client):
        resp = client.get("/notifications.js")
        js = resp.text
        assert "Sin notificaciones" in js or "notif-empty" in js

    def test_page_has_acknowledge_button_markup(self, client):
        resp = client.get("/notifications.js")
        js = resp.text
        assert "Reconocer" in js


class TestNotificationsAPI:
    """Notification API integration tests via the page."""

    def test_create_and_list_notifications(self, client, admin_headers):
        # Create a farm
        farm_resp = client.post(
            "/api/farms",
            json={"name": "Finca Notif Test", "location": "Jalisco"},
            headers=admin_headers,
        )
        farm_id = farm_resp.json()["id"]

        # Create a notification
        notif_resp = client.post(
            f"/api/farms/{farm_id}/notifications",
            json={
                "alert_type": "health",
                "message": "Campo 1 salud bajo 40",
                "severity": "critical",
            },
        )
        assert notif_resp.status_code == 201
        notif = notif_resp.json()
        assert notif["severity"] == "critical"
        assert notif["acknowledged"] is False

        # List notifications
        list_resp = client.get(f"/api/farms/{farm_id}/notifications")
        assert list_resp.status_code == 200
        items = list_resp.json()
        assert len(items) >= 1
        assert items[0]["message"] == "Campo 1 salud bajo 40"

    def test_acknowledge_notification(self, client, admin_headers):
        farm_resp = client.post(
            "/api/farms",
            json={"name": "Finca Ack Test", "location": "Jalisco"},
            headers=admin_headers,
        )
        farm_id = farm_resp.json()["id"]

        notif_resp = client.post(
            f"/api/farms/{farm_id}/notifications",
            json={
                "alert_type": "irrigation",
                "message": "Deficit de riego detectado",
                "severity": "warning",
            },
        )
        notif_id = notif_resp.json()["id"]

        ack_resp = client.post(
            f"/api/farms/{farm_id}/notifications/{notif_id}/acknowledge"
        )
        assert ack_resp.status_code == 200
        assert ack_resp.json()["acknowledged"] is True

    def test_filter_by_severity(self, client, admin_headers):
        farm_resp = client.post(
            "/api/farms",
            json={"name": "Finca Filter Test", "location": "Jalisco"},
            headers=admin_headers,
        )
        farm_id = farm_resp.json()["id"]

        # Create info and critical
        client.post(
            f"/api/farms/{farm_id}/notifications",
            json={"alert_type": "health", "message": "Info msg", "severity": "info"},
        )
        client.post(
            f"/api/farms/{farm_id}/notifications",
            json={
                "alert_type": "health",
                "message": "Critical msg",
                "severity": "critical",
            },
        )

        # Filter critical only
        resp = client.get(
            f"/api/farms/{farm_id}/notifications?severity=critical"
        )
        items = resp.json()
        assert all(n["severity"] == "critical" for n in items)
        assert len(items) >= 1
