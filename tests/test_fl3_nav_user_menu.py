"""FL3 — Nav + user menu rebuild tests.

Verifies:
- styles.css has avatar chip + dropdown CSS using FL1 tokens
- auth-guard.js injects the dropdown dynamically (avatar initial, role, logout)
- auth-guard.js has accessible behavior: aria-expanded, Escape key, click-outside
- auth-guard.js decodes JWT to extract username + role
- notifications.html + whatsapp-demo.html include auth-guard.js
"""

import re
from pathlib import Path

import pytest

FRONTEND = Path(__file__).parent.parent / "frontend"
STYLES = FRONTEND / "styles.css"
AUTH_GUARD = FRONTEND / "auth-guard.js"
NOTIFICATIONS = FRONTEND / "notifications.html"
WHATSAPP_DEMO = FRONTEND / "whatsapp-demo.html"


@pytest.fixture
def css_text():
    assert STYLES.exists(), "frontend/styles.css not found"
    return STYLES.read_text(encoding="utf-8")


@pytest.fixture
def auth_guard_text():
    assert AUTH_GUARD.exists(), "frontend/auth-guard.js not found"
    return AUTH_GUARD.read_text(encoding="utf-8")


# ── CSS: avatar chip ──

def test_nav_user_chip_class_exists(css_text):
    """styles.css must define .nav-user-chip for the avatar initial button."""
    assert ".nav-user-chip" in css_text, (
        ".nav-user-chip CSS class missing from styles.css. "
        "Add it for the avatar initial button."
    )


def test_nav_user_dropdown_class_exists(css_text):
    """styles.css must define .nav-user-dropdown for the dropdown panel."""
    assert ".nav-user-dropdown" in css_text, (
        ".nav-user-dropdown CSS class missing from styles.css. "
        "Add it for the avatar dropdown panel."
    )


def test_nav_user_chip_uses_tokens(css_text):
    """Avatar chip must use FL1 CSS tokens, not raw hex colors."""
    chip_block = re.search(
        r"\.nav-user-chip\s*\{([^}]+)\}", css_text, re.DOTALL
    )
    assert chip_block, ".nav-user-chip CSS rule not found"
    block = chip_block.group(1)
    raw_hex = re.findall(r":\s*#[0-9a-fA-F]{3,8}", block)
    assert len(raw_hex) == 0, (
        f".nav-user-chip uses raw hex colors {raw_hex}. "
        "Use FL1 CSS variables (var(--brand-green), var(--neutral-*), etc.)."
    )


def test_nav_user_dropdown_hidden_by_default(css_text):
    """Dropdown panel must be hidden by default (display:none or visibility)."""
    dropdown_block = re.search(
        r"\.nav-user-dropdown\s*\{([^}]+)\}", css_text, re.DOTALL
    )
    assert dropdown_block, ".nav-user-dropdown CSS rule not found"
    block = dropdown_block.group(1)
    assert "display: none" in block or "display:none" in block or "visibility: hidden" in block, (
        ".nav-user-dropdown must be hidden by default. Add 'display: none;'."
    )


# ── auth-guard.js: dropdown injection ──

def test_auth_guard_has_chip_class_reference(auth_guard_text):
    """auth-guard.js must reference nav-user-chip to build the avatar chip HTML."""
    assert "nav-user-chip" in auth_guard_text, (
        "auth-guard.js does not reference 'nav-user-chip'. "
        "It must inject the avatar chip HTML into #nav-user-info."
    )


def test_auth_guard_has_dropdown_class_reference(auth_guard_text):
    """auth-guard.js must reference nav-user-dropdown to build the dropdown HTML."""
    assert "nav-user-dropdown" in auth_guard_text, (
        "auth-guard.js does not reference 'nav-user-dropdown'. "
        "It must inject the dropdown panel HTML."
    )


def test_auth_guard_has_aria_expanded(auth_guard_text):
    """auth-guard.js must toggle aria-expanded for accessibility."""
    assert "aria-expanded" in auth_guard_text, (
        "auth-guard.js missing aria-expanded toggle. "
        "The avatar chip button must set aria-expanded='true'/'false'."
    )


def test_auth_guard_has_escape_handler(auth_guard_text):
    """auth-guard.js must close the dropdown on Escape key."""
    has_escape = "Escape" in auth_guard_text or "keydown" in auth_guard_text
    assert has_escape, (
        "auth-guard.js missing Escape key handler. "
        "Add document keydown listener that closes dropdown on Escape."
    )


def test_auth_guard_has_click_outside(auth_guard_text):
    """auth-guard.js must close dropdown when clicking outside."""
    has_click_outside = (
        "document.addEventListener" in auth_guard_text
        and "click" in auth_guard_text
        and ("contains" in auth_guard_text or "closest" in auth_guard_text)
    )
    assert has_click_outside, (
        "auth-guard.js missing click-outside handler. "
        "Add document click listener that closes dropdown when clicking outside the chip."
    )


def test_auth_guard_decodes_jwt_role(auth_guard_text):
    """auth-guard.js must decode JWT payload to extract role for display."""
    has_decode = (
        "atob(" in auth_guard_text
        and ("split('.')" in auth_guard_text or 'split(".")' in auth_guard_text)
    )
    assert has_decode, (
        "auth-guard.js does not decode JWT. "
        "Add JWT payload decode: token.split('.')[1] + atob() to extract role."
    )


def test_auth_guard_references_role_display(auth_guard_text):
    """auth-guard.js must display the role value from JWT payload."""
    assert "role" in auth_guard_text, (
        "auth-guard.js does not reference 'role'. "
        "Must extract and display role from JWT payload in the dropdown."
    )


# ── Farmer pages: auth-guard.js must be included ──

def test_notifications_has_auth_guard():
    """notifications.html must include auth-guard.js for user control."""
    content = NOTIFICATIONS.read_text(encoding="utf-8")
    assert 'src="/auth-guard.js"' in content, (
        "notifications.html missing auth-guard.js script tag. "
        "Add <script src=\"/auth-guard.js\"></script> before other scripts."
    )


def test_whatsapp_demo_has_auth_guard():
    """whatsapp-demo.html must include auth-guard.js for user control."""
    content = WHATSAPP_DEMO.read_text(encoding="utf-8")
    assert 'src="/auth-guard.js"' in content, (
        "whatsapp-demo.html missing auth-guard.js script tag. "
        "Add <script src=\"/auth-guard.js\"></script> before other scripts."
    )
