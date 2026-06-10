/* cultivOS — Auth guard + nav user menu */

(function () {
    'use strict';

    var token = localStorage.getItem('cultivOS_token');

    // Redirect to login if no token
    if (!token) {
        window.location.href = '/login';
        return;
    }

    // Decode JWT payload (display-only — no signature verification needed)
    function parseJwt(t) {
        try {
            var base64 = t.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
            return JSON.parse(atob(base64));
        } catch (e) {
            return {};
        }
    }

    var payload = parseJwt(token);
    var username = payload.username || localStorage.getItem('cultivOS_user') || 'Usuario';
    var role = payload.role || '';

    // Role label mapping (Spanish display)
    var roleLabels = { farmer: 'Agricultor', researcher: 'Investigador', admin: 'Administrador' };
    var roleLabel = roleLabels[role] || role;

    // Avatar: first letter of username, uppercased
    var initial = (username.charAt(0) || 'U').toUpperCase();

    // Inject avatar chip + dropdown into #nav-user-info
    var userInfo = document.getElementById('nav-user-info');
    if (userInfo) {
        userInfo.innerHTML =
            '<button class="nav-user-chip" id="nav-user-chip" aria-haspopup="true" aria-expanded="false">' +
                initial +
            '</button>' +
            '<div class="nav-user-dropdown" id="nav-user-dropdown" role="menu">' +
                '<div class="nav-user-dropdown-name">' + username + '</div>' +
                '<div class="nav-user-dropdown-role">' + roleLabel + '</div>' +
                '<hr class="nav-user-dropdown-divider">' +
                '<button class="nav-user-dropdown-logout" id="nav-logout" role="menuitem">Salir</button>' +
            '</div>';

        var chip = document.getElementById('nav-user-chip');
        var dropdown = document.getElementById('nav-user-dropdown');

        // Toggle dropdown open/close
        chip.addEventListener('click', function (e) {
            e.stopPropagation();
            var open = chip.getAttribute('aria-expanded') === 'true';
            chip.setAttribute('aria-expanded', open ? 'false' : 'true');
            dropdown.style.display = open ? 'none' : 'block';
        });

        // Close on Escape key
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                chip.setAttribute('aria-expanded', 'false');
                dropdown.style.display = 'none';
            }
        });

        // Close on click outside
        document.addEventListener('click', function (e) {
            if (!userInfo.contains(e.target)) {
                chip.setAttribute('aria-expanded', 'false');
                dropdown.style.display = 'none';
            }
        });

        // Logout handler
        var logoutBtn = document.getElementById('nav-logout');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', function () {
                localStorage.removeItem('cultivOS_token');
                localStorage.removeItem('cultivOS_user');
                window.location.href = '/login';
            });
        }
    }
})();
