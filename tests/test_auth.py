"""Tests for role-based access control."""

import os
import pytest
from datetime import datetime


@pytest.fixture(autouse=True)
def enable_auth():
    """Auth tests need AUTH_ENABLED=true to enforce role checks."""
    os.environ["AUTH_ENABLED"] = "true"
    from cultivos.config import get_settings
    get_settings.cache_clear()
    yield
    os.environ.pop("AUTH_ENABLED", None)
    get_settings.cache_clear()


@pytest.fixture
def seed_farm(db):
    """Create a farm for farmer-role tests."""
    from cultivos.db.models import Farm
    farm = Farm(name="Rancho Test", owner_name="Juan", location_lat=20.6, location_lon=-103.3,
                total_hectares=50, municipality="Zapopan", state="Jalisco", country="MX")
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@pytest.fixture
def seed_farm_other(db):
    """Create a second farm that the test farmer should NOT see."""
    from cultivos.db.models import Farm
    farm = Farm(name="Rancho Otro", owner_name="Pedro", location_lat=20.7, location_lon=-103.4,
                total_hectares=30, municipality="Tlaquepaque", state="Jalisco", country="MX")
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


def _register_user(client, username, password, role, farm_id=None):
    """Helper: register a user and return the response."""
    body = {"username": username, "password": password, "role": role}
    if farm_id is not None:
        body["farm_id"] = farm_id
    return client.post("/api/auth/register", json=body)


def _login_user(client, username, password):
    """Helper: login and return the JWT token."""
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


class TestAdminCanCreateFarm:
    def test_admin_can_create_farm(self, client, db):
        """role=admin -> POST /api/farms returns 201"""
        _register_user(client, "admin1", "secret123", "admin")
        token = _login_user(client, "admin1", "secret123")
        resp = client.post("/api/farms", json={
            "name": "Admin Farm", "owner_name": "Admin", "location_lat": 20.6,
            "location_lon": -103.3, "total_hectares": 100, "municipality": "Zapopan",
            "state": "Jalisco", "country": "MX"
        }, headers=_auth_header(token))
        assert resp.status_code == 201
        assert resp.json()["name"] == "Admin Farm"


class TestResearcherCannotCreateFarm:
    def test_researcher_cannot_create_farm(self, client, db):
        """role=researcher -> POST /api/farms returns 403"""
        _register_user(client, "researcher1", "secret123", "researcher")
        token = _login_user(client, "researcher1", "secret123")
        resp = client.post("/api/farms", json={
            "name": "Researcher Farm", "owner_name": "Dr. X", "location_lat": 20.6,
            "location_lon": -103.3, "total_hectares": 50, "municipality": "Zapopan",
            "state": "Jalisco", "country": "MX"
        }, headers=_auth_header(token))
        assert resp.status_code == 403


class TestResearcherCanReadFarms:
    def test_researcher_can_read_farms(self, client, db, seed_farm):
        """role=researcher -> GET /api/farms returns 200"""
        _register_user(client, "researcher2", "secret123", "researcher")
        token = _login_user(client, "researcher2", "secret123")
        resp = client.get("/api/farms", headers=_auth_header(token))
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)
        assert len(resp.json()["data"]) >= 1


class TestFarmerSeesOnlyOwnFarms:
    def test_farmer_sees_only_own_farms(self, client, db, seed_farm, seed_farm_other):
        """role=farmer, farm_id=1 -> GET /api/farms returns only their farm"""
        _register_user(client, "farmer1", "secret123", "farmer", farm_id=seed_farm.id)
        token = _login_user(client, "farmer1", "secret123")
        resp = client.get("/api/farms", headers=_auth_header(token))
        assert resp.status_code == 200
        farms = resp.json()["data"]
        assert len(farms) == 1
        assert farms[0]["id"] == seed_farm.id


class TestUnauthenticatedReturns401:
    def test_unauthenticated_returns_401(self, client, db):
        """no token -> 401"""
        resp = client.post("/api/farms", json={
            "name": "No Auth Farm", "owner_name": "Ghost", "location_lat": 20.6,
            "location_lon": -103.3, "total_hectares": 10, "municipality": "Zapopan",
            "state": "Jalisco", "country": "MX"
        })
        assert resp.status_code == 401
