"""Tests for the ancestral farming methods knowledge base."""

import pytest


@pytest.fixture(autouse=True)
def seed_ancestral(db):
    """Seed ancestral method data into test DB."""
    from cultivos.db.seeds import seed_ancestral_methods
    seed_ancestral_methods(db)


class TestAncestralMethods:
    """GET /api/knowledge/ancestral — traditional Mexican/LATAM agriculture practices."""

    def test_list_ancestral_methods(self, client):
        """GET /api/knowledge/ancestral returns methods with name, region, description, crops."""
        resp = client.get("/api/knowledge/ancestral")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        required = {"name", "region", "description_es", "crops", "practice_type"}
        for method in data:
            for field in required:
                assert field in method, f"Missing '{field}' in method '{method.get('name', '?')}'"

    def test_filter_by_region(self, client):
        """?region=jalisco returns only Jalisco methods."""
        resp = client.get("/api/knowledge/ancestral?region=jalisco")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        for method in data:
            assert "jalisco" in method["region"].lower(), (
                f"Method '{method['name']}' region '{method['region']}' does not match 'jalisco'"
            )

    def test_filter_by_practice_type(self, client):
        """?type=soil_management returns milpa, chinampas, etc."""
        resp = client.get("/api/knowledge/ancestral?type=soil_management")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        for method in data:
            assert method["practice_type"] == "soil_management"

    def test_seed_data_loads(self, client):
        """At least 8 methods seeded (milpa, chinampa, terrazas, etc.)."""
        resp = client.get("/api/knowledge/ancestral")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 8, f"Expected at least 8 seed methods, got {len(data)}"
        names_lower = [m["name"].lower() for m in data]
        expected = ["milpa", "chinampa"]
        for name in expected:
            assert any(name in n for n in names_lower), f"'{name}' not found in ancestral methods"
