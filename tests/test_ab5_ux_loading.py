"""AB5 — UX loading/empty/aria on the 2 impact pages (I3).

economic-impact: skeleton loader on hero + aria-live on stats strip.
impacto-agricultor: distinct empty-state + aria-live on stats strip.
"""
import re
from pathlib import Path

ECON = Path("frontend/economic-impact.html").read_text()
ECON_JS = Path("frontend/economic-impact.js").read_text()
FARMER = Path("frontend/impacto-agricultor.html").read_text()
FARMER_JS = Path("frontend/impacto-agricultor.js").read_text()
CSS = Path("frontend/styles.css").read_text()


# ── economic-impact: aria-live on stats strip ─────────────────────────────────

def test_econ_stats_strip_has_aria_live():
    """Stats strip announces value changes to screen readers."""
    assert re.search(r'intel-stats-strip[^>]*aria-live="polite"', ECON), \
        "economic-impact stats strip needs aria-live='polite'"


def test_econ_stats_strip_has_aria_atomic_false():
    """Each stat cell updates independently — atomic=false lets screen readers read each."""
    assert re.search(r'intel-stats-strip[^>]*aria-atomic="false"', ECON) or \
           re.search(r'aria-atomic="false"[^>]*intel-stats-strip', ECON), \
        "economic-impact stats strip needs aria-atomic='false'"


# ── economic-impact: skeleton loader on hero ──────────────────────────────────

def test_econ_hero_skeleton_element_exists():
    """Hero area needs a skeleton-loader element shown while data loads."""
    assert 'id="econ-hero-skeleton"' in ECON, \
        "economic-impact hero needs #econ-hero-skeleton element"


def test_skeleton_class_in_css():
    """styles.css must define .skeleton for the shimmer loading state."""
    assert ".skeleton" in CSS, "styles.css needs .skeleton class"


def test_skeleton_animation_in_css():
    """Skeleton must have a visible animation (shimmer / pulse)."""
    assert "skeleton" in CSS and "animation" in CSS, \
        "styles.css needs animation on skeleton elements"


def test_econ_js_hides_skeleton_after_load():
    """economic-impact.js must remove skeleton after data loads."""
    assert "econ-hero-skeleton" in ECON_JS, \
        "economic-impact.js must reference #econ-hero-skeleton to hide after load"


# ── impacto-agricultor: aria-live on stats strip ──────────────────────────────

def test_farmer_support_strip_has_aria_live():
    """#impact-support strip announces value changes to screen readers."""
    assert re.search(r'id="impact-support"[^>]*aria-live="polite"', FARMER) or \
           re.search(r'aria-live="polite"[^>]*id="impact-support"', FARMER), \
        "impacto-agricultor #impact-support needs aria-live='polite'"


# ── impacto-agricultor: distinct empty-state ─────────────────────────────────

def test_farmer_has_distinct_empty_state_element():
    """Page needs a dedicated empty-state div, distinct from the hero."""
    assert 'id="impact-empty-state"' in FARMER, \
        "impacto-agricultor needs #impact-empty-state element"


def test_farmer_empty_state_css_exists():
    """styles.css must have .impact-empty-state rule."""
    assert ".impact-empty-state" in CSS, \
        "styles.css needs .impact-empty-state class"


def test_farmer_js_uses_empty_state_toggle():
    """showEmptyHero must toggle #impact-empty-state visibility."""
    assert "impact-empty-state" in FARMER_JS, \
        "impacto-agricultor.js showEmptyHero must show/hide #impact-empty-state"
