"""Tests for region profile endpoint — GET /api/regions/{region}."""


def test_get_jalisco_profile(client):
    """Jalisco region returns a complete profile."""
    resp = client.get("/api/regions/jalisco_mx")
    assert resp.status_code == 200
    data = resp.json()
    assert data["region_name"] == "jalisco"
    assert data["climate_zone"] == "tropical_subtropical"
    assert data["currency"] == "MXN"
    assert "maiz" in data["key_crops"]
    assert len(data["key_crops"]) >= 3
    assert data["soil_type"]
    assert data["growing_season"]
    assert data["seasonal_notes"]


def test_get_ontario_profile(client):
    """Ontario region returns a complete profile with CAD currency."""
    resp = client.get("/api/regions/ontario_ca")
    assert resp.status_code == 200
    data = resp.json()
    assert data["region_name"] == "ontario"
    assert data["currency"] == "CAD"
    assert "corn" in data["key_crops"]
    assert data["climate_zone"] == "temperate_continental"


def test_unknown_region_returns_404(client):
    """Unknown region key returns 404, not a generic fallback."""
    resp = client.get("/api/regions/atlantis_xx")
    assert resp.status_code == 404


def test_region_key_case_insensitive(client):
    """Region key lookup is case-insensitive."""
    resp = client.get("/api/regions/JALISCO_MX")
    assert resp.status_code == 200
    assert resp.json()["region_name"] == "jalisco"


def test_list_regions(client):
    """GET /api/regions returns all known region keys."""
    resp = client.get("/api/regions")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    keys = {item["key"] for item in data}
    assert "jalisco_mx" in keys
    assert "ontario_ca" in keys
    # Each list entry has key + region_name + currency for quick display
    for item in data:
        assert "key" in item
        assert "region_name" in item
        assert "currency" in item
