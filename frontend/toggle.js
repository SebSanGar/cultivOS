/**
 * toggle.js — Agronomist / Farmer view toggle (F8)
 *
 * Reads `cultivos_view_mode` from localStorage ('farmer' default, 'agronomist' expanded).
 * Applies mode on page load and on button click.
 *
 * Farmer mode (default):
 *   - .agronomo-only elements → hidden
 *   - .nav-agronomo-extras elements → hidden
 *   - #agronomo-toggle label → "Vista agronomo"
 *
 * Agronomist mode:
 *   - .agronomo-only elements → visible (remove hidden attribute)
 *   - .nav-agronomo-extras elements → visible
 *   - #agronomo-toggle label → "Vista productor"
 */

(function () {
    'use strict';

    var LS_KEY = 'cultivos_view_mode';
    var MODE_FARMER = 'farmer';
    var MODE_AGRONOMO = 'agronomist';

    function getMode() {
        return localStorage.getItem(LS_KEY) || MODE_FARMER;
    }

    function setMode(mode) {
        localStorage.setItem(LS_KEY, mode);
    }

    function applyMode(mode) {
        var isAgronomo = mode === MODE_AGRONOMO;

        // Show/hide .agronomo-only sections (field.html: #agronomo-bloque-principal etc.)
        var agroOnly = document.querySelectorAll('.agronomo-only');
        for (var i = 0; i < agroOnly.length; i++) {
            if (isAgronomo) {
                agroOnly[i].removeAttribute('hidden');
            } else {
                agroOnly[i].setAttribute('hidden', '');
            }
        }

        // Show/hide .nav-agronomo-extras nav lists
        var agroExtras = document.querySelectorAll('.nav-agronomo-extras');
        for (var j = 0; j < agroExtras.length; j++) {
            if (isAgronomo) {
                agroExtras[j].removeAttribute('hidden');
            } else {
                agroExtras[j].setAttribute('hidden', '');
            }
        }

        // Update toggle button label
        var btn = document.getElementById('agronomo-toggle');
        if (btn) {
            btn.textContent = isAgronomo ? 'Vista productor' : 'Vista agronomo';
            btn.setAttribute('aria-pressed', isAgronomo ? 'true' : 'false');
        }
    }

    function handleToggleClick() {
        var current = getMode();
        var next = current === MODE_AGRONOMO ? MODE_FARMER : MODE_AGRONOMO;
        setMode(next);
        applyMode(next);
    }

    function init() {
        // Apply persisted mode on load
        applyMode(getMode());

        // Wire up button
        var btn = document.getElementById('agronomo-toggle');
        if (btn) {
            btn.addEventListener('click', handleToggleClick);
        }
    }

    // Run after DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
