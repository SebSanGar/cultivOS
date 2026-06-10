/* cultivOS — Login / Register page logic */

(function () {
    'use strict';

    const API = window.location.origin;
    let isRegisterMode = false;

    function t(key) {
        return (window.cultivOS_i18n && window.cultivOS_i18n.t)
            ? window.cultivOS_i18n.t(key)
            : key;
    }

    const form = document.getElementById('login-form');
    const title = document.getElementById('login-title');
    const submitBtn = document.getElementById('login-submit');
    const errorDiv = document.getElementById('login-error');
    const toggleLink = document.getElementById('toggle-register');
    const toggleText = document.getElementById('toggle-text');
    const registerFields = document.getElementById('register-fields');
    const usernameInput = document.getElementById('login-username');
    const passwordInput = document.getElementById('login-password');
    const roleSelect = document.getElementById('register-role');
    const confirmPasswordInput = document.getElementById('register-confirm-password');
    const farmSelect = document.getElementById('register-farm');

    // Fetch farms for the registration dropdown
    (async function loadFarms() {
        try {
            var resp = await fetch(API + '/api/farms/public');
            if (resp.ok) {
                var data = await resp.json();
                var farms = data.items || data || [];
                farms.forEach(function (farm) {
                    var opt = document.createElement('option');
                    opt.value = farm.id;
                    opt.textContent = farm.name;
                    farmSelect.appendChild(opt);
                });
            }
        } catch (e) {
            // Farm list unavailable — user can register without farm
        }
    })();

    function showError(msg) {
        errorDiv.textContent = msg;
        errorDiv.classList.add('visible');
    }

    function hideError() {
        errorDiv.textContent = '';
        errorDiv.classList.remove('visible');
    }

    function setLoading(loading) {
        submitBtn.disabled = loading;
        submitBtn.textContent = loading
            ? (isRegisterMode ? t('login.registering') : t('login.signingIn'))
            : (isRegisterMode ? t('login.register') : t('login.submit'));
    }

    toggleLink.addEventListener('click', function (e) {
        e.preventDefault();
        isRegisterMode = !isRegisterMode;
        hideError();
        if (isRegisterMode) {
            title.setAttribute('data-i18n', 'login.registerSubmit');
            submitBtn.setAttribute('data-i18n', 'login.register');
            toggleText.setAttribute('data-i18n', 'login.hasAccount');
            toggleLink.setAttribute('data-i18n', 'login.signIn');
            registerFields.classList.add('visible');
        } else {
            title.setAttribute('data-i18n', 'login.title');
            submitBtn.setAttribute('data-i18n', 'login.submit');
            toggleText.setAttribute('data-i18n', 'login.noAccount');
            toggleLink.setAttribute('data-i18n', 'login.register');
            registerFields.classList.remove('visible');
        }
        if (window.cultivOS_i18n && window.cultivOS_i18n.applyAll) {
            window.cultivOS_i18n.applyAll();
        }
    });

    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        hideError();

        var username = usernameInput.value.trim();
        var password = passwordInput.value.trim();

        if (!username || !password) {
            showError(t('login.errAllFields'));
            return;
        }

        setLoading(true);

        try {
            if (isRegisterMode) {
                var confirmPassword = confirmPasswordInput.value.trim();
                if (password !== confirmPassword) {
                    showError(t('login.errPasswordMismatch'));
                    setLoading(false);
                    return;
                }
                if (password.length < 6) {
                    showError(t('login.errPasswordShort'));
                    setLoading(false);
                    return;
                }
                var role = roleSelect.value;
                var farmId = farmSelect.value ? parseInt(farmSelect.value, 10) : null;
                var regBody = { username: username, password: password, role: role };
                if (farmId) { regBody.farm_id = farmId; }
                var regResp = await fetch(API + '/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(regBody)
                });

                if (!regResp.ok) {
                    var regData = await regResp.json();
                    showError((regData.error && regData.error.message) || regData.detail || t('login.errRegister'));
                    setLoading(false);
                    return;
                }

                // Auto-login after registration
            }

            var loginResp = await fetch(API + '/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: username, password: password })
            });

            if (!loginResp.ok) {
                var loginData = await loginResp.json();
                showError((loginData.error && loginData.error.message) || loginData.detail || t('login.errBadCredentials'));
                setLoading(false);
                return;
            }

            var tokenData = await loginResp.json();
            localStorage.setItem('cultivOS_token', tokenData.access_token);
            localStorage.setItem('cultivOS_user', username);

            window.location.href = '/';
        } catch (err) {
            showError(t('login.errConnection'));
            setLoading(false);
        }
    });

    // If already logged in, redirect to dashboard
    if (localStorage.getItem('cultivOS_token')) {
        window.location.href = '/';
    }
})();
