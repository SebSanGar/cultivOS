"""T0.1 — assumptions.py provenance registry.

Every magic number in economics.py / analytics.py must be registered here with:
  - non-empty source_url
  - valid status (measured | literature | model_assumption)
  - non-empty confidence_note

Tests FAIL before assumptions.py exists, PASS after.
"""

import re
from pathlib import Path

import pytest

SRC = Path(__file__).parent.parent / "src" / "cultivos" / "services" / "intelligence"
ECONOMICS_PY = SRC / "economics.py"
ANALYTICS_PY = SRC / "analytics.py"

VALID_STATUSES = {"measured", "literature", "model_assumption"}

# Keys that must be in the registry (corresponding to economics.py / analytics.py constants)
REQUIRED_KEYS = {
    "water_savings_per_ha",
    "fertilizer_savings_per_ha",
    "yield_baseline_per_ha",
    "default_irrigation_efficiency",
    "per_treatment_savings_mxn",
}


# ---------------------------------------------------------------------------
# Import guard
# ---------------------------------------------------------------------------


def _get_registry():
    from cultivos.services.intelligence.assumptions import REGISTRY
    return REGISTRY


# ---------------------------------------------------------------------------
# T1 — Registry structure
# ---------------------------------------------------------------------------


class TestRegistryStructure:
    def test_registry_is_dict(self):
        registry = _get_registry()
        assert isinstance(registry, dict), "REGISTRY must be a dict keyed by assumption key"

    def test_registry_not_empty(self):
        registry = _get_registry()
        assert len(registry) > 0, "REGISTRY must have at least one entry"

    def test_all_required_keys_present(self):
        registry = _get_registry()
        missing = REQUIRED_KEYS - set(registry.keys())
        assert not missing, f"T0.1: REGISTRY missing required keys: {sorted(missing)}"

    def test_each_record_has_required_fields(self):
        registry = _get_registry()
        required_fields = {
            "value", "low", "high", "unit",
            "source_name", "source_url", "source_year",
            "status", "confidence_note",
        }
        for key, rec in registry.items():
            missing = required_fields - set(rec.keys())
            assert not missing, f"T0.1: record '{key}' missing fields: {sorted(missing)}"

    def test_all_statuses_valid(self):
        registry = _get_registry()
        for key, rec in registry.items():
            assert rec["status"] in VALID_STATUSES, (
                f"T0.1: record '{key}' has invalid status '{rec['status']}'. "
                f"Must be one of: {VALID_STATUSES}"
            )

    def test_all_source_urls_non_empty(self):
        registry = _get_registry()
        for key, rec in registry.items():
            assert rec["source_url"] and rec["source_url"].strip(), (
                f"T0.1: record '{key}' has empty source_url"
            )

    def test_all_confidence_notes_non_empty(self):
        registry = _get_registry()
        for key, rec in registry.items():
            assert rec["confidence_note"] and rec["confidence_note"].strip(), (
                f"T0.1: record '{key}' has empty confidence_note"
            )

    def test_all_low_lte_value_lte_high(self):
        registry = _get_registry()
        for key, rec in registry.items():
            assert rec["low"] <= rec["value"] <= rec["high"], (
                f"T0.1: record '{key}' violates low <= value <= high: "
                f"{rec['low']} <= {rec['value']} <= {rec['high']}"
            )

    def test_source_years_plausible(self):
        registry = _get_registry()
        for key, rec in registry.items():
            assert 1990 <= rec["source_year"] <= 2030, (
                f"T0.1: record '{key}' has implausible source_year {rec['source_year']}"
            )


# ---------------------------------------------------------------------------
# T2 — get() accessor
# ---------------------------------------------------------------------------


class TestGetAccessor:
    def test_get_returns_record_for_known_key(self):
        from cultivos.services.intelligence.assumptions import get
        rec = get("water_savings_per_ha")
        assert rec is not None
        assert "value" in rec

    def test_get_raises_for_unknown_key(self):
        from cultivos.services.intelligence.assumptions import get
        with pytest.raises(KeyError):
            get("nonexistent_key_xyz")

    def test_get_value_returns_float(self):
        from cultivos.services.intelligence.assumptions import get_value
        val = get_value("water_savings_per_ha")
        assert isinstance(val, (int, float))
        assert val > 0


# ---------------------------------------------------------------------------
# T3 — Magic numbers NOT bare in economics.py / analytics.py
# ---------------------------------------------------------------------------


class TestNoBareMagicNumbers:
    """After T0.1, economics.py and analytics.py must NOT contain bare numeric literals
    for the constants that were migrated to assumptions.py."""

    def _bare_pattern(self, number: str) -> re.Pattern:
        # Match the bare number as a standalone token (not part of a larger number or comment)
        return re.compile(
            rf"(?<![#\"'])(?<!\d)(?<!\w){re.escape(number)}(?!\d)(?!,\d)",
            re.MULTILINE,
        )

    def test_economics_no_bare_8000(self):
        text = ECONOMICS_PY.read_text()
        # Should not contain bare 8000 as a constant definition
        # But may appear in comments; strip comments first
        lines = [l for l in text.splitlines() if not l.strip().startswith("#")]
        code = "\n".join(lines)
        assert "8_000" not in code and "8000" not in code, (
            "T0.1: economics.py still has bare 8000 constant — move to assumptions.py"
        )

    def test_economics_no_bare_5000(self):
        text = ECONOMICS_PY.read_text()
        lines = [l for l in text.splitlines() if not l.strip().startswith("#")]
        code = "\n".join(lines)
        assert "5_000" not in code and "5000" not in code, (
            "T0.1: economics.py still has bare 5000 constant — move to assumptions.py"
        )

    def test_economics_no_bare_7700(self):
        text = ECONOMICS_PY.read_text()
        lines = [l for l in text.splitlines() if not l.strip().startswith("#")]
        code = "\n".join(lines)
        assert "7_700" not in code and "7700" not in code, (
            "T0.1: economics.py still has bare 7700 constant — move to assumptions.py"
        )

    def test_analytics_no_bare_1500(self):
        text = ANALYTICS_PY.read_text()
        lines = [l for l in text.splitlines() if not l.strip().startswith("#")]
        code = "\n".join(lines)
        # 1500 should not appear as a raw number in non-comment lines
        pattern = re.compile(r"\b1500\b")
        assert not pattern.search(code), (
            "T0.1: analytics.py still has bare 1500 constant — move to assumptions.py"
        )

    def test_economics_imports_from_assumptions(self):
        text = ECONOMICS_PY.read_text()
        assert "assumptions" in text, (
            "T0.1: economics.py must import from assumptions.py"
        )

    def test_analytics_imports_from_assumptions(self):
        text = ANALYTICS_PY.read_text()
        assert "assumptions" in text, (
            "T0.1: analytics.py must import from assumptions.py"
        )
