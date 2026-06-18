"""Guard: seeded Spanish treatment strings get an English variant in EN mode.

Seb's report (2026-06-18): the intelligence page (/intel) still showed treatment
techniques in Spanish while the UI was in English. Root cause: the OUT models
carried an optional `tratamiento_en` but nothing populated it, so the frontend
`loc()` fell back to the Spanish `tratamiento`. Fixed by a translate pass
(treatment_i18n.treatment_en) wired into the analytics report builders.

These tests lock the map coverage + the builder wiring so the leak can't return.
"""
import re

import pytest

from cultivos.services.intelligence.treatment_i18n import TREATMENT_EN, treatment_en


def _seed_treatment_strings():
    """Every Spanish `tratamiento` string seeded into the demo DB."""
    with open("scripts/seed_demo.py", encoding="utf-8") as f:
        src = f.read()
    return re.findall(r'"tratamiento":\s*"([^"]+)"', src)


def test_every_seeded_treatment_has_english():
    seeded = _seed_treatment_strings()
    assert seeded, "no seeded treatment strings found — test wiring broke"
    missing = [s for s in seeded if not treatment_en(s)]
    assert not missing, f"seeded treatments without an English variant: {missing}"


def test_english_variants_are_not_spanish_passthrough():
    """The map must actually translate, not echo the Spanish back."""
    for es, en in TREATMENT_EN.items():
        assert en and en != es, f"non-translation for: {es!r}"
        # crude leak check: translated text should not retain Spanish stems
        assert not re.search(r"\b(aplicar|sembrar|riego|composta|ton/ha)\b", en.lower()), (
            f"English variant still contains Spanish tokens: {en!r}"
        )


def test_unknown_treatment_returns_none():
    assert treatment_en("Some free-text treatment not in the map") is None
    assert treatment_en("") is None
    assert treatment_en(None) is None


def test_report_builder_populates_tratamiento_en(db):
    """End-to-end: the /intel effectiveness report emits tratamiento_en."""
    from datetime import datetime, timedelta

    from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord
    from cultivos.services.intelligence.analytics import (
        compute_treatment_effectiveness_report,
    )

    es = "Aplicar bocashi 4 ton/ha + siembra de frijol de abono intercalado"
    farm = Farm(name="T", state="Jalisco", total_hectares=10.0,
                location_lat=20.6, location_lon=-103.3, municipality="Zapopan")
    db.add(farm); db.flush()
    field = Field(farm_id=farm.id, name="P1", hectares=10.0, crop_type="maiz")
    db.add(field); db.flush()
    t0 = datetime(2026, 1, 1)
    db.add(TreatmentRecord(field_id=field.id, tratamiento=es, health_score_used=50.0,
                           problema="Compactacion", causa_probable="Trafico",
                           urgencia="media", prevencion="Rotacion", created_at=t0))
    db.add(HealthScore(field_id=field.id, score=60.0, scored_at=t0 + timedelta(days=5)))
    db.commit()

    report = compute_treatment_effectiveness_report(db)
    rows = [t for t in report["treatments"] if t["tratamiento"] == es]
    assert rows, "seeded treatment not in report"
    assert rows[0]["tratamiento_en"] == treatment_en(es)
    assert rows[0]["tratamiento_en"] and rows[0]["tratamiento_en"] != es
