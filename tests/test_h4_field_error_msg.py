"""H4 — Verify field.js handles a param-less /campo load using the correct
param names (?farm= / ?field=, not farm_id/field_id).

ROOT CAUSE: field.js reads params.get('farm') + params.get('field') but original
error text said '?farm_id=ID&field_id=ID' — misleading to end user.
FIX (EN-leak sweep): the raw "Error: missing parameters" heading was replaced by
a graceful path — auto-select the first farm/field (redirect using ?farm=&field=)
and fall back to a friendly message with a link home. The wrong param names must
still never appear.
TEST: grep asserts the auto-select redirect uses correct param names + old wrong
string absent.
"""

from pathlib import Path

FIELD_JS = Path(__file__).parent.parent / "frontend" / "field.js"


def test_error_message_correct_params():
    """Param-less load must auto-select via a ?farm=&field= redirect (correct names)."""
    content = FIELD_JS.read_text()
    assert "window.location.replace(`/campo?farm=" in content, (
        "field.js must auto-select the first farm/field on a param-less load by "
        "redirecting to /campo?farm=...&field=... (correct param names)"
    )
    assert "&field=" in content, "field.js redirect must include the &field= param"


def test_error_message_no_wrong_params():
    """Error message must NOT say ?farm_id=ID or ?field_id=ID (wrong param names)."""
    content = FIELD_JS.read_text()
    assert "farm_id=ID" not in content, (
        "field.js still contains 'farm_id=ID' in error message — must be removed"
    )
    assert "field_id=ID" not in content, (
        "field.js still contains 'field_id=ID' in error message — must be removed"
    )
