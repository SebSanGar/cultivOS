"""Tests for #219 — batch 2 of Jalisco regenerative TEK seeds (target >= 26)."""

from cultivos.db.models import AncestralMethod
from cultivos.db.seeds import ANCESTRAL_METHOD_SEEDS, seed_ancestral_methods


NEW_METHOD_NAMES = {
    "Metepantle con magueyes",
    "Cafe bajo sombra nativa",
    "Curvas a nivel con nopal",
    "Apicultura melipona integrada",
}


class TestBatch2AncestralSeeds:
    def test_seed_count_at_least_26(self):
        assert len(ANCESTRAL_METHOD_SEEDS) >= 26

    def test_new_methods_present(self):
        names = {m.name for m in ANCESTRAL_METHOD_SEEDS}
        missing = NEW_METHOD_NAMES - names
        assert not missing, f"Missing batch-2 ancestral methods: {missing}"

    def test_new_methods_have_all_fields_populated(self):
        """#216 regression guard — every batch-2 field must be non-None and non-empty."""
        by_name = {m.name: m for m in ANCESTRAL_METHOD_SEEDS}
        for name in NEW_METHOD_NAMES:
            m = by_name[name]
            assert m.description_es and len(m.description_es) >= 20
            assert m.region
            assert m.practice_type in {
                "soil_management",
                "intercropping",
                "water_management",
                "biological_control",
                "knowledge_system",
            }, f"{name}: unknown practice_type {m.practice_type!r}"
            assert isinstance(m.crops, list) and len(m.crops) >= 1
            assert m.benefits_es
            assert m.scientific_basis
            assert isinstance(m.problems, list) and len(m.problems) >= 1, (
                f"{name}: problems must be non-empty list (not None) to avoid #216 Pydantic regression"
            )
            assert isinstance(m.applicable_months, list) and len(m.applicable_months) >= 1
            for month in m.applicable_months:
                assert 1 <= month <= 12, f"{name}: month {month} out of range"
            assert isinstance(m.ecological_benefit, int)
            assert 1 <= m.ecological_benefit <= 5
            assert m.timing_rationale

    def test_seed_function_persists_new_methods(self, db):
        inserted = seed_ancestral_methods(db)
        assert inserted >= 26
        rows = db.query(AncestralMethod).filter(
            AncestralMethod.name.in_(list(NEW_METHOD_NAMES))
        ).all()
        assert len(rows) == len(NEW_METHOD_NAMES)
        for r in rows:
            assert r.problems
            assert r.applicable_months
            assert r.ecological_benefit is not None
            assert r.timing_rationale
