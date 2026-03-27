"""Tests for disease/pest identification service."""

import pytest


@pytest.fixture(autouse=True)
def seed_diseases(db):
    """Seed disease data for tests."""
    from cultivos.db.seeds import seed_diseases as _seed
    _seed(db)


class TestIdentifyDisease:
    """Test symptom-based disease identification."""

    def test_identify_disease(self, client, admin_headers):
        """Given symptoms (yellow leaves, spots, wilting) returns ranked disease matches."""
        resp = client.post(
            "/api/knowledge/diseases/identify",
            json={"symptoms": ["hojas amarillas", "manchas", "marchitamiento"]},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Each match has name, confidence, symptoms_matched
        first = data[0]
        assert "name" in first
        assert "confidence" in first
        assert "symptoms_matched" in first
        # Results should be ranked by confidence (descending)
        confidences = [d["confidence"] for d in data]
        assert confidences == sorted(confidences, reverse=True)

    def test_disease_has_organic_treatment(self, client, admin_headers):
        """Every identified disease includes at least one organic/regenerative treatment."""
        resp = client.post(
            "/api/knowledge/diseases/identify",
            json={"symptoms": ["hojas amarillas"]},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        for disease in data:
            assert "treatments" in disease
            assert len(disease["treatments"]) > 0
            for treatment in disease["treatments"]:
                assert treatment.get("organic") is True

    def test_filter_by_crop(self, client, admin_headers):
        """?crop=maiz returns only maize-relevant diseases."""
        resp = client.get(
            "/api/knowledge/diseases?crop=maiz",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        for disease in data:
            assert "maiz" in disease["affected_crops"]

    def test_common_jalisco_diseases(self, client, admin_headers):
        """Seed data includes at least 6 diseases common to Jalisco crops."""
        resp = client.get(
            "/api/knowledge/diseases",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 6
        names = [d["name"] for d in data]
        # These 6 must be present
        expected = [
            "Roya del maiz",
            "Tizon tardio",
            "Fusarium",
            "Mosca blanca",
            "Gusano cogollero",
            "Mancha de asfalto",
        ]
        for disease_name in expected:
            assert disease_name in names, f"Missing expected disease: {disease_name}"
