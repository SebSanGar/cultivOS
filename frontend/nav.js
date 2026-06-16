/**
 * nav.js — single canonical navigation bar (supersedes per-page <nav> + toggle.js)
 *
 * Renders the dashboard (index.html) nav on every app page so the bar never
 * drifts between pages. Owns the agronomist/farmer view toggle and the mobile
 * hamburger (folded in from the old toggle.js).
 *
 * Load order: include BEFORE i18n.js, at end of <body>. nav.js renders the nav
 * synchronously at execution time so i18n's DOMContentLoaded init localizes the
 * data-i18n labels and wires the ES/EN toggle. The agronomist toggle button
 * carries NO data-i18n (its label is mode-dependent); nav.js owns that label and
 * re-applies it after i18n via a deferred pass to avoid a clobber race.
 *
 * View mode: localStorage 'cultivos_view_mode' ('farmer' default / 'agronomist').
 * Agronomist mode reveals .nav-agronomo-extras and .agronomo-only elements.
 */

(function () {
    'use strict';

    var LS_KEY = 'cultivos_view_mode';
    var MODE_FARMER = 'farmer';
    var MODE_AGRONOMO = 'agronomist';

    // Canonical nav markup. Mirrors index.html. The agronomist toggle button
    // intentionally omits data-i18n — nav.js sets its label per current mode.
    var NAV_HTML =
        '<div class="nav-inner">' +
            '<a href="/" class="nav-logo">cultiv<span>OS</span></a>' +
            '<button id="nav-hamburger" class="nav-hamburger" aria-label="Open menu" aria-expanded="false">' +
                '<span></span><span></span><span></span>' +
            '</button>' +
            '<ul class="nav-farmer-tabs">' +
                '<li><a href="/" data-i18n="nav.farms">My Crops</a></li>' +
                '<li><a href="/notificaciones" data-i18n="nav.alerts">Alerts</a></li>' +
                '<li><a href="/conocimiento" data-i18n="nav.knowledge">Knowledge</a></li>' +
                '<li><a href="/whatsapp-demo" data-i18n="nav.whatsapp">Chat</a></li>' +
            '</ul>' +
            '<ul class="nav-agronomo-extras" hidden>' +
                '<li><a href="/intel" class="nav-tab" data-i18n="nav.intel">Intelligence</a></li>' +
                '<li><a href="/mapa" class="nav-tab" data-i18n="nav.map">Map</a></li>' +
                '<li><a href="/vuelos" class="nav-tab" data-i18n="nav.flights">Flights</a></li>' +
                '<li><a href="/plataforma" class="nav-tab" data-i18n="nav.platform">Platform</a></li>' +
                '<li><a href="/estado" class="nav-tab" data-i18n="nav.status">Status</a></li>' +
            '</ul>' +
            '<button id="agronomo-toggle" class="agronomo-toggle-btn" aria-pressed="false">Agronomist view</button>' +
            '<div class="nav-lang-toggle" role="group" aria-label="Language">' +
                '<span data-lang="es" class="active">ES</span>' +
                '<span data-lang="en">EN</span>' +
            '</div>' +
            '<div id="nav-user-info" class="nav-user-info">' +
                '<span id="nav-username" class="nav-username"></span>' +
                '<a href="#" id="nav-logout" class="nav-logout" data-i18n="user.logout">Log out</a>' +
            '</div>' +
        '</div>';

    function getMode() {
        return localStorage.getItem(LS_KEY) || MODE_FARMER;
    }

    function setMode(mode) {
        localStorage.setItem(LS_KEY, mode);
    }

    // Normalize a path for active-state comparison: drop trailing slash and .html.
    function normPath(p) {
        if (!p) return '/';
        p = p.split('?')[0].split('#')[0];
        if (p.length > 1 && p.charAt(p.length - 1) === '/') p = p.slice(0, -1);
        if (p.slice(-5) === '.html') p = p.slice(0, -5);
        if (p === '/index') p = '/';
        return p || '/';
    }

    // Set .active on the canonical link matching the current path.
    function setActive(nav) {
        var here = normPath(window.location.pathname);
        // Only tab links get active state — never the logo or user-menu links.
        var links = nav.querySelectorAll('.nav-farmer-tabs a, .nav-agronomo-extras a');
        for (var i = 0; i < links.length; i++) {
            var href = links[i].getAttribute('href');
            if (!href || href === '#' || href.indexOf('http') === 0) continue;
            links[i].classList.toggle('active', normPath(href) === here);
        }
    }

    // Apply view mode: reveal/hide agronomist sections + set toggle label.
    function applyMode(mode) {
        var isAgronomo = mode === MODE_AGRONOMO;

        var hideTargets = document.querySelectorAll('.agronomo-only, .nav-agronomo-extras');
        for (var i = 0; i < hideTargets.length; i++) {
            if (isAgronomo) {
                hideTargets[i].removeAttribute('hidden');
            } else {
                hideTargets[i].setAttribute('hidden', '');
            }
        }

        var btn = document.getElementById('agronomo-toggle');
        if (btn) {
            var i18n = window.cultivOS_i18n;
            btn.textContent = (i18n && i18n.t)
                ? i18n.t(isAgronomo ? 'toggle.farmer' : 'toggle.agronomo')
                : (isAgronomo ? 'Farmer view' : 'Agronomist view');
            btn.setAttribute('aria-pressed', isAgronomo ? 'true' : 'false');
        }
    }

    function handleToggleClick() {
        var next = getMode() === MODE_AGRONOMO ? MODE_FARMER : MODE_AGRONOMO;
        setMode(next);
        applyMode(next);
    }

    function wire(nav) {
        var btn = document.getElementById('agronomo-toggle');
        if (btn) btn.addEventListener('click', handleToggleClick);

        var hamburger = document.getElementById('nav-hamburger');
        if (hamburger) {
            hamburger.addEventListener('click', function () {
                var inner = hamburger.closest('.nav-inner');
                if (!inner) return;
                var isOpen = inner.classList.toggle('nav-open');
                hamburger.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
            });
        }

        // Re-apply the mode label after i18n's lang switch (i18n won't touch the
        // toggle button — it has no data-i18n — so nav.js keeps it in sync).
        var langToggle = nav.querySelector('.nav-lang-toggle');
        if (langToggle) {
            langToggle.addEventListener('click', function () {
                // Defer so this runs after i18n's own switchLang handler.
                setTimeout(function () { applyMode(getMode()); }, 0);
            });
        }
    }

    function render() {
        var nav = document.querySelector('nav');
        if (nav) {
            nav.innerHTML = NAV_HTML;
            nav.removeAttribute('class'); // canonical bare <nav> styling
        } else if (document.body) {
            nav = document.createElement('nav');
            nav.innerHTML = NAV_HTML;
            document.body.insertBefore(nav, document.body.firstChild);
        } else {
            return;
        }

        setActive(nav);
        applyMode(getMode());
        wire(nav);

        // i18n loads after nav.js; once its DOMContentLoaded runs applyAll, the
        // toggle label may need re-applying with the correct localized string.
        setTimeout(function () { applyMode(getMode()); }, 0);
    }

    if (document.body) {
        render();
    } else if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', render);
    } else {
        render();
    }
})();
