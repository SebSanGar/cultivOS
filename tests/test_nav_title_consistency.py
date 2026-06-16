"""Nav label and dashboard title must name the same thing identically.

Regression guard for the "My Crops -> Farms" confusion: the nav link
(nav.farms) and the dashboard heading (dash.title) resolve to different
words, so clicking "My Crops" landed on a page titled "Farms".
"""
import os
import re

I18N = os.path.join(os.path.dirname(__file__), "..", "frontend", "i18n.js")


def _values(key):
    """Return all values assigned to a given i18n key (one per locale block)."""
    with open(I18N, encoding="utf-8") as f:
        src = f.read()
    return re.findall(r"'%s':\s*'([^']*)'" % re.escape(key), src)


def test_nav_farms_matches_dash_title_per_locale():
    nav = _values("nav.farms")
    dash = _values("dash.title")
    assert nav and dash, "nav.farms / dash.title not found in i18n.js"
    assert len(nav) == len(dash), "nav.farms and dash.title defined in different # of locales"
    # locale blocks are in the same order (ES then EN); each pair must agree
    for n, d in zip(nav, dash):
        assert n == d, f"nav label {n!r} != dashboard title {d!r} — same entity, different name"
