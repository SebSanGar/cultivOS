"""Tests for GET /api/knowledge/farmer-vocabulary endpoint."""

import pytest
from cultivos.db.models import FarmerVocabulary


def make_vocab(
    db,
    phrase="se está amarillando",
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


def test_list_all_returns_all(client, db):
    """No filters returns all entries."""
    make_vocab(db, phrase="se está amarillando", crop="maiz", symptom="yellowing")
    make_vocab(db, phrase="tiene plaga", crop="maiz", symptom="pest")
    resp = client.get("/api/knowledge/farmer-vocabulary")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_filter_by_crop(client, db):
    """Filter by crop returns only matching entries."""
    make_vocab(db, phrase="se petateó", crop="maiz", symptom="dying")
    make_vocab(db, phrase="le falta agua", crop="frijol", symptom="drought")
    make_vocab(db, phrase="sale espuma", crop="agave", symptom="disease")
    resp = client.get("/api/knowledge/farmer-vocabulary?crop=maiz")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["crop"] == "maiz"


def test_filter_by_symptom(client, db):
    """Filter by symptom returns only matching entries."""
    make_vocab(db, phrase="se está amarillando", crop="maiz", symptom="yellowing")
    make_vocab(db, phrase="hoja amarilla", crop="agave", symptom="yellowing")
    make_vocab(db, phrase="tiene plaga", crop="maiz", symptom="pest")
    resp = client.get("/api/knowledge/farmer-vocabulary?symptom=yellowing")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(d["symptom"] == "yellowing" for d in data)


def test_filter_by_crop_and_symptom(client, db):
    """Both filters combined returns intersection."""
    make_vocab(db, phrase="se está amarillando", crop="maiz", symptom="yellowing")
    make_vocab(db, phrase="hoja amarilla", crop="agave", symptom="yellowing")
    make_vocab(db, phrase="tiene plaga", crop="maiz", symptom="pest")
    resp = client.get("/api/knowledge/farmer-vocabulary?crop=maiz&symptom=yellowing")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["phrase"] == "se está amarillando"


def test_unknown_symptom_returns_empty_not_404(client, db):
    """Unknown symptom/crop combo returns empty list, not 404."""
    make_vocab(db, phrase="se está amarillando", crop="maiz", symptom="yellowing")
    resp = client.get("/api/knowledge/farmer-vocabulary?symptom=explosion")
    assert resp.status_code == 200
    assert resp.json() == []


def test_case_insensitive_crop_filter(client, db):
    """Crop filter is case-insensitive."""
    make_vocab(db, phrase="se petateó", crop="maiz", symptom="dying")
    resp = client.get("/api/knowledge/farmer-vocabulary?crop=MAIZ")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_response_fields(client, db):
    """Response includes all required fields."""
    make_vocab(
        db,
        phrase="se está amarillando",
        formal_term_es="clorosis",
        likely_cause="deficiencia de nitrógeno",
        recommended_action="Aplicar composta nitrogenada.",
        crop="maiz",
        symptom="yellowing",
    )
    resp = client.get("/api/knowledge/farmer-vocabulary")
    assert resp.status_code == 200
    entry = resp.json()[0]
    assert "id" in entry
    assert entry["phrase"] == "se está amarillando"
    assert entry["formal_term_es"] == "clorosis"
    assert entry["likely_cause"] == "deficiencia de nitrógeno"
    assert entry["recommended_action"] == "Aplicar composta nitrogenada."
    assert entry["crop"] == "maiz"
    assert entry["symptom"] == "yellowing"


def test_empty_db_returns_empty_list(client, db):
    """Empty DB returns empty list, not error."""
    resp = client.get("/api/knowledge/farmer-vocabulary")
    assert resp.status_code == 200
    assert resp.json() == []
