/* cultivOS — Auth guard + nav user info */

(function () {
    'use strict';

    // Redirect to login if no token
    if (!localStorage.getItem('cultivOS_token')) {
        window.location.href = '/login';
        return;
    }

    // Populate nav user info
    var username = localStorage.getItem('cultivOS_user') || 'Usuario';
    var userInfo = document.getElementById('nav-user-info');
    if (userInfo) {
        var nameSpan = document.getElementById('nav-username');
        if (nameSpan) nameSpan.textContent = username;
    }

    // Logout handler
    var logoutBtn = document.getElementById('nav-logout');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function (e) {
            e.preventDefault();
            localStorage.removeItem('cultivOS_token');
            localStorage.removeItem('cultivOS_user');
            window.location.href = '/login';
        });
    }
})();
