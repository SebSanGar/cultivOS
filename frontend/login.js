/* cultivOS — Login / Register page logic */

(function () {
    'use strict';

    const API = window.location.origin;
    let isRegisterMode = false;

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
            var resp = await fetch(API + '/api/farms', {
                headers: { 'Authorization': 'Bearer anonymous' }
            });
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
            ? (isRegisterMode ? 'Registrando...' : 'Entrando...')
            : (isRegisterMode ? 'Registrarse' : 'Entrar');
    }

    toggleLink.addEventListener('click', function (e) {
        e.preventDefault();
        isRegisterMode = !isRegisterMode;
        hideError();
        if (isRegisterMode) {
            title.textContent = 'Crear Cuenta';
            submitBtn.textContent = 'Registrarse';
            toggleText.textContent = 'Ya tienes cuenta?';
            toggleLink.textContent = 'Iniciar Sesion';
            registerFields.classList.add('visible');
        } else {
            title.textContent = 'Iniciar Sesion';
            submitBtn.textContent = 'Entrar';
            toggleText.textContent = 'No tienes cuenta?';
            toggleLink.textContent = 'Registrarse';
            registerFields.classList.remove('visible');
        }
    });

    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        hideError();

        var username = usernameInput.value.trim();
        var password = passwordInput.value.trim();

        if (!username || !password) {
            showError('Por favor, completa todos los campos.');
            return;
        }

        setLoading(true);

        try {
            if (isRegisterMode) {
                var confirmPassword = confirmPasswordInput.value.trim();
                if (password !== confirmPassword) {
                    showError('Las contrasenas no coinciden.');
                    setLoading(false);
                    return;
                }
                if (password.length < 6) {
                    showError('La contrasena debe tener al menos 6 caracteres.');
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
                    showError(regData.detail || 'Error al registrarse. Intenta de nuevo.');
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
                showError(loginData.detail || 'Credenciales incorrectas. Intenta de nuevo.');
                setLoading(false);
                return;
            }

            var tokenData = await loginResp.json();
            localStorage.setItem('cultivOS_token', tokenData.access_token);
            localStorage.setItem('cultivOS_user', username);

            window.location.href = '/';
        } catch (err) {
            showError('No se pudo conectar al servidor. Intenta de nuevo.');
            setLoading(false);
        }
    });

    // If already logged in, redirect to dashboard
    if (localStorage.getItem('cultivOS_token')) {
        window.location.href = '/';
    }
})();
