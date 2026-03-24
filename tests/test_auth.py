"""Tests for PIN-based authentication and user management."""

from cultivos.db.models import Location, User
from cultivos.services.auth_service import hash_pin


def _create_user(db, role="staff", pin="1234"):
    """Helper: create a Location + User with hashed PIN."""
    loc = Location(name="Test Kitchen", timezone="America/Toronto")
    db.add(loc)
    db.commit()
    db.refresh(loc)
    user = User(name=f"Test {role.title()}", role=role, pin_hash=hash_pin(pin), location_id=loc.id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, loc


def _login(client, user_id, pin="1234"):
    """Helper: login and return auth header dict."""
    res = client.post("/api/auth/login", json={"user_id": user_id, "pin": pin})
    assert res.status_code == 200, f"Login failed: {res.json()}"
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_success(self, client, db):
        user, _ = _create_user(db, pin="5678")
        res = client.post("/api/auth/login", json={"user_id": user.id, "pin": "5678"})
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["id"] == user.id
        assert data["user"]["role"] == "staff"

    def test_wrong_pin(self, client, db):
        user, _ = _create_user(db, pin="1234")
        res = client.post("/api/auth/login", json={"user_id": user.id, "pin": "9999"})
        assert res.status_code == 401

    def test_nonexistent_user(self, client, db):
        res = client.post("/api/auth/login", json={"user_id": 99999, "pin": "1234"})
        assert res.status_code == 401

    def test_pin_too_short(self, client, db):
        res = client.post("/api/auth/login", json={"user_id": 1, "pin": "12"})
        assert res.status_code == 422

    def test_pin_non_numeric(self, client, db):
        res = client.post("/api/auth/login", json={"user_id": 1, "pin": "abcd"})
        assert res.status_code == 422


# ---------------------------------------------------------------------------
# /auth/me
# ---------------------------------------------------------------------------

class TestGetMe:
    def test_authenticated(self, client, db):
        user, _ = _create_user(db, role="manager")
        headers = _login(client, user.id)
        res = client.get("/api/auth/me", headers=headers)
        assert res.status_code == 200
        assert res.json()["name"] == "Test Manager"
        assert res.json()["role"] == "manager"

    def test_no_token(self, client, db):
        res = client.get("/api/auth/me")
        assert res.status_code in (401, 403)  # HTTPBearer rejects missing credentials

    def test_invalid_token(self, client, db):
        res = client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"})
        assert res.status_code == 401


# ---------------------------------------------------------------------------
# PIN update
# ---------------------------------------------------------------------------

class TestPinUpdate:
    def test_success(self, client, db):
        user, _ = _create_user(db, pin="1234")
        headers = _login(client, user.id, "1234")
        res = client.put("/api/auth/pin", json={"current_pin": "1234", "new_pin": "5678"}, headers=headers)
        assert res.status_code == 200
        # Login with new PIN
        res2 = client.post("/api/auth/login", json={"user_id": user.id, "pin": "5678"})
        assert res2.status_code == 200

    def test_wrong_current_pin(self, client, db):
        user, _ = _create_user(db, pin="1234")
        headers = _login(client, user.id, "1234")
        res = client.put("/api/auth/pin", json={"current_pin": "0000", "new_pin": "5678"}, headers=headers)
        assert res.status_code == 401


# ---------------------------------------------------------------------------
# User CRUD (role-gated)
# ---------------------------------------------------------------------------

class TestUserManagement:
    def test_create_user_as_admin(self, client, db):
        admin, loc = _create_user(db, role="admin", pin="0000")
        headers = _login(client, admin.id, "0000")
        res = client.post("/api/users", json={
            "name": "New Cook",
            "role": "staff",
            "pin": "4444",
            "location_id": loc.id,
        }, headers=headers)
        assert res.status_code == 201
        assert res.json()["name"] == "New Cook"

    def test_create_user_as_staff_forbidden(self, client, db):
        staff, loc = _create_user(db, role="staff", pin="1234")
        headers = _login(client, staff.id, "1234")
        res = client.post("/api/users", json={
            "name": "Nope",
            "role": "staff",
            "pin": "4444",
            "location_id": loc.id,
        }, headers=headers)
        assert res.status_code == 403

    def test_list_users_as_manager(self, client, db):
        manager, loc = _create_user(db, role="manager", pin="1111")
        headers = _login(client, manager.id, "1111")
        res = client.get(f"/api/users?location_id={loc.id}", headers=headers)
        assert res.status_code == 200
        assert len(res.json()) >= 1

    def test_list_users_as_staff_forbidden(self, client, db):
        staff, loc = _create_user(db, role="staff", pin="1234")
        headers = _login(client, staff.id, "1234")
        res = client.get(f"/api/users?location_id={loc.id}", headers=headers)
        assert res.status_code == 403
