"""Tests for /vuelos — drone flight log page."""


class TestFlightsPage:
    """Flight log page serves and contains expected elements."""

    def test_vuelos_route_returns_200(self, client):
        resp = client.get("/vuelos")
        assert resp.status_code == 200

    def test_vuelos_returns_html(self, client):
        resp = client.get("/vuelos")
        assert "text/html" in resp.headers.get("content-type", "")

    def test_page_contains_title(self, client):
        resp = client.get("/vuelos")
        assert "Registro de Vuelos" in resp.text

    def test_page_contains_stats_strip(self, client):
        resp = client.get("/vuelos")
        body = resp.text
        assert "flights-total" in body
        assert "flights-hours" in body
        assert "flights-hectares" in body

    def test_page_contains_flight_table(self, client):
        resp = client.get("/vuelos")
        assert "flights-table-body" in body if (body := resp.text) else False

    def test_page_loads_flights_js(self, client):
        resp = client.get("/vuelos")
        assert "flights.js" in resp.text

    def test_page_has_nav_with_links(self, client):
        resp = client.get("/vuelos")
        body = resp.text
        assert 'href="/"' in body
        assert 'href="/intel"' in body
        assert 'href="/vuelos"' in body

    def test_flights_js_accessible(self, client):
        resp = client.get("/flights.js")
        assert resp.status_code == 200

    def test_flights_js_has_fetch_logic(self, client):
        resp = client.get("/flights.js")
        js = resp.text
        assert "fetchJSON" in js
        assert "/api/farms" in js

    def test_flights_js_has_stats_update(self, client):
        resp = client.get("/flights.js")
        js = resp.text
        assert "flights-total" in js
        assert "flights-hours" in js

    def test_flights_js_handles_empty_state(self, client):
        resp = client.get("/flights.js")
        js = resp.text
        assert "Sin vuelos" in js or "flights-empty" in js

    def test_flights_js_has_drone_type_labels(self, client):
        resp = client.get("/flights.js")
        js = resp.text
        assert "mavic_multispectral" in js or "Multispectral" in js

    def test_flights_js_has_sort_logic(self, client):
        resp = client.get("/flights.js")
        js = resp.text
        assert "sort" in js


class TestFlightsAPIIntegration:
    """Flight API integration via the page."""

    def test_create_and_list_flights(self, client, admin_headers):
        farm_resp = client.post(
            "/api/farms",
            json={"name": "Finca Vuelo Test", "location": "Jalisco"},
            headers=admin_headers,
        )
        farm_id = farm_resp.json()["id"]

        field_resp = client.post(
            f"/api/farms/{farm_id}/fields",
            json={"name": "Parcela A", "crop_type": "maize", "hectares": 10},
        )
        field_id = field_resp.json()["id"]

        flight_resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/flights",
            json={
                "drone_type": "mavic_multispectral",
                "mission_type": "health_scan",
                "flight_date": "2026-03-01T10:00:00",
                "duration_minutes": 25.0,
                "altitude_m": 80.0,
                "images_count": 120,
                "coverage_pct": 85.0,
            },
        )
        assert flight_resp.status_code == 201

        list_resp = client.get(f"/api/farms/{farm_id}/fields/{field_id}/flights")
        assert list_resp.status_code == 200
        items = list_resp.json()
        assert len(items) >= 1
        assert items[0]["drone_type"] == "mavic_multispectral"

    def test_flight_stats(self, client, admin_headers):
        farm_resp = client.post(
            "/api/farms",
            json={"name": "Finca Stats Test", "location": "Jalisco"},
            headers=admin_headers,
        )
        farm_id = farm_resp.json()["id"]

        field_resp = client.post(
            f"/api/farms/{farm_id}/fields",
            json={"name": "Parcela B", "crop_type": "agave", "hectares": 5},
        )
        field_id = field_resp.json()["id"]

        client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/flights",
            json={
                "drone_type": "mavic_thermal",
                "mission_type": "thermal_check",
                "flight_date": "2026-02-15T14:00:00",
                "duration_minutes": 30.0,
                "altitude_m": 60.0,
                "images_count": 80,
                "coverage_pct": 50.0,
            },
        )

        stats_resp = client.get(f"/api/farms/{farm_id}/fields/{field_id}/flights/stats")
        assert stats_resp.status_code == 200
        stats = stats_resp.json()
        assert stats["total_flights"] == 1
        assert stats["total_hours"] == 0.5
        assert stats["total_area_covered_ha"] == 50.0
        assert stats["drone_breakdown"]["mavic_thermal"] == 1
