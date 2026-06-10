"""Honesty CI gate — proves every cultivOS economic constant has traceable provenance.

Tests FAIL before honesty gate implementation, PASS after:
- TestSocConstantCoverage: _SOC_TO_CO2E (3.67) must have a registry entry

Always-on assertions (guard against future regressions):
- TestRegistryFormat: every REGISTRY entry has non-empty source_url/source_name + valid status
- TestGetValueCoverage: all _a("key") calls in economics.py/analytics.py exist in REGISTRY
- TestFarmerVoiceLinter: returned strings from _HANDLERS lack banned jargon
"""

import re
from pathlib import Path

import pytest

SRC = Path(__file__).parent.parent / "src" / "cultivos" / "services" / "intelligence"

VALID_STATUSES = {"measured", "literature", "model_assumption"}

BANNED_JARGON = {
    "ROI", "KPI", "NDVI", "threshold", "optimization", "anomaly",
    "dashboard", "metricas", "celsius", "pct",
}


# ---------------------------------------------------------------------------
# T1 — Registry format: every entry is fully documented
# ---------------------------------------------------------------------------


class TestRegistryFormat:
    def test_all_entries_have_source_url(self):
        from cultivos.services.intelligence.assumptions import REGISTRY
        bad = [k for k, v in REGISTRY.items() if not v.get("source_url", "").strip()]
        assert not bad, f"Missing source_url: {bad}"

    def test_all_entries_have_source_name(self):
        from cultivos.services.intelligence.assumptions import REGISTRY
        bad = [k for k, v in REGISTRY.items() if not v.get("source_name", "").strip()]
        assert not bad, f"Missing source_name: {bad}"

    def test_all_entries_have_valid_status(self):
        from cultivos.services.intelligence.assumptions import REGISTRY
        bad = [k for k, v in REGISTRY.items() if v.get("status") not in VALID_STATUSES]
        assert not bad, f"Invalid status: {bad}"

    def test_all_entries_have_nonzero_value(self):
        from cultivos.services.intelligence.assumptions import REGISTRY
        # value=0 is a sentinel for "not set" — every real constant must be non-zero
        bad = [k for k, v in REGISTRY.items() if v.get("value", 0) == 0]
        assert not bad, f"Zero value (missing?): {bad}"


# ---------------------------------------------------------------------------
# T2 — get_value() / _a() call coverage: all keys exist in REGISTRY
# ---------------------------------------------------------------------------


def _extract_a_keys(filepath: Path) -> list[str]:
    """Extract all string literals used in _a("key") or get_value("key") calls."""
    text = filepath.read_text()
    # Match _a("key") or _a('key') or get_value("key") or get_value('key')
    pattern = r'(?:_a|get_value)\(\s*["\']([^"\']+)["\']\s*\)'
    return re.findall(pattern, text)


class TestGetValueCoverage:
    def test_economics_py_keys_in_registry(self):
        from cultivos.services.intelligence.assumptions import REGISTRY
        keys = _extract_a_keys(SRC / "economics.py")
        missing = [k for k in keys if k not in REGISTRY]
        assert not missing, (
            f"economics.py references keys not in REGISTRY: {missing}"
        )

    def test_analytics_py_keys_in_registry(self):
        from cultivos.services.intelligence.assumptions import REGISTRY
        analytics_path = SRC / "analytics.py"
        if not analytics_path.exists():
            pytest.skip("analytics.py not found")
        keys = _extract_a_keys(analytics_path)
        missing = [k for k in keys if k not in REGISTRY]
        assert not missing, (
            f"analytics.py references keys not in REGISTRY: {missing}"
        )


# ---------------------------------------------------------------------------
# T3 — Known bare constants must have registry entries
# Tests FAIL before adding soc_to_co2e to REGISTRY (RED commit target)
# ---------------------------------------------------------------------------


class TestSocConstantCoverage:
    def test_soc_to_co2e_has_registry_entry(self):
        """_SOC_TO_CO2E = 3.67 appears 4x in analytics.py — must be in REGISTRY.

        This is the molecular weight ratio CO2/C (44/12 ≈ 3.667), used to convert
        soil organic carbon tonnes to CO2-equivalent tonnes for carbon reporting.
        Source: IPCC Guidelines for National GHG Inventories (2006).
        """
        from cultivos.services.intelligence.assumptions import REGISTRY
        assert "soc_to_co2e" in REGISTRY, (
            "Honesty gate FAIL: _SOC_TO_CO2E = 3.67 in analytics.py has no assumptions.py entry. "
            "Add 'soc_to_co2e' to REGISTRY with IPCC 2006 source."
        )

    def test_soc_to_co2e_value_is_correct(self):
        """3.67 is the accepted IPCC value (44/12 rounded); verify registry matches."""
        from cultivos.services.intelligence.assumptions import REGISTRY
        if "soc_to_co2e" not in REGISTRY:
            pytest.skip("soc_to_co2e not yet in REGISTRY")
        value = REGISTRY["soc_to_co2e"]["value"]
        assert abs(value - 3.67) < 0.01, f"soc_to_co2e should be ~3.67, got {value}"

    def test_soc_to_co2e_status_is_literature(self):
        from cultivos.services.intelligence.assumptions import REGISTRY
        if "soc_to_co2e" not in REGISTRY:
            pytest.skip("soc_to_co2e not yet in REGISTRY")
        assert REGISTRY["soc_to_co2e"]["status"] == "literature", (
            "soc_to_co2e is an IPCC constant — status must be 'literature'"
        )


# ---------------------------------------------------------------------------
# T4 — Farmer-voice linter: no banned jargon in returned strings
# ---------------------------------------------------------------------------


class TestFarmerVoiceLinter:
    def _get_all_handler_outputs(self) -> list[str]:
        """Call all handlers with a minimal signal dict and collect outputs."""
        from cultivos.services.intelligence.farmer_voice import _HANDLERS, translate_to_farmer
        outputs = []
        for signal_type in _HANDLERS:
            result = translate_to_farmer({"type": signal_type, "value": 0.3, "score": 35, "celsius": 38})
            outputs.append(result)
        return outputs

    def test_no_banned_jargon_in_farmer_strings(self):
        outputs = self._get_all_handler_outputs()
        violations = []
        for word in BANNED_JARGON:
            for s in outputs:
                if word.lower() in s.lower():
                    violations.append(f"'{word}' in: {s!r}")
        assert not violations, f"Banned jargon in farmer strings:\n" + "\n".join(violations)

    def test_no_decimals_in_farmer_strings(self):
        outputs = self._get_all_handler_outputs()
        # Decimal pattern: digit followed by . and more digits
        decimal_re = re.compile(r'\d+\.\d+')
        violations = [s for s in outputs if decimal_re.search(s)]
        assert not violations, f"Decimal numbers in farmer strings: {violations}"

    def test_all_outputs_are_nonempty(self):
        outputs = self._get_all_handler_outputs()
        assert all(len(s) > 5 for s in outputs), "Some handler returned empty/trivial string"
