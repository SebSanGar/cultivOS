"""Tests for disease encyclopedia and identify form on the knowledge page."""

import pytest


@pytest.fixture(autouse=True)
def seed_diseases(db):
    """Seed disease data for tests."""
    from cultivos.db.seeds import seed_diseases as _seed
    _seed(db)


class TestKnowledgeDiseaseHTML:
    """Knowledge page has an Enfermedades section with correct containers."""

    def test_disease_section_exists(self, client):
        """Knowledge page has the disease section with correct ID."""
        resp = client.get("/conocimiento")
        assert resp.status_code == 200
        html = resp.text
        assert 'id="disease-cards"' in html

    def test_disease_section_spanish_title(self, client):
        """Disease section has Spanish title."""
        resp = client.get("/conocimiento")
        html = resp.text
        assert "Enfermedades" in html

    def test_identify_form_exists(self, client):
        """Knowledge page has a symptom identification form."""
        resp = client.get("/conocimiento")
        html = resp.text
        assert 'id="identify-form"' in html
        assert 'id="identify-results"' in html


class TestKnowledgeDiseaseJS:
    """knowledge.js renders disease cards and has identify form logic."""

    def test_js_has_disease_rendering(self, client):
        """knowledge.js includes disease rendering function."""
        resp = client.get("/knowledge.js")
        assert resp.status_code == 200
        js = resp.text
        assert "renderDiseases" in js

    def test_js_fetches_diseases(self, client):
        """knowledge.js fetches from /api/knowledge/diseases."""
        resp = client.get("/knowledge.js")
        js = resp.text
        assert "/api/knowledge/diseases" in js

    def test_js_has_identify_handler(self, client):
        """knowledge.js handles identify form submission."""
        resp = client.get("/knowledge.js")
        js = resp.text
        assert "identify" in js.lower()
        assert "/api/knowledge/diseases/identify" in js


class TestKnowledgeDiseaseAPI:
    """Disease list endpoint returns correct data for knowledge page."""

    def test_list_diseases(self, client, admin_headers):
        """GET /api/knowledge/diseases returns seeded diseases."""
        resp = client.get("/api/knowledge/diseases", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 6
        first = data[0]
        assert "name" in first
        assert "symptoms" in first
        assert "severity" in first

    def test_filter_by_crop(self, client, admin_headers):
        """GET /api/knowledge/diseases?crop=maiz filters correctly."""
        resp = client.get("/api/knowledge/diseases?crop=maiz", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        for d in data:
            assert "maiz" in [c.lower() for c in d["affected_crops"]]

    def test_identify_symptoms(self, client, admin_headers):
        """POST /api/knowledge/diseases/identify returns ranked matches."""
        resp = client.post(
            "/api/knowledge/diseases/identify",
            json={"symptoms": ["hojas amarillas", "manchas"]},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        confidences = [d["confidence"] for d in data]
        assert confidences == sorted(confidences, reverse=True)
