"""FL5 — Component polish pass tests.

Verify FL1 design tokens are consumed by cards, stat tiles, health badges,
buttons, forms across main pages. Consistent button hierarchy, no orphan
hardcoded values, hover/transition motion on interactive elements.
"""

import re
from pathlib import Path

import pytest

FRONTEND = Path(__file__).parent.parent / "frontend"
STYLES = FRONTEND / "styles.css"

MAIN_PAGES = ["index.html", "field.html", "management.html",
              "notifications.html", "intel.html", "knowledge.html"]


@pytest.fixture
def css_text():
    return STYLES.read_text(encoding="utf-8")


@pytest.fixture(params=MAIN_PAGES)
def page_text(request):
    p = FRONTEND / request.param
    if not p.exists():
        pytest.skip(f"{request.param} not found")
    return (request.param, p.read_text(encoding="utf-8"))


# ── Button hierarchy classes exist ──


def test_btn_primary_class_exists(css_text):
    assert re.search(r"\.btn-primary\s*\{", css_text), \
        "styles.css must define .btn-primary"


def test_btn_secondary_class_exists(css_text):
    assert re.search(r"\.btn-secondary\s*\{", css_text), \
        "styles.css must define .btn-secondary"


def test_btn_ghost_class_exists(css_text):
    assert re.search(r"\.btn-ghost\s*\{", css_text), \
        "styles.css must define .btn-ghost"


def test_btn_primary_uses_brand_green(css_text):
    primary_block = re.search(
        r"\.btn-primary\s*\{([^}]+)\}", css_text)
    assert primary_block, ".btn-primary block not found"
    block = primary_block.group(1)
    assert "var(--brand-green" in block or "var(--green" in block or "var(--accent" in block, \
        ".btn-primary must use a green token for background"


def test_btn_primary_has_hover(css_text):
    assert re.search(r"\.btn-primary:hover\s*\{", css_text), \
        ".btn-primary must have a :hover state"


def test_btn_secondary_has_border(css_text):
    block = re.search(r"\.btn-secondary\s*\{([^}]+)\}", css_text)
    assert block, ".btn-secondary block not found"
    assert "border" in block.group(1), \
        ".btn-secondary must have a border (outline style)"


def test_btn_ghost_transparent_bg(css_text):
    block = re.search(r"\.btn-ghost\s*\{([^}]+)\}", css_text)
    assert block, ".btn-ghost block not found"
    b = block.group(1)
    assert "transparent" in b or "none" in b, \
        ".btn-ghost must have transparent/none background"


# ── Card hover uses token shadows ──


CARD_HOVER_SELECTORS = [
    r"\.stat-card:hover",
    r"\.farm-card:hover",
    r"\.field-card:hover",
]


@pytest.mark.parametrize("selector", CARD_HOVER_SELECTORS)
def test_card_hover_uses_token_shadow(css_text, selector):
    pattern = selector + r"\s*\{([^}]+)\}"
    match = re.search(pattern, css_text)
    if not match:
        pytest.skip(f"{selector} not found")
    block = match.group(1)
    if "box-shadow" in block:
        assert "var(--shadow" in block, \
            f"{selector} box-shadow must use var(--shadow-*) token, not hardcoded rgba"


# ── Health badge colors use tokens ──


def test_health_badge_warning_uses_token(css_text):
    match = re.search(r"\.health-badge\.warning\s*\{([^}]+)\}", css_text)
    assert match, ".health-badge.warning not found"
    block = match.group(1)
    assert "#92400e" not in block, \
        ".health-badge.warning must use a token, not hardcoded #92400e"
    assert "var(--" in block, \
        ".health-badge.warning color must reference a CSS variable"


def test_health_badge_critical_uses_token(css_text):
    match = re.search(r"\.health-badge\.critical\s*\{([^}]+)\}", css_text)
    assert match, ".health-badge.critical not found"
    block = match.group(1)
    assert "#991b1b" not in block, \
        ".health-badge.critical must use a token, not hardcoded #991b1b"


def test_health_badge_none_uses_token(css_text):
    match = re.search(r"\.health-badge\.none\s*\{([^}]+)\}", css_text)
    assert match, ".health-badge.none not found"
    block = match.group(1)
    assert "#f3f4f6" not in block, \
        ".health-badge.none must use a token, not hardcoded #f3f4f6"


# ── Border radius uses tokens ──


RADIUS_SELECTORS = [
    (r"\.health-badge\s*\{", "--radius"),
    (r"\.field-card\s*\{", "--radius"),
    (r"\.export-csv-btn\s*\{", "--radius"),
]


@pytest.mark.parametrize("selector,token_prefix", RADIUS_SELECTORS)
def test_border_radius_uses_token(css_text, selector, token_prefix):
    match = re.search(selector + r"([^}]+)\}", css_text)
    if not match:
        pytest.skip(f"{selector} not found")
    block = match.group(1)
    if "border-radius" in block:
        radius_val = re.search(r"border-radius:\s*([^;]+)", block)
        if radius_val:
            val = radius_val.group(1).strip()
            assert "var(" in val, \
                f"{selector} border-radius must use var({token_prefix}-*), got '{val}'"


# ── Transition/motion on interactive elements ──


INTERACTIVE_SELECTORS = [
    r"\.btn-primary\s*\{",
    r"\.btn-secondary\s*\{",
    r"\.btn-ghost\s*\{",
]


@pytest.mark.parametrize("selector", INTERACTIVE_SELECTORS)
def test_interactive_has_transition(css_text, selector):
    match = re.search(selector + r"([^}]+)\}", css_text)
    assert match, f"{selector} not found"
    block = match.group(1)
    assert "transition" in block, \
        f"{selector} must have a transition property for hover motion"


# ── Form focus ring uses tokens ──


def test_form_focus_ring_uses_token(css_text):
    focus_blocks = re.findall(r"focus\s*\{([^}]+)\}", css_text)
    hardcoded_focus = [b for b in focus_blocks
                       if "rgba(22" in b and "box-shadow" in b]
    assert len(hardcoded_focus) == 0, \
        "Form focus rings must use token-based color, not hardcoded rgba(22,163,74,...)"


# ── Buttons use token-based colors, not hardcoded #fff ──


def test_soil_submit_btn_no_hardcoded_white(css_text):
    match = re.search(r"\.soil-submit-btn\s*\{([^}]+)\}", css_text)
    if not match:
        pytest.skip(".soil-submit-btn not found")
    block = match.group(1)
    assert "#fff" not in block.lower(), \
        ".soil-submit-btn must not use hardcoded #fff — use var(--neutral-50) or token"


# ── Summary stat health colors use tokens ──


def test_summary_health_warning_no_hardcoded(css_text):
    if ".summary-stat-value.health-warning" not in css_text:
        pytest.skip("selector not found")
    match = re.search(
        r"\.summary-stat-value\.health-warning\s*\{([^}]+)\}", css_text)
    assert match
    assert "#f59e0b" not in match.group(1), \
        ".summary-stat-value.health-warning must use token, not #f59e0b"


def test_summary_health_critical_no_hardcoded(css_text):
    if ".summary-stat-value.health-critical" not in css_text:
        pytest.skip("selector not found")
    match = re.search(
        r"\.summary-stat-value\.health-critical\s*\{([^}]+)\}", css_text)
    assert match
    assert "#ef4444" not in match.group(1), \
        ".summary-stat-value.health-critical must use token, not #ef4444"
