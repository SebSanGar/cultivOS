"""H4 — Verify field.js error message uses ?farm=ID&field=ID (not farm_id/field_id).

ROOT CAUSE: field.js reads params.get('farm') + params.get('field') but original
error text said '?farm_id=ID&field_id=ID' — misleading to end user.
FIX: already applied (line 41 now reads '?farm=ID&field=ID').
TEST: grep asserts corrected string present + old wrong string absent.
"""

from pathlib import Path

FIELD_JS = Path(__file__).parent.parent / "frontend" / "field.js"


def test_error_message_correct_params():
    """Error message must say ?farm=ID&field=ID (matches actual JS params)."""
    content = FIELD_JS.read_text()
    assert "?farm=ID&field=ID" in content, (
        "field.js error message must use ?farm=ID&field=ID — matches params.get('farm') / params.get('field')"
    )


def test_error_message_no_wrong_params():
    """Error message must NOT say ?farm_id=ID or ?field_id=ID (wrong param names)."""
    content = FIELD_JS.read_text()
    assert "farm_id=ID" not in content, (
        "field.js still contains 'farm_id=ID' in error message — must be removed"
    )
    assert "field_id=ID" not in content, (
        "field.js still contains 'field_id=ID' in error message — must be removed"
    )
