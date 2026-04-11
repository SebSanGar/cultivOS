"""Tests for POST /api/intel/diagnose-problem — phrase-to-treatment pipeline."""

import pytest
from cultivos.db.models import Farm, Field, FarmerVocabulary, HealthScore
from datetime import datetime


def make_vocab(
    db,
    phrase="se está amarillando el maíz",
    formal_term_es="clorosis",
    likely_cause="deficiencia de nitrógeno",
    recommended_action="Aplicar composta o fertilizante orgánico nitrogenado.",
    crop="maiz",
    symptom="yellowing",
):
    entry = FarmerVocabulary(
        phrase=phrase,
        formal_term_es=formal_term_es,
        likely_cause=likely_cause,
        recommended_action=recommended_action,
        crop=crop,
        symptom=symptom,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def make_farm_field(db, crop_type="maiz", health_score_value=45.0):
    farm = Farm(name="Rancho Test", state="Jalisco", total_hectares=10)
    db.add(farm)
    db.commit()
    db.refresh(farm)

    field = Field(farm_id=farm.id, name="Parcela 1", crop_type=crop_type, hectares=5)
    db.add(field)
    db.commit()
    db.refresh(field)

    score = HealthScore(
        field_id=field.id,
        score=health_score_value,
        scored_at=datetime.utcnow(),
        sources=[],
        breakdown={},
    )
    db.add(score)
    db.commit()

    return farm, field


# ── Response key contract (spec assertion — must pass before implementation) ──

def test_response_keys_present(client, db):
    """Response must contain exactly: matched_phrase, formal_term_es, likely_cause,
    recommended_action, treatments."""
    make_vocab(db, phrase="se está amarillando el maíz", crop="maiz")
    resp = client.post("/api/intel/diagnose-problem", json={
        "phrase": "se está amarillando el maíz",
        "crop": "maiz",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "matched_phrase" in data
    assert "formal_term_es" in data
    assert "likely_cause" in data
    assert "recommended_action" in data
    assert "treatments" in data
    assert isinstance(data["treatments"], list)


# ── Exact phrase match ──

def test_exact_phrase_match(client, db):
    """Exact phrase match returns vocab entry fields."""
    make_vocab(
        db,
        phrase="se está amarillando el maíz",
        formal_term_es="clorosis",
        likely_cause="deficiencia de nitrógeno",
        recommended_action="Aplicar composta nitrogenada.",
        crop="maiz",
    )
    resp = client.post("/api/intel/diagnose-problem", json={
        "phrase": "se está amarillando el maíz",
        "crop": "maiz",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["matched_phrase"] == "se está amarillando el maíz"
    assert data["formal_term_es"] == "clorosis"
    assert data["likely_cause"] == "deficiencia de nitrógeno"
    assert data["recommended_action"] == "Aplicar composta nitrogenada."


# ── Partial / word-overlap match ──

def test_partial_word_match(client, db):
    """Phrase sharing words with a vocab entry still returns a match."""
    make_vocab(db, phrase="se está amarillando", crop="maiz", symptom="yellowing")
    # Input phrase has extra words but shares "amarillando"
    resp = client.post("/api/intel/diagnose-problem", json={
        "phrase": "el maíz se está amarillando mucho",
        "crop": "maiz",
    })
    assert resp.status_code == 200
    data = resp.json()
    # Should match the vocab entry via word overlap
    assert data["matched_phrase"] == "se está amarillando"
    assert isinstance(data["treatments"], list)


# ── No match — fallback to generic recommendations ──

def test_no_match_returns_recommendations_not_404(client, db):
    """Unrecognised phrase returns generic treatments — never 404 or error."""
    # DB is empty — no vocab entries
    resp = client.post("/api/intel/diagnose-problem", json={
        "phrase": "el campo tiene un problema raro",
        "crop": "maiz",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["matched_phrase"] is None
    assert data["formal_term_es"] is None
    assert isinstance(data["treatments"], list)
    assert len(data["treatments"]) >= 1


# ── Crop scoping ──

def test_crop_scoping_prefers_matching_crop(client, db):
    """When multiple vocab entries exist, crop-scoped entry is preferred."""
    make_vocab(db, phrase="se está secando", crop="agave", symptom="drought",
               formal_term_es="deshidratación del agave")
    make_vocab(db, phrase="se está secando", crop="maiz", symptom="drought",
               formal_term_es="deshidratación del maíz")
    resp = client.post("/api/intel/diagnose-problem", json={
        "phrase": "se está secando",
        "crop": "maiz",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["formal_term_es"] == "deshidratación del maíz"


# ── field_id adds health context ──

def test_field_id_adds_health_context(client, db):
    """Providing field_id returns treatments informed by field health score."""
    make_vocab(db, phrase="hojas amarillas", crop="maiz", symptom="yellowing")
    _, field = make_farm_field(db, crop_type="maiz", health_score_value=30.0)

    resp = client.post("/api/intel/diagnose-problem", json={
        "phrase": "hojas amarillas",
        "crop": "maiz",
        "field_id": field.id,
    })
    assert resp.status_code == 200
    data = resp.json()
    # Low health score (30) should produce treatments
    assert isinstance(data["treatments"], list)
    assert len(data["treatments"]) >= 1


def test_field_id_not_found_still_returns_result(client, db):
    """Non-existent field_id does not 404 — gracefully falls back to no health context."""
    make_vocab(db, phrase="hojas amarillas", crop="maiz", symptom="yellowing")
    resp = client.post("/api/intel/diagnose-problem", json={
        "phrase": "hojas amarillas",
        "crop": "maiz",
        "field_id": 99999,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "treatments" in data


# ── Keyword extraction fallback ──

def test_keyword_extraction_for_pest(client, db):
    """Phrase containing 'plaga' returns pest-relevant treatments even with no vocab match."""
    resp = client.post("/api/intel/diagnose-problem", json={
        "phrase": "tiene plaga en las hojas",
        "crop": "maiz",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["treatments"], list)
    assert len(data["treatments"]) >= 1
