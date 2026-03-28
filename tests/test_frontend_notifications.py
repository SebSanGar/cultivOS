"""Tests for the notification panel on the farm dashboard."""


def test_dashboard_contains_notification_container(client):
    """Dashboard HTML includes a notification panel element."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert 'id="notification-panel"' in resp.text


def test_dashboard_js_has_notification_render(client):
    """Dashboard JS includes notification rendering and acknowledge logic."""
    resp = client.get("/app.js")
    assert resp.status_code == 200
    js = resp.text
    assert "renderNotifications" in js
    assert "acknowledgeNotification" in js


def test_dashboard_css_has_notification_styles(client):
    """Dashboard CSS includes notification styling with severity colors."""
    resp = client.get("/styles.css")
    assert resp.status_code == 200
    css = resp.text
    assert "notification" in css
    assert "severity" in css


def test_notification_api_returns_severity_data(client, db, admin_headers):
    """Notification endpoint returns severity field used for color-coding."""
    from cultivos.db.models import AlertLog, Farm

    farm = Farm(name="Notify Farm", state="Jalisco", country="MX")
    db.add(farm)
    db.commit()
    db.refresh(farm)

    db.add(AlertLog(farm_id=farm.id, alert_type="health",
                    message="Salud baja en campo norte", severity="alta"))
    db.add(AlertLog(farm_id=farm.id, alert_type="irrigation",
                    message="Riego necesario", severity="media"))
    db.add(AlertLog(farm_id=farm.id, alert_type="recommendation",
                    message="Todo bien", severity="baja"))
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/notifications",
                      headers=admin_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 3

    severities = {n["severity"] for n in items}
    assert severities == {"alta", "media", "baja"}
    # All should have acknowledged=False by default
    assert all(not n["acknowledged"] for n in items)


def test_notification_acknowledge_updates(client, db, admin_headers):
    """Acknowledging a notification sets acknowledged=True."""
    from cultivos.db.models import AlertLog, Farm

    farm = Farm(name="Ack Farm", state="Jalisco", country="MX")
    db.add(farm)
    db.commit()
    db.refresh(farm)

    log = AlertLog(farm_id=farm.id, alert_type="health",
                   message="Alerta de salud", severity="alta")
    db.add(log)
    db.commit()
    db.refresh(log)

    resp = client.post(
        f"/api/farms/{farm.id}/notifications/{log.id}/acknowledge",
        headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["acknowledged"] is True

    # Verify it persists
    resp2 = client.get(f"/api/farms/{farm.id}/notifications",
                       headers=admin_headers)
    assert resp2.json()[0]["acknowledged"] is True


def test_notification_js_loads_on_farm_select(client):
    """JS loads notifications when a farm is selected."""
    resp = client.get("/app.js")
    assert resp.status_code == 200
    js = resp.text
    assert "loadNotifications" in js
    assert "/notifications" in js
