"""Tests for enhanced registration form on login page."""


class TestRegistrationFormElements:
    """Registration form has all required fields and elements."""

    def test_has_confirm_password_field(self, client):
        """Registration form has a confirm password input."""
        resp = client.get("/login")
        assert 'id="register-confirm-password"' in resp.text

    def test_has_farm_select_dropdown(self, client):
        """Registration form has a farm association dropdown."""
        resp = client.get("/login")
        assert 'id="register-farm"' in resp.text

    def test_confirm_password_label_in_spanish(self, client):
        """Confirm password label is in Spanish."""
        resp = client.get("/login")
        assert "Confirmar" in resp.text

    def test_farm_label_in_spanish(self, client):
        """Farm dropdown label is in Spanish."""
        resp = client.get("/login")
        html = resp.text
        assert "Granja" in html or "Finca" in html

    def test_farm_has_none_option(self, client):
        """Farm dropdown has a 'none' / no-farm option."""
        resp = client.get("/login")
        assert "Sin granja" in resp.text or "Ninguna" in resp.text


class TestRegistrationJS:
    """login.js handles registration enhancements."""

    def test_js_has_confirm_password_validation(self, client):
        """login.js validates that passwords match."""
        resp = client.get("/login.js")
        js = resp.text
        assert "register-confirm-password" in js

    def test_js_has_farm_fetch(self, client):
        """login.js fetches farm list for the dropdown."""
        resp = client.get("/login.js")
        js = resp.text
        assert "/api/farms" in js or "register-farm" in js

    def test_js_sends_farm_id_on_register(self, client):
        """login.js sends farm_id in the registration request body."""
        resp = client.get("/login.js")
        js = resp.text
        assert "farm_id" in js


class TestRegistrationAPIWithFarm:
    """Registration API accepts farm_id."""

    def test_register_with_farm_id(self, client, db):
        """Register with a farm_id associates the user to a farm."""
        from cultivos.db.models import Farm
        farm = Farm(name="Rancho Test", state="Jalisco", total_hectares=50.0)
        db.add(farm)
        db.commit()
        db.refresh(farm)

        resp = client.post("/api/auth/register", json={
            "username": "farmworker",
            "password": "secret123",
            "role": "farmer",
            "farm_id": farm.id,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["farm_id"] == farm.id

    def test_register_without_farm_id(self, client, db):
        """Register without farm_id works (farm_id is optional)."""
        resp = client.post("/api/auth/register", json={
            "username": "researcher1",
            "password": "secret123",
            "role": "researcher",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["farm_id"] is None
