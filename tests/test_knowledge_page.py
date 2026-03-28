"""Tests for the ancestral knowledge reference page — knowledge.html + knowledge.js."""

import pytest

from cultivos.db.models import AncestralMethod, CropType, Fertilizer


# ── HTML structure ──

def test_knowledge_page_loads(client):
    """Knowledge page loads at /conocimiento."""
    resp = client.get("/conocimiento")
    assert resp.status_code == 200
    assert "Conocimiento" in resp.text


def test_knowledge_page_has_search_input(client):
    """Knowledge page has a search input for filtering cards."""
    resp = client.get("/conocimiento")
    html = resp.text
    assert 'id="knowledge-search"' in html


def test_knowledge_page_has_ancestral_section(client):
    """Knowledge page has a section for ancestral methods."""
    resp = client.get("/conocimiento")
    html = resp.text
    assert 'id="ancestral-cards"' in html
    assert "Metodos Ancestrales" in html or "Ancestrales" in html


def test_knowledge_page_has_crops_section(client):
    """Knowledge page has a section for crop types."""
    resp = client.get("/conocimiento")
    html = resp.text
    assert 'id="crop-cards"' in html
    assert "Cultivos" in html


def test_knowledge_page_has_fertilizer_section(client):
    """Knowledge page has a section for natural fertilizers."""
    resp = client.get("/conocimiento")
    html = resp.text
    assert 'id="fertilizer-cards"' in html
    assert "Fertilizantes" in html


def test_knowledge_page_has_nav(client):
    """Knowledge page has navigation with link back to dashboard."""
    resp = client.get("/conocimiento")
    html = resp.text
    assert 'href="/"' in html
    assert 'href="/conocimiento"' in html


# ── JS logic ──

def test_knowledge_js_loads(client):
    """knowledge.js is served and contains render functions."""
    resp = client.get("/knowledge.js")
    assert resp.status_code == 200
    assert "renderAncestral" in resp.text


def test_knowledge_js_fetches_endpoints(client):
    """knowledge.js fetches all three knowledge endpoints."""
    resp = client.get("/knowledge.js")
    js = resp.text
    assert "/api/knowledge/ancestral" in js
    assert "/api/knowledge/crops" in js
    assert "/api/knowledge/fertilizers" in js


def test_knowledge_js_has_search_filter(client):
    """knowledge.js has a search/filter function."""
    resp = client.get("/knowledge.js")
    js = resp.text
    assert "filterCards" in js or "knowledge-search" in js


# ── CSS ──

def test_knowledge_styles_present(client):
    """styles.css has knowledge page styling."""
    resp = client.get("/styles.css")
    assert resp.status_code == 200
    assert "knowledge" in resp.text


# ── API integration (backends exist — verify they work for page rendering) ──

@pytest.fixture
def seed_knowledge(db):
    """Seed knowledge base data for testing."""
    m = AncestralMethod(
        name="Milpa",
        description_es="Sistema de policultivo mesoamericano con maiz, frijol y calabaza.",
        region="Mesoamerica",
        practice_type="intercropping",
        crops=["maiz", "frijol", "calabaza"],
        benefits_es="Fijacion de nitrogeno, control de plagas, diversidad alimentaria.",
        scientific_basis="Complementary nitrogen fixation by legumes.",
    )
    c = CropType(
        name="maiz",
        family="Poaceae",
        growing_season="temporal",
        water_needs="medium",
        regions=["jalisco", "oaxaca"],
        companions=["frijol", "calabaza"],
        days_to_harvest=120,
        optimal_temp_min=18.0,
        optimal_temp_max=32.0,
        description_es="Cultivo base de la dieta mexicana.",
    )
    f = Fertilizer(
        name="Composta",
        description_es="Materia organica descompuesta rica en nutrientes.",
        application_method="Incorporar al suelo antes de siembra.",
        cost_per_ha_mxn=1500,
        nutrient_profile="N-P-K balanceado, micronutrientes",
        suitable_crops=["maiz", "frijol", "tomate"],
    )
    db.add_all([m, c, f])
    db.commit()
    return m, c, f


def test_ancestral_api_returns_data(client, seed_knowledge):
    """GET /api/knowledge/ancestral returns seeded methods."""
    resp = client.get("/api/knowledge/ancestral")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Milpa"
    assert "practice_type" in data[0]


def test_crops_api_returns_data(client, seed_knowledge):
    """GET /api/knowledge/crops returns seeded crop types."""
    resp = client.get("/api/knowledge/crops")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["name"] == "maiz"
    assert "regions" in data[0]


def test_fertilizer_api_returns_data(client, seed_knowledge):
    """GET /api/knowledge/fertilizers returns seeded fertilizers."""
    resp = client.get("/api/knowledge/fertilizers")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Composta"
    assert "cost_per_ha_mxn" in data[0]
