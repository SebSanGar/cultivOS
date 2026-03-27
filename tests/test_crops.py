"""Tests for the crop type knowledge base."""

import pytest


@pytest.fixture(autouse=True)
def seed_crops(db):
    """Seed crop type data into test DB."""
    from cultivos.db.seeds import seed_crops
    seed_crops(db)


class TestCropTypes:
    """GET /api/knowledge/crops — structured crop info with growing requirements."""

    def test_list_crops(self, client):
        """GET /api/knowledge/crops returns crops with name, family, growing_season, water_needs."""
        resp = client.get("/api/knowledge/crops")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        required = {"name", "family", "growing_season", "water_needs"}
        for crop in data:
            for field in required:
                assert field in crop, f"Missing '{field}' in crop '{crop.get('name', '?')}'"

    def test_filter_by_region(self, client):
        """?region=jalisco returns Jalisco-suitable crops."""
        resp = client.get("/api/knowledge/crops?region=jalisco")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        for crop in data:
            assert "jalisco" in [r.lower() for r in crop["regions"]], (
                f"Crop '{crop['name']}' regions {crop['regions']} does not include 'jalisco'"
            )

    def test_crop_has_companions(self, client):
        """Each crop lists companion plants (for intercropping)."""
        resp = client.get("/api/knowledge/crops")
        assert resp.status_code == 200
        data = resp.json()
        for crop in data:
            assert "companions" in crop, f"Missing 'companions' in crop '{crop['name']}'"
            assert isinstance(crop["companions"], list), (
                f"companions should be a list for crop '{crop['name']}'"
            )
            assert len(crop["companions"]) > 0, (
                f"Crop '{crop['name']}' should have at least one companion plant"
            )

    def test_seed_data(self, client):
        """At least 10 crops seeded (maiz, frijol, calabaza, chile, jitomate, aguacate, agave, sorgo, garbanzo, cana de azucar)."""
        resp = client.get("/api/knowledge/crops")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 10, f"Expected at least 10 seed crops, got {len(data)}"
        names_lower = [c["name"].lower() for c in data]
        expected = ["maiz", "frijol", "calabaza", "chile", "jitomate",
                     "aguacate", "agave", "sorgo", "garbanzo"]
        for name in expected:
            assert any(name in n for n in names_lower), f"'{name}' not found in crop types"
