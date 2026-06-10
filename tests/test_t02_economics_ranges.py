"""T0.2 — economics endpoint returns RANGES not points.

Adds total_savings_low_mxn / total_savings_high_mxn, confidence, is_estimate,
basis. Drops causal "esta generando valor real" language. TDD: low < point <= high.

Tests FAIL before T0.2 implementation, PASS after.
"""

import pytest


@pytest.fixture()
def seeded_farm(db):
    from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord

    farm = Farm(name="T02 Test Farm", municipality="Guadalajara", total_hectares=20.0)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Parcela Norte", hectares=20.0, crop_type="aguacate")
    db.add(field)
    db.flush()
    for score in [60, 70, 75, 80]:
        db.add(HealthScore(field_id=field.id, score=score))
    for _ in range(4):
        db.add(TreatmentRecord(
            field_id=field.id,
            health_score_used=72,
            problema="Estres hidrico",
            causa_probable="Falta de riego",
            tratamiento="Compost organico",
            urgencia="media",
            prevencion="Monitoreo semanal",
        ))
    db.commit()
    return farm.id


@pytest.fixture()
def empty_farm(db):
    from cultivos.db.models import Farm

    farm = Farm(name="T02 Empty Farm", municipality="Guadalajara", total_hectares=0.0)
    db.add(farm)
    db.commit()
    return farm.id


# ---------------------------------------------------------------------------
# T1 — Response shape: new fields present
# ---------------------------------------------------------------------------


class TestEconomicImpactShape:
    def test_response_has_low_field(self, client, seeded_farm):
        r = client.get(f"/api/farms/{seeded_farm}/economic-impact")
        assert r.status_code == 200
        body = r.json()
        assert "total_savings_low_mxn" in body, (
            "T0.2: response missing total_savings_low_mxn field"
        )

    def test_response_has_high_field(self, client, seeded_farm):
        r = client.get(f"/api/farms/{seeded_farm}/economic-impact")
        assert r.status_code == 200
        body = r.json()
        assert "total_savings_high_mxn" in body, (
            "T0.2: response missing total_savings_high_mxn field"
        )

    def test_response_has_is_estimate(self, client, seeded_farm):
        r = client.get(f"/api/farms/{seeded_farm}/economic-impact")
        assert r.status_code == 200
        body = r.json()
        assert "is_estimate" in body, "T0.2: response missing is_estimate field"
        assert body["is_estimate"] is True, "T0.2: is_estimate must always be True"

    def test_response_has_confidence(self, client, seeded_farm):
        r = client.get(f"/api/farms/{seeded_farm}/economic-impact")
        assert r.status_code == 200
        body = r.json()
        assert "confidence" in body, "T0.2: response missing confidence field"
        assert body["confidence"] in {"low", "medium", "high"}, (
            f"T0.2: confidence must be low/medium/high, got {body['confidence']!r}"
        )

    def test_response_has_basis(self, client, seeded_farm):
        r = client.get(f"/api/farms/{seeded_farm}/economic-impact")
        assert r.status_code == 200
        body = r.json()
        assert "basis" in body, "T0.2: response missing basis field"
        assert isinstance(body["basis"], list), "T0.2: basis must be a list"
        assert len(body["basis"]) > 0, "T0.2: basis must reference at least one assumption"


# ---------------------------------------------------------------------------
# T2 — Range correctness: low < total <= high
# ---------------------------------------------------------------------------


class TestEconomicRangeValues:
    def test_low_less_than_total_savings(self, client, seeded_farm):
        r = client.get(f"/api/farms/{seeded_farm}/economic-impact")
        body = r.json()
        if body["total_savings_mxn"] > 0:
            assert body["total_savings_low_mxn"] < body["total_savings_mxn"], (
                "T0.2: low must be strictly less than total when total > 0"
            )

    def test_total_savings_lte_high(self, client, seeded_farm):
        r = client.get(f"/api/farms/{seeded_farm}/economic-impact")
        body = r.json()
        assert body["total_savings_mxn"] <= body["total_savings_high_mxn"], (
            "T0.2: total_savings_mxn must be <= total_savings_high_mxn"
        )

    def test_low_approx_60_pct_of_high(self, client, seeded_farm):
        r = client.get(f"/api/farms/{seeded_farm}/economic-impact")
        body = r.json()
        if body["total_savings_high_mxn"] > 0:
            ratio = body["total_savings_low_mxn"] / body["total_savings_high_mxn"]
            assert 0.50 <= ratio <= 0.70, (
                f"T0.2: low/high ratio should be ~0.6, got {ratio:.2f}"
            )

    def test_unknown_farm_returns_404(self, client):
        r = client.get("/api/farms/99999/economic-impact")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# T3 — Causal language removed from nota
# ---------------------------------------------------------------------------


class TestHonestCopyInNota:
    def test_nota_lacks_causal_language(self, client, seeded_farm):
        r = client.get(f"/api/farms/{seeded_farm}/economic-impact")
        body = r.json()
        nota = body.get("nota", "")
        forbidden = ["generando valor real", "esta generando", "cultivOS te ahorro"]
        for phrase in forbidden:
            assert phrase not in nota.lower(), (
                f"T0.2: nota contains causal language '{phrase}' — replace with honest qualifier"
            )

    def test_nota_contains_estimate_qualifier(self, client, seeded_farm):
        r = client.get(f"/api/farms/{seeded_farm}/economic-impact")
        body = r.json()
        nota = body.get("nota", "")
        qualifiers = ["estimacion", "estimado", "depende", "basada", "aproxim"]
        has_qualifier = any(q in nota.lower() for q in qualifiers)
        assert has_qualifier, (
            f"T0.2: nota must contain an estimate qualifier. Got: {nota!r}"
        )


# ---------------------------------------------------------------------------
# T4 — No-fields case still works
# ---------------------------------------------------------------------------


class TestNoFieldsCase:
    def test_no_fields_farm_has_range_fields(self, client, empty_farm):
        r = client.get(f"/api/farms/{empty_farm}/economic-impact")
        assert r.status_code == 200
        body = r.json()
        assert "total_savings_low_mxn" in body
        assert "is_estimate" in body
        assert body["is_estimate"] is True
