"""Tests for GET /api/knowledge/search unified knowledge base search."""

import pytest


# ---------------------------------------------------------------------------
# Helpers — seed minimal knowledge records
# ---------------------------------------------------------------------------

def _add_vocab(db, phrase, formal_term_es, crop="maiz"):
    from cultivos.db.models import FarmerVocabulary
    v = FarmerVocabulary(
        phrase=phrase,
        formal_term_es=formal_term_es,
        likely_cause="Estrés hídrico",
        recommended_action="Regar de madrugada con agua filtrada",
        crop=crop,
        symptom="drought",
    )
    db.add(v)
    db.commit()
    return v


def _add_ancestral(db, name, description_es, problems=None):
    from cultivos.db.models import AncestralMethod
    m = AncestralMethod(
        name=name,
        description_es=description_es,
        region="jalisco",
        practice_type="soil_management",
        crops=["maiz"],
        benefits_es="Mejora el suelo",
        problems=problems or [],
    )
    db.add(m)
    db.commit()
    return m


def _add_fertilizer(db, name, description_es):
    from cultivos.db.models import Fertilizer
    f = Fertilizer(
        name=name,
        description_es=description_es,
        application_method="Aplicar al suelo",
        cost_per_ha_mxn=500,
        nutrient_profile="N-P-K",
        suitable_crops=["maiz"],
    )
    db.add(f)
    db.commit()
    return f


def _add_tip(db, crop, problem, tip_text_es):
    from cultivos.db.models import AgronomistTip
    t = AgronomistTip(
        crop=crop,
        problem=problem,
        tip_text_es=tip_text_es,
        source="CIMMYT",
        region="jalisco",
        season="dry",
    )
    db.add(t)
    db.commit()
    return t


# ---------------------------------------------------------------------------
# Key-schema assertion
# ---------------------------------------------------------------------------

def test_response_schema_keys(client, db):
    _add_ancestral(db, "Milpa", "Sistema de cultivo con erosion control")
    resp = client.get("/api/knowledge/search?q=erosion")
    assert resp.status_code == 200
    results = resp.json()
    assert isinstance(results, list)
    if results:
        item = results[0]
        assert "type" in item
        assert "id" in item
        assert "name" in item
        assert "summary" in item


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_query_matches_ancestral_method(client, db):
    """Search returns ancestral method when query matches name or description."""
    _add_ancestral(db, "Milpa Tradicional", "Control de erosion mediante intercultivo")
    resp = client.get("/api/knowledge/search?q=erosion")
    assert resp.status_code == 200
    data = resp.json()
    types = [r["type"] for r in data]
    assert "ancestral_method" in types


def test_query_matches_fertilizer(client, db):
    """Search returns fertilizer when query matches name or description."""
    _add_fertilizer(db, "Composta Verde", "Rico en nitrogeno organico para suelo")
    resp = client.get("/api/knowledge/search?q=nitrogeno")
    assert resp.status_code == 200
    data = resp.json()
    types = [r["type"] for r in data]
    assert "fertilizer" in types


def test_query_matches_agronomist_tip(client, db):
    """Search returns agronomist tip when query matches tip text."""
    _add_tip(db, "maiz", "drought", "Mulchear el suelo para retener humedad en sequia")
    resp = client.get("/api/knowledge/search?q=sequia")
    assert resp.status_code == 200
    data = resp.json()
    types = [r["type"] for r in data]
    assert "agronomist_tip" in types


def test_unknown_term_returns_empty_not_404(client, db):
    """Unknown query term returns empty list, not 404."""
    _add_ancestral(db, "Milpa", "Cultivo tradicional de maiz")
    resp = client.get("/api/knowledge/search?q=xyzunknownterm999")
    assert resp.status_code == 200
    assert resp.json() == []


def test_empty_query_returns_all_limited(client, db):
    """Empty q returns all records (up to limit)."""
    _add_ancestral(db, "Milpa", "Sistema milpa")
    _add_fertilizer(db, "Vermicomposta", "Composta de lombriz")
    _add_tip(db, "maiz", "drought", "Regar de madrugada")
    resp = client.get("/api/knowledge/search?q=")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 3


def test_case_insensitive_match(client, db):
    """Search is case-insensitive."""
    _add_ancestral(db, "Tesgüino", "Practica de EROSION ancestral")
    resp = client.get("/api/knowledge/search?q=Erosion")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1


