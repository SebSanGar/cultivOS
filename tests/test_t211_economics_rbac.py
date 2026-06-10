"""T2.11 — RBAC gate on /api/farms/{farm_id}/economic-impact.

403 when AUTH_ENABLED=true + caller is farmer for a different farm.
200 for own farm, admin, researcher. 200 when auth disabled (default).
"""

import os
import pytest


@pytest.fixture
def _farm(db):
    from cultivos.db.models import Farm
    f = Farm(
        name="Rancho T211",
        owner_name="Juan",
        location_lat=20.6,
        location_lon=-103.3,
        total_hectares=10.0,
        municipality="Zapopan",
        state="Jalisco",
        country="MX",
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@pytest.fixture
def _other_farm(db):
    from cultivos.db.models import Farm
    f = Farm(
        name="Rancho Ajeno",
        owner_name="Pedro",
        location_lat=20.7,
        location_lon=-103.4,
        total_hectares=5.0,
        municipality="Tlaquepaque",
        state="Jalisco",
        country="MX",
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def _register_and_login(client, db, username, role, farm_id=None):
    from cultivos.auth import hash_password
    from cultivos.db.models import User as UserModel

    if role == "admin":
        user = UserModel(
            username=username,
            hashed_password=hash_password("pw123456"),
            role="admin",
            farm_id=farm_id,
        )
        db.add(user)
        db.commit()
    else:
        r = client.post(
            "/api/auth/register",
            json={"username": username, "password": "pw123456", "role": role, "farm_id": farm_id},
        )
        assert r.status_code == 201, f"register failed: {r.text}"
    resp = client.post("/api/auth/login", json={"username": username, "password": "pw123456"})
    assert resp.status_code == 200, f"login failed: {resp.text}"
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture(autouse=True)
def _reset_settings():
    yield
    os.environ.pop("AUTH_ENABLED", None)
    from cultivos.config import get_settings
    get_settings.cache_clear()


def _enable_auth():
    os.environ["AUTH_ENABLED"] = "true"
    from cultivos.config import get_settings
    get_settings.cache_clear()


class TestEconomicsRbac:
    def test_auth_disabled_allows_any_farm(self, client, _farm):
        """AUTH_ENABLED=false (default) — no token needed, 200."""
        resp = client.get(f"/api/farms/{_farm.id}/economic-impact")
        assert resp.status_code == 200

    def test_farmer_own_farm_200(self, client, db, _farm):
        """Farmer with matching farm_id → 200."""
        _enable_auth()
        headers = _register_and_login(client, db, "farmer_own", "farmer", farm_id=_farm.id)
        resp = client.get(f"/api/farms/{_farm.id}/economic-impact", headers=headers)
        assert resp.status_code == 200

    def test_farmer_other_farm_403(self, client, db, _farm, _other_farm):
        """Farmer with different farm_id → 403."""
        _enable_auth()
        headers = _register_and_login(client, db, "farmer_other", "farmer", farm_id=_other_farm.id)
        resp = client.get(f"/api/farms/{_farm.id}/economic-impact", headers=headers)
        assert resp.status_code == 403

    def test_admin_any_farm_200(self, client, db, _farm):
        """Admin → can access any farm's economics, 200."""
        _enable_auth()
        headers = _register_and_login(client, db, "admin_t211", "admin")
        resp = client.get(f"/api/farms/{_farm.id}/economic-impact", headers=headers)
        assert resp.status_code == 200

    def test_researcher_any_farm_200(self, client, db, _farm):
        """Researcher → can access any farm's economics, 200."""
        _enable_auth()
        headers = _register_and_login(client, db, "researcher_t211", "researcher")
        resp = client.get(f"/api/farms/{_farm.id}/economic-impact", headers=headers)
        assert resp.status_code == 200

    def test_unauthenticated_with_auth_enabled_401(self, client, _farm):
        """No token + auth enabled → 401."""
        _enable_auth()
        resp = client.get(f"/api/farms/{_farm.id}/economic-impact")
        assert resp.status_code == 401

    def test_403_detail_message(self, client, db, _farm, _other_farm):
        """403 response body includes 'Forbidden' or 'farm access denied'."""
        _enable_auth()
        headers = _register_and_login(client, db, "farmer_detail", "farmer", farm_id=_other_farm.id)
        resp = client.get(f"/api/farms/{_farm.id}/economic-impact", headers=headers)
        assert resp.status_code == 403
        body = resp.json()
        # App wraps errors as {"error": {"message": ...}} OR FastAPI {"detail": ...}
        msg = (
            (body.get("error") or {}).get("message")
            or body.get("detail")
            or ""
        ).lower()
        assert "forbidden" in msg or "farm" in msg or "denied" in msg
