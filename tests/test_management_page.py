"""Tests for /gestion — farm and field management CRUD page."""


class TestManagementPageRoute:
    """Management page serves and contains expected elements."""

    def test_gestion_route_returns_200(self, client):
        resp = client.get("/gestion")
        assert resp.status_code == 200

    def test_gestion_returns_html(self, client):
        resp = client.get("/gestion")
        assert "text/html" in resp.headers.get("content-type", "")

    def test_page_contains_title(self, client):
        resp = client.get("/gestion")
        assert "Gestion" in resp.text or "gestion" in resp.text

    def test_page_has_nav_with_links(self, client):
        resp = client.get("/gestion")
        body = resp.text
        assert 'href="/"' in body
        assert 'href="/intel"' in body
        assert 'href="/gestion"' in body

    def test_page_loads_management_js(self, client):
        resp = client.get("/gestion")
        assert "management.js" in resp.text


class TestManagementPageFarmElements:
    """Page contains farm CRUD form elements."""

    def test_page_contains_farm_table(self, client):
        resp = client.get("/gestion")
        assert "mgmt-farms-table" in resp.text

    def test_page_contains_farm_create_form(self, client):
        resp = client.get("/gestion")
        body = resp.text
        assert "mgmt-farm-name" in body
        assert "mgmt-farm-state" in body
        assert "mgmt-farm-hectares" in body

    def test_page_contains_farm_create_button(self, client):
        resp = client.get("/gestion")
        assert "Crear Granja" in resp.text or "crear-granja" in resp.text.lower()

    def test_page_contains_farm_delete_confirm(self, client):
        resp = client.get("/gestion")
        assert "mgmt-confirm-dialog" in resp.text


class TestManagementPageFieldElements:
    """Page contains field CRUD form elements."""

    def test_page_contains_field_section(self, client):
        resp = client.get("/gestion")
        assert "mgmt-fields-section" in resp.text

    def test_page_contains_field_create_form(self, client):
        resp = client.get("/gestion")
        body = resp.text
        assert "mgmt-field-name" in body
        assert "mgmt-field-crop" in body
        assert "mgmt-field-hectares" in body

    def test_page_contains_field_table(self, client):
        resp = client.get("/gestion")
        assert "mgmt-fields-table" in resp.text


class TestManagementJS:
    """Management JS contains CRUD and fetch logic."""

    def test_management_js_accessible(self, client):
        resp = client.get("/management.js")
        assert resp.status_code == 200

    def test_js_has_fetch_logic(self, client):
        resp = client.get("/management.js")
        js = resp.text
        assert "fetchJSON" in js
        assert "/api/farms" in js

    def test_js_has_create_farm_function(self, client):
        resp = client.get("/management.js")
        assert "createFarm" in resp.text

    def test_js_has_delete_farm_function(self, client):
        resp = client.get("/management.js")
        assert "deleteFarm" in resp.text

    def test_js_has_create_field_function(self, client):
        resp = client.get("/management.js")
        assert "createField" in resp.text

    def test_js_has_delete_field_function(self, client):
        resp = client.get("/management.js")
        assert "deleteField" in resp.text

    def test_js_has_edit_farm_function(self, client):
        resp = client.get("/management.js")
        assert "editFarm" in resp.text or "updateFarm" in resp.text

    def test_js_has_edit_field_function(self, client):
        resp = client.get("/management.js")
        assert "editField" in resp.text or "updateField" in resp.text

    def test_js_handles_validation(self, client):
        resp = client.get("/management.js")
        js = resp.text
        assert "required" in js.lower() or "validation" in js.lower() or "nombre" in js.lower()

    def test_js_has_confirmation_dialog(self, client):
        resp = client.get("/management.js")
        assert "confirm" in resp.text.lower()
