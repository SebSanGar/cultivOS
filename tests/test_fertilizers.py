"""Tests for the natural fertilizer knowledge base."""

import pytest


@pytest.fixture(autouse=True)
def seed_fertilizers(db):
    """Seed fertilizer data into test DB."""
    from cultivos.db.seeds import seed_fertilizers
    seed_fertilizers(db)


class TestFertilizerKnowledgeBase:
    """GET /api/knowledge/fertilizers — queryable organic fertilizer methods."""

    def test_list_fertilizers_returns_all(self, client):
        """GET /api/knowledge/fertilizers returns list including key organic methods."""
        resp = client.get("/api/knowledge/fertilizers")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        names = [f["name"] for f in data]
        for method in ["compost", "manure", "vermicompost", "biochar", "aquaculture"]:
            assert any(method in n.lower() for n in names), f"{method} not found in fertilizer list"

    def test_filter_by_crop_type(self, client):
        """GET /api/knowledge/fertilizers?crop=maiz returns only methods suitable for corn."""
        resp = client.get("/api/knowledge/fertilizers?crop=maiz")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        for fert in data:
            assert "maiz" in fert["suitable_crops"]

    def test_fertilizer_has_required_fields(self, client):
        """Each fertilizer entry has required fields."""
        resp = client.get("/api/knowledge/fertilizers")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        required = {"name", "description_es", "application_method", "cost_per_ha_mxn", "nutrient_profile"}
        for fert in data:
            for field in required:
                assert field in fert, f"Missing field '{field}' in fertilizer '{fert.get('name', '?')}'"

    def test_seed_data_loads(self, client):
        """On startup, DB has at least 8 fertilizer methods pre-loaded."""
        resp = client.get("/api/knowledge/fertilizers")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 8, f"Expected at least 8 seed fertilizers, got {len(data)}"
