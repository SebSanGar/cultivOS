"""Tests for the farm heatmap frontend integration."""


def test_dashboard_contains_heatmap_container(client):
    """Dashboard HTML includes a heatmap container element."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert 'id="heatmap-container"' in resp.text


def test_dashboard_js_has_heatmap_render(client):
    """Dashboard JS includes heatmap rendering function."""
    resp = client.get("/app.js")
    assert resp.status_code == 200
    js = resp.text
    assert "renderHeatmap" in js


def test_dashboard_css_has_heatmap_styles(client):
    """Dashboard CSS includes heatmap styling."""
    resp = client.get("/styles.css")
    assert resp.status_code == 200
    css = resp.text
    assert "heatmap" in css


def test_heatmap_api_returns_color_data(client, db, admin_headers):
    """Heatmap endpoint returns health_score that frontend uses for coloring."""
    from cultivos.db.models import Farm, Field, HealthScore

    farm = Farm(name="Color Farm", state="Jalisco", country="MX")
    db.add(farm)
    db.commit()
    db.refresh(farm)

    # Field with high health (green)
    f1 = Field(farm_id=farm.id, name="Green Field", crop_type="maiz",
               boundary_coordinates=[[-103.35, 20.65], [-103.34, 20.65],
                                     [-103.34, 20.66], [-103.35, 20.66]])
    # Field with low health (red)
    f2 = Field(farm_id=farm.id, name="Red Field", crop_type="agave",
               boundary_coordinates=[[-103.33, 20.65], [-103.32, 20.65],
                                     [-103.32, 20.66], [-103.33, 20.66]])
    db.add_all([f1, f2])
    db.commit()
    db.refresh(f1)
    db.refresh(f2)

    db.add(HealthScore(field_id=f1.id, score=85.0, trend="improving", sources=["ndvi"]))
    db.add(HealthScore(field_id=f2.id, score=30.0, trend="declining", sources=["ndvi"]))
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/heatmap", headers=admin_headers)
    assert resp.status_code == 200
    fields = resp.json()["fields"]
    assert len(fields) == 2

    green = next(f for f in fields if f["field_name"] == "Green Field")
    red = next(f for f in fields if f["field_name"] == "Red Field")
    # Frontend will use these scores to color: >75 green, 50-75 yellow, <50 red
    assert green["health_score"] == 85.0
    assert red["health_score"] == 30.0
    # Both have centroids for map positioning
    assert green["centroid_lat"] is not None
    assert red["centroid_lat"] is not None


def test_heatmap_js_has_click_navigation(client):
    """Heatmap JS includes click handler that navigates to field detail."""
    resp = client.get("/app.js")
    assert resp.status_code == 200
    js = resp.text
    # The heatmap should link to the field detail page on click
    assert "/campo" in js
