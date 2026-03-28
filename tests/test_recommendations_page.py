"""Tests for /recomendaciones — farm recommendations page."""


class TestRecommendationsPage:
    """Recommendations page serves and contains expected elements."""

    def test_recomendaciones_route_returns_200(self, client):
        resp = client.get("/recomendaciones")
        assert resp.status_code == 200

    def test_recomendaciones_returns_html(self, client):
        resp = client.get("/recomendaciones")
        assert "text/html" in resp.headers.get("content-type", "")

    def test_page_contains_title(self, client):
        resp = client.get("/recomendaciones")
        assert "Recomendaciones" in resp.text

    def test_page_contains_farm_selector(self, client):
        resp = client.get("/recomendaciones")
        assert "recs-farm-select" in resp.text

    def test_page_contains_stats_strip(self, client):
        resp = client.get("/recomendaciones")
        body = resp.text
        assert "recs-total" in body
        assert "recs-urgent" in body
        assert "recs-organic" in body

    def test_page_contains_cards_container(self, client):
        resp = client.get("/recomendaciones")
        assert "recs-cards" in body if (body := resp.text) else False

    def test_page_loads_recommendations_js(self, client):
        resp = client.get("/recomendaciones")
        assert "recommendations.js" in resp.text

    def test_page_has_nav_with_links(self, client):
        resp = client.get("/recomendaciones")
        body = resp.text
        assert 'href="/"' in body
        assert 'href="/intel"' in body
        assert 'href="/recomendaciones"' in body

    def test_page_contains_region_info_container(self, client):
        resp = client.get("/recomendaciones")
        assert "recs-region-info" in resp.text


class TestRecommendationsJS:
    """Recommendations JS contains rendering and fetch logic."""

    def test_recommendations_js_accessible(self, client):
        resp = client.get("/recommendations.js")
        assert resp.status_code == 200

    def test_js_has_fetch_logic(self, client):
        resp = client.get("/recommendations.js")
        js = resp.text
        assert "fetchJSON" in js
        assert "/api/farms" in js
        assert "/recommendations" in js

    def test_js_renders_urgency_badges(self, client):
        resp = client.get("/recommendations.js")
        js = resp.text
        assert "urgencia" in js

    def test_js_renders_organic_badges(self, client):
        resp = client.get("/recommendations.js")
        js = resp.text
        assert "organic" in js.lower() or "Organico" in js or "organico" in js

    def test_js_formats_mxn_cost(self, client):
        resp = client.get("/recommendations.js")
        js = resp.text
        assert "MXN" in js
        assert "toLocaleString" in js or "costo" in js

    def test_js_handles_empty_state(self, client):
        resp = client.get("/recommendations.js")
        js = resp.text
        assert "Sin recomendaciones" in js or "recs-empty" in js

    def test_js_renders_treatment_details(self, client):
        resp = client.get("/recommendations.js")
        js = resp.text
        assert "tratamiento" in js
        assert "problema" in js
        assert "causa_probable" in js

    def test_js_renders_ancestral_method(self, client):
        resp = client.get("/recommendations.js")
        js = resp.text
        assert "metodo_ancestral" in js

    def test_js_renders_regional_context(self, client):
        resp = client.get("/recommendations.js")
        js = resp.text
        assert "contexto_regional" in js

    def test_js_updates_stats(self, client):
        resp = client.get("/recommendations.js")
        js = resp.text
        assert "recs-total" in js
        assert "recs-urgent" in js


class TestRecommendationsAPIIntegration:
    """Recommendations API via page context."""

    def test_recommendations_endpoint_for_seeded_farm(self, client, admin_headers, db):
        from cultivos.db.models import NDVIResult

        farm_resp = client.post(
            "/api/farms",
            json={"name": "Finca Rec Test", "location": "Jalisco"},
            headers=admin_headers,
        )
        assert farm_resp.status_code == 201
        farm_id = farm_resp.json()["id"]

        field_resp = client.post(
            f"/api/farms/{farm_id}/fields",
            json={"name": "Parcela Maiz", "crop_type": "maize", "hectares": 10},
        )
        assert field_resp.status_code == 201
        field_id = field_resp.json()["id"]

        # Seed NDVI data so health can be computed
        ndvi = NDVIResult(
            field_id=field_id, ndvi_mean=0.35, ndvi_min=0.1, ndvi_max=0.6,
            ndvi_std=0.08, pixels_total=1000, stress_pct=45.0, zones=[],
        )
        db.add(ndvi)
        db.commit()

        # Compute health score from seeded data
        health_resp = client.post(f"/api/farms/{farm_id}/fields/{field_id}/health")
        assert health_resp.status_code == 201

        rec_resp = client.get(f"/api/farms/{farm_id}/recommendations")
        assert rec_resp.status_code == 200
        data = rec_resp.json()
        assert "recommendations" in data
        assert "region" in data
        assert len(data["recommendations"]) > 0
        rec = data["recommendations"][0]
        assert "problema" in rec
        assert "tratamiento" in rec
        assert "urgencia" in rec
        assert "costo_estimado_mxn" in rec
