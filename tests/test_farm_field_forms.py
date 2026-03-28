"""Tests for farm and field creation forms on dashboard.

Verifies:
1. "Nueva Granja" button and form HTML render in index.html
2. "Nuevo Campo" button renders in field panel
3. createFarm() JS function exists in app.js
4. createField() JS function exists in app.js
5. POST /api/farms creates a farm (API sanity — already tested in test_farms.py, light check here)
6. POST /api/farms/{id}/fields creates a field (API sanity)
"""

import re


class TestFarmCreationFormHTML:
    """Farm creation form renders in index.html."""

    def test_nueva_granja_button_exists(self):
        with open("frontend/index.html") as f:
            html = f.read()
        assert "Nueva Granja" in html, "Missing 'Nueva Granja' button in index.html"

    def test_farm_creation_form_exists(self):
        with open("frontend/index.html") as f:
            html = f.read()
        assert 'id="farm-create-form"' in html, "Missing farm creation form in index.html"

    def test_farm_form_has_name_field(self):
        with open("frontend/index.html") as f:
            html = f.read()
        assert 'id="farm-name"' in html, "Missing farm name input"

    def test_farm_form_has_hectares_field(self):
        with open("frontend/index.html") as f:
            html = f.read()
        assert 'id="farm-hectares"' in html, "Missing farm hectares input"

    def test_farm_form_has_municipality_field(self):
        with open("frontend/index.html") as f:
            html = f.read()
        assert 'id="farm-municipality"' in html, "Missing farm municipality input"


class TestFieldCreationFormHTML:
    """Field creation form renders in field panel."""

    def test_nuevo_campo_button_exists(self):
        with open("frontend/index.html") as f:
            html = f.read()
        assert "Nuevo Campo" in html, "Missing 'Nuevo Campo' button in index.html"

    def test_field_creation_form_exists(self):
        with open("frontend/index.html") as f:
            html = f.read()
        assert 'id="field-create-form"' in html, "Missing field creation form in index.html"

    def test_field_form_has_name_field(self):
        with open("frontend/index.html") as f:
            html = f.read()
        assert 'id="field-name"' in html, "Missing field name input"

    def test_field_form_has_crop_type_field(self):
        with open("frontend/index.html") as f:
            html = f.read()
        assert 'id="field-crop-type"' in html, "Missing field crop type input"

    def test_field_form_has_hectares_field(self):
        with open("frontend/index.html") as f:
            html = f.read()
        assert 'id="field-hectares"' in html, "Missing field hectares input"


class TestCreateFarmJS:
    """createFarm and createField functions exist in app.js."""

    def test_create_farm_function_exists(self):
        with open("frontend/app.js") as f:
            js = f.read()
        assert re.search(r"async\s+function\s+createFarm", js), "Missing createFarm() in app.js"

    def test_create_field_function_exists(self):
        with open("frontend/app.js") as f:
            js = f.read()
        assert re.search(r"async\s+function\s+createField", js), "Missing createField() in app.js"

    def test_create_farm_posts_to_api(self):
        with open("frontend/app.js") as f:
            js = f.read()
        assert "POST" in js and "/farms" in js, "createFarm must POST to /api/farms"

    def test_create_farm_sends_auth_token(self):
        with open("frontend/app.js") as f:
            js = f.read()
        assert "cultivOS_token" in js, "createFarm must send auth token from localStorage"


class TestFarmCreationAPI:
    """POST /api/farms creates farm (light sanity check)."""

    def test_create_farm_returns_201(self, client, admin_headers):
        resp = client.post("/api/farms", json={"name": "Rancho Test"}, headers=admin_headers)
        assert resp.status_code == 201
        assert resp.json()["name"] == "Rancho Test"

    def test_create_field_returns_201(self, client, admin_headers):
        farm = client.post("/api/farms", json={"name": "Farm X"}, headers=admin_headers).json()
        resp = client.post(
            f"/api/farms/{farm['id']}/fields",
            json={"name": "Campo Norte", "crop_type": "maiz", "hectares": 25.0},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Campo Norte"
        assert resp.json()["crop_type"] == "maiz"
