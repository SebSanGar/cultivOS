"""Tests for #216 — extended ancestral method seeds (target >= 22)."""

import pytest

from cultivos.db.models import AncestralMethod
from cultivos.db.seeds import ANCESTRAL_METHOD_SEEDS, seed_ancestral_methods


NEW_METHOD_NAMES = {
    "Terrazas mayas",
    "Calendario lunar agricola",
    "Tres hermanas con chile (4-hermanas)",
    "Zanjas de infiltracion",
    "Cobertura con paja seca",
    "Abonos verdes con Crotalaria",
    "Control biologico con Trichogramma",
    "Captura de agua de niebla",
    "Biofertilizante Bocashi tradicional",
    "Lombricomposta tradicional",
}


class TestExtendedAncestralSeeds:
    def test_seed_count_at_least_22(self):
        assert len(ANCESTRAL_METHOD_SEEDS) >= 22

    def test_new_methods_present(self):
        names = {m.name for m in ANCESTRAL_METHOD_SEEDS}
        missing = NEW_METHOD_NAMES - names
        assert not missing, f"Missing new ancestral methods: {missing}"

    def test_new_methods_have_required_fields(self):
        by_name = {m.name: m for m in ANCESTRAL_METHOD_SEEDS}
        for name in NEW_METHOD_NAMES:
            m = by_name[name]
            assert m.description_es and len(m.description_es) >= 20
            assert m.region
            assert m.practice_type
            assert isinstance(m.crops, list) and len(m.crops) >= 1
            assert m.benefits_es
            assert m.scientific_basis
            assert isinstance(m.applicable_months, list) and len(m.applicable_months) >= 1
            for month in m.applicable_months:
                assert 1 <= month <= 12, f"{name}: month {month} out of range"
            assert isinstance(m.ecological_benefit, int)
            assert 1 <= m.ecological_benefit <= 5
            assert m.timing_rationale

    def test_seed_function_loads_new_methods_into_db(self, db):
        inserted = seed_ancestral_methods(db)
        assert inserted >= 22
        rows = db.query(AncestralMethod).all()
        names = {r.name for r in rows}
        assert NEW_METHOD_NAMES.issubset(names)

    def test_new_methods_persist_applicable_months_and_ecological_benefit(self, db):
        seed_ancestral_methods(db)
        rows = db.query(AncestralMethod).filter(
            AncestralMethod.name.in_(list(NEW_METHOD_NAMES))
        ).all()
        assert len(rows) == len(NEW_METHOD_NAMES)
        for r in rows:
            assert r.applicable_months, f"{r.name} missing applicable_months in DB"
            assert r.ecological_benefit is not None, f"{r.name} missing ecological_benefit in DB"
            assert r.timing_rationale, f"{r.name} missing timing_rationale in DB"
