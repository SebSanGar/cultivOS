"""M1 — Public minimal farm list for pre-auth registration dropdown.

Tests that GET /api/farms/public returns {id, name, municipality} without auth,
and does NOT leak sensitive fields (health, hectares, owner, etc.).
Also verifies /api/farms still requires auth when AUTH_ENABLED=true.
"""

import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def auth_enabled_client(db):
    """TestClient with AUTH_ENABLED=true."""
    original = os.environ.get("AUTH_ENABLED", "")
    os.environ["AUTH_ENABLED"] = "true"

    from cultivos.config import get_settings
    get_settings.cache_clear()

    from cultivos.app import create_app
    from cultivos.db.session import get_db

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    os.environ["AUTH_ENABLED"] = original
    get_settings.cache_clear()


def _seed_farm(db):
    from cultivos.db.models import Farm
    farm = Farm(
        name="Rancho Test",
        owner_name="Don Manuel",
        municipality="Zapopan",
        total_hectares=50.0,
        state="Jalisco",
    )
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


class TestFarmsPublic:
    """GET /api/farms/public — unauthenticated, minimal shape."""

    def test_returns_200_without_auth(self, auth_enabled_client, db):
        _seed_farm(db)
        resp = auth_enabled_client.get("/api/farms/public")
        assert resp.status_code == 200

    def test_returns_list_of_farms(self, auth_enabled_client, db):
        _seed_farm(db)
        data = auth_enabled_client.get("/api/farms/public").json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_each_farm_has_id_name_municipality(self, auth_enabled_client, db):
        _seed_farm(db)
        data = auth_enabled_client.get("/api/farms/public").json()
        farm = data[0]
        assert "id" in farm
        assert "name" in farm
        assert "municipality" in farm

    def test_does_not_leak_sensitive_fields(self, auth_enabled_client, db):
        _seed_farm(db)
        data = auth_enabled_client.get("/api/farms/public").json()
        farm = data[0]
        for forbidden in ("owner_name", "total_hectares", "location_lat",
                          "location_lon", "created_at", "cooperative_id"):
            assert forbidden not in farm, f"Leaked sensitive field: {forbidden}"

    def test_ordered_by_name(self, auth_enabled_client, db):
        from cultivos.db.models import Farm
        db.add(Farm(name="Zeta Farm", municipality="Lagos"))
        db.add(Farm(name="Alpha Farm", municipality="Arandas"))
        db.commit()
        data = auth_enabled_client.get("/api/farms/public").json()
        names = [f["name"] for f in data]
        assert names == sorted(names)

    def test_empty_list_when_no_farms(self, auth_enabled_client):
        data = auth_enabled_client.get("/api/farms/public").json()
        assert data == []

    def test_private_farms_endpoint_still_401s(self, auth_enabled_client, db):
        """Gate: /api/farms must still require auth."""
        _seed_farm(db)
        resp = auth_enabled_client.get("/api/farms")
        assert resp.status_code == 401
