"""T3.3 — Shared .impact-* CSS block in styles.css (single source of truth for farmer + owner pages)."""
import re
import pytest

STYLES = "/Users/SebSan/Documents/cultivOS/frontend/styles.css"


@pytest.fixture(scope="module")
def css():
    with open(STYLES) as f:
        return f.read()


REQUIRED_CLASSES = [
    ".impact-equiv-row",
    ".impact-equiv-chip",
    ".before-after-field",
    ".owner-hero",
    ".cost-compare-bar",
    ".estimate-badge",
    ".estimate-range",
    ".source-cite",
    ".card--estimated",
    ".card--measured",
]


@pytest.mark.parametrize("cls", REQUIRED_CLASSES)
def test_required_class_exists(css, cls):
    """Each T3.3 shared class must be defined in styles.css."""
    assert cls in css, f"Missing shared CSS class: {cls}"


def test_no_hardcoded_hex_in_t33_block(css):
    """All new T3.3 classes must use CSS vars — no hardcoded hex colors."""
    # Extract the T3.3 block (after the marker comment)
    marker = "/* T3.3 SHARED IMPACT CLASSES */"
    assert marker in css, "T3.3 block marker missing"
    block_start = css.index(marker)
    t33_block = css[block_start:]
    # Allow hex inside var() fallbacks — e.g. var(--foo, #fff) — by stripping those first
    stripped = re.sub(r"var\([^)]+\)", "", t33_block)
    bare_hex = re.findall(r":\s*#[0-9a-fA-F]{3,6}", stripped)
    assert not bare_hex, f"Hardcoded hex in T3.3 block: {bare_hex}"


def test_estimate_badge_has_padding(css):
    """estimate-badge must have padding (visible qualifier chip)."""
    # Find the rule block
    m = re.search(r"\.estimate-badge\s*\{([^}]+)\}", css)
    assert m, ".estimate-badge rule block not found"
    assert "padding" in m.group(1)


def test_card_estimated_vs_measured_differ(css):
    """card--estimated and card--measured must have different border/background treatments."""
    m_est = re.search(r"\.card--estimated\s*\{([^}]+)\}", css)
    m_meas = re.search(r"\.card--measured\s*\{([^}]+)\}", css)
    assert m_est and m_meas, "Both card modifier rules must exist"
    # They must not be identical
    assert m_est.group(1).strip() != m_meas.group(1).strip(), (
        "card--estimated and card--measured must have distinct styles"
    )


def test_owner_hero_has_text_size(css):
    """owner-hero must define a font-size using CSS var."""
    m = re.search(r"\.owner-hero\s*\{([^}]+)\}", css)
    assert m, ".owner-hero rule not found"
    assert "font-size" in m.group(1) or "var(--text" in m.group(1)


def test_source_cite_has_color(css):
    """source-cite must define a color (muted, to indicate secondary attribution)."""
    m = re.search(r"\.source-cite\s*\{([^}]+)\}", css)
    assert m, ".source-cite rule not found"
    assert "color" in m.group(1)


def test_cost_compare_bar_has_height(css):
    """cost-compare-bar must define a height for the bar visual."""
    m = re.search(r"\.cost-compare-bar\s*\{([^}]+)\}", css)
    assert m, ".cost-compare-bar rule not found"
    assert "height" in m.group(1)


def test_mobile_responsive_equiv_row(css):
    """impact-equiv-row must be flex/wrap for small screens."""
    m = re.search(r"\.impact-equiv-row\s*\{([^}]+)\}", css)
    assert m, ".impact-equiv-row rule not found"
    rule = m.group(1)
    assert "flex" in rule or "wrap" in rule, "equiv-row should use flex layout"