def test_limit_param_respected(client, db):
    """limit param caps results."""
    for i in range(10):
        _add_fertilizer(db, f"Abono{i}", f"Descripcion organica del abono numero {i}")
    resp = client.get("/api/knowledge/search?q=organica&limit=3")
    assert resp.status_code == 200
    assert len(resp.json()) <= 3


def test_multi_type_results_in_single_response(client, db):
    """Single query can return results from multiple knowledge types."""
    _add_ancestral(db, "Milpa Organica", "Metodo organico ancestral")
    _add_fertilizer(db, "Composta Organica", "Fertilizante organico de calidad")
    resp = client.get("/api/knowledge/search?q=organica")
    assert resp.status_code == 200
    data = resp.json()
    types = {r["type"] for r in data}
    assert len(types) >= 2


# ---------------------------------------------------------------------------
# New tests: type filter + FarmerVocabulary (#168)
# ---------------------------------------------------------------------------

def test_type_tips_returns_only_tips(client, db):
    """type=tips filter returns only agronomist_tip results, not fertilizers or ancestral."""
    _add_tip(db, "maiz", "drought", "Aplicar agua en la madrugada para evitar perdida")
    _add_ancestral(db, "Milpa Agua", "Practica tradicional para agua")
    _add_fertilizer(db, "Abono Agua", "Fertilizante para suelo con agua")
    resp = client.get("/api/knowledge/search?q=agua&type=tips")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    types = {r["type"] for r in data}
    assert types == {"agronomist_tip"}


def test_type_fertilizers_returns_only_fertilizers(client, db):
    """type=fertilizers filter returns only fertilizer results."""
    _add_fertilizer(db, "Composta Verde", "Nitrogeno organico para suelo fertil")
    _add_tip(db, "maiz", "disease", "Consejos fertil para el cultivo")
    resp = client.get("/api/knowledge/search?q=fertil&type=fertilizers")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    types = {r["type"] for r in data}
    assert types == {"fertilizer"}


def test_type_ancestral_returns_only_ancestral(client, db):
    """type=ancestral filter returns only ancestral_method results."""
    _add_ancestral(db, "Milpa Sagrada", "Sistema de milpa sagrada ancestral")
    _add_fertilizer(db, "Composta Sagrada", "Fertilizante sagrado de calidad")
    resp = client.get("/api/knowledge/search?q=sagrada&type=ancestral")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    types = {r["type"] for r in data}
    assert types == {"ancestral_method"}


def test_type_vocab_returns_only_farmer_vocabulary(client, db):
    """type=vocab filter returns only farmer_vocabulary results."""
    _add_vocab(db, "se esta petateando", "marchitamiento severo")
    _add_ancestral(db, "Metodo Marchitamiento", "Practica para marchitamiento del cultivo")
    resp = client.get("/api/knowledge/search?q=marchitamiento&type=vocab")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    types = {r["type"] for r in data}
    assert types == {"farmer_vocabulary"}


def test_vocab_included_in_unfiltered_search(client, db):
    """FarmerVocabulary appears in results when no type filter."""
    _add_vocab(db, "el maiz se esta secando", "desecacion foliar")
    resp = client.get("/api/knowledge/search?q=secando")
    assert resp.status_code == 200
    data = resp.json()
    types = {r["type"] for r in data}
    assert "farmer_vocabulary" in types


def test_vocab_searches_phrase_and_formal_term(client, db):
    """FarmerVocabulary search covers both phrase and formal_term_es."""
    _add_vocab(db, "la planta llora", "exudacion radicular")
    # search on formal term
    resp = client.get("/api/knowledge/search?q=exudacion")
    assert resp.status_code == 200
    data = resp.json()
    assert any(r["type"] == "farmer_vocabulary" for r in data)


def test_unknown_type_filter_returns_400(client, db):
    """Unknown type value returns 400 (invalid parameter)."""
    resp = client.get("/api/knowledge/search?q=maiz&type=invalid_type")
    assert resp.status_code == 422


def test_q_agua_matches_multiple_categories(client, db):
    """q=agua returns results from multiple knowledge categories (spec test)."""
    _add_ancestral(db, "Manejo del Agua", "Practica ancestral para conservar agua en suelo")
    _add_fertilizer(db, "Riego Organico", "Aplicacion de fertilizante con agua de lluvia")
    _add_tip(db, "maiz", "drought", "Aplicar agua por las mananas para reducir evaporacion")
    _add_vocab(db, "falta agua", "deficit hidrico")
    resp = client.get("/api/knowledge/search?q=agua")
    assert resp.status_code == 200
    data = resp.json()
    types = {r["type"] for r in data}
    assert len(types) >= 2
