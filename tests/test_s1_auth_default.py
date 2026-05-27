"""S1 — Auth migration: flip AUTH_ENABLED default to True.

Tests:
  - unauthenticated request to protected endpoint → 401
  - farmer accessing wrong farm_id → 403
  - production default (no env override) → auth enabled

These tests run against a fresh app with AUTH_ENABLED=true.
conftest.py sets AUTH_ENABLED=false so all other tests are unaffected.
"""

import os
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def auth_enabled_client(db):
    """TestClient with AUTH_ENABLED=true (isolated, cache-safe)."""
    # Save original value (conftest sets 'false')
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

    # Restore
    os.environ["AUTH_ENABLED"] = original
    get_settings.cache_clear()


@pytest.fixture
def farmer_token_wrong_farm(auth_enabled_client, db):
    """Create a farmer user scoped to farm 1, return headers. Farm 2 should be 403."""
    from cultivos.db.models import Farm, User
    from cultivos.auth import hash_password, create_access_token

    # Create two farms
    farm1 = Farm(name="Farmer Farm")
    farm2 = Farm(name="Other Farm")
    db.add(farm1)
    db.add(farm2)
    db.commit()

    # Create farmer user scoped to farm 1
    user = User(
        username="s1farmer",
        hashed_password=hash_password("pass123"),
        role="farmer",
        farm_id=farm1.id,
    )
    db.add(user)
    db.commit()

    token = create_access_token(user.id, user.username, user.role, user.farm_id)
    return {"Authorization": f"Bearer {token}", "farm1_id": farm1.id, "farm2_id": farm2.id}


class TestS1AuthDefault:
    """S1 acceptance tests — auth enforcement when AUTH_ENABLED=true."""

    def test_unauthenticated_request_returns_401(self, auth_enabled_client):
        """Any non-public endpoint without credentials → 401."""
        resp = auth_enabled_client.get("/api/farms")
        assert resp.status_code == 401, (
            f"Expected 401 for unauthenticated request, got {resp.status_code}: {resp.text}"
        )

    def test_unauthenticated_farm_scoped_returns_401(self, auth_enabled_client, db):
        """Farm-scoped route (with {farm_id} in prefix) without credentials → 401."""
        from cultivos.db.models import Farm
        farm = Farm(name="Test Farm S1")
        db.add(farm)
        db.commit()

        # /api/farms/{farm_id}/alerts has {farm_id} in prefix → require_farm_access applied
        resp = auth_enabled_client.get(f"/api/farms/{farm.id}/alerts")
        assert resp.status_code == 401, (
            f"Expected 401 for unauthenticated farm-scoped request, got {resp.status_code}"
        )

    def test_farmer_wrong_farm_returns_403(self, auth_enabled_client, farmer_token_wrong_farm):
        """Farmer token scoped to farm 1 accessing farm 2 alerts → 403."""
        headers = {
            "Authorization": farmer_token_wrong_farm["Authorization"]
        }
        farm2_id = farmer_token_wrong_farm["farm2_id"]

        # /api/farms/{farm_id}/alerts has {farm_id} in prefix → require_farm_access enforces farm
        resp = auth_enabled_client.get(f"/api/farms/{farm2_id}/alerts", headers=headers)
        assert resp.status_code == 403, (
            f"Expected 403 for farmer accessing wrong farm, got {resp.status_code}: {resp.text}"
        )

    def test_auth_enabled_is_production_default(self):
        """Config default for auth_enabled must be True (production-safe)."""
        import inspect
        from cultivos.config import Settings
        # Get default value of auth_enabled field
        fields = Settings.model_fields
        default = fields["auth_enabled"].default
        assert default is True, (
            f"auth_enabled default must be True (production-safe), got {default!r}. "
            "Set AUTH_ENABLED=false in .env / test env to disable in dev/tests."
        )
