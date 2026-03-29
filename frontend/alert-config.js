/* -- cultivOS Alert Configuration -- alert-config.js -- */

async function fetchJSON(path) {
    try {
        const token = localStorage.getItem('cultivOS_token');
        const headers = {};
        if (token) headers['Authorization'] = 'Bearer ' + token;
        const resp = await fetch(path, { headers });
        if (!resp.ok) return null;
        return await resp.json();
    } catch {
        return null;
    }
}

function showStatus(msg, isError) {
    const el = document.getElementById('alert-status');
    el.textContent = msg;
    el.style.display = 'block';
    el.style.borderColor = isError ? '#e74c3c' : '#00c896';
    el.style.color = isError ? '#e74c3c' : '#00c896';
    setTimeout(() => { el.style.display = 'none'; }, 4000);
}

// Wire slider labels
function setupSliders() {
    const pairs = [
        ['slider-health', 'slider-health-val', v => Math.round(v)],
        ['slider-ndvi', 'slider-ndvi-val', v => parseFloat(v).toFixed(2)],
        ['slider-temp', 'slider-temp-val', v => Math.round(v)],
    ];
    pairs.forEach(([id, labelId, fmt]) => {
        const slider = document.getElementById(id);
        const label = document.getElementById(labelId);
        if (slider && label) {
            slider.addEventListener('input', () => {
                label.textContent = fmt(slider.value);
            });
        }
    });
}

async function initPage() {
    setupSliders();

    const farms = await fetchJSON('/api/farms');
    const select = document.getElementById('alert-farm-select');
    if (farms && farms.length > 0) {
        farms.forEach(f => {
            const opt = document.createElement('option');
            opt.value = f.id;
            opt.textContent = f.name;
            select.appendChild(opt);
        });
        select.value = farms[0].id;
        loadAlertConfig();
    }
    setupNav();
}

function setupNav() {
    const token = localStorage.getItem('cultivOS_token');
    const userInfo = document.getElementById('nav-user-info');
    const username = document.getElementById('nav-username');
    const logout = document.getElementById('nav-logout');
    if (token && userInfo) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            username.textContent = payload.sub || '';
        } catch { /* ignore */ }
        userInfo.style.display = 'flex';
        logout.onclick = (e) => {
            e.preventDefault();
            localStorage.removeItem('cultivOS_token');
            window.location.href = '/login';
        };
    }
}

async function loadAlertConfig() {
    const farmId = document.getElementById('alert-farm-select').value;
    const currentSection = document.getElementById('alert-current');

    if (!farmId) {
        currentSection.style.display = 'none';
        return;
    }

    const data = await fetchJSON(`/api/farms/${farmId}/alert-config`);

    if (!data) {
        currentSection.style.display = 'none';
        showStatus('No se pudo cargar la configuracion.', true);
        return;
    }

    // Update sliders to current values
    document.getElementById('slider-health').value = data.health_score_floor;
    document.getElementById('slider-health-val').textContent = Math.round(data.health_score_floor);

    document.getElementById('slider-ndvi').value = data.ndvi_minimum;
    document.getElementById('slider-ndvi-val').textContent = parseFloat(data.ndvi_minimum).toFixed(2);

    document.getElementById('slider-temp').value = data.temp_max_c;
    document.getElementById('slider-temp-val').textContent = Math.round(data.temp_max_c);

    // Update current config display
    document.getElementById('current-health').textContent = Math.round(data.health_score_floor);
    document.getElementById('current-ndvi').textContent = parseFloat(data.ndvi_minimum).toFixed(2);
    document.getElementById('current-temp').textContent = Math.round(data.temp_max_c) + ' C';
    currentSection.style.display = '';
}

async function saveAlertConfig() {
    const farmId = document.getElementById('alert-farm-select').value;
    if (!farmId) {
        showStatus('Seleccione una granja primero.', true);
        return;
    }

    const btn = document.getElementById('alert-save-btn');
    btn.disabled = true;
    btn.textContent = 'Guardando...';

    const body = {
        health_score_floor: parseFloat(document.getElementById('slider-health').value),
        ndvi_minimum: parseFloat(document.getElementById('slider-ndvi').value),
        temp_max_c: parseFloat(document.getElementById('slider-temp').value),
    };

    try {
        const token = localStorage.getItem('cultivOS_token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = 'Bearer ' + token;

        const resp = await fetch(`/api/farms/${farmId}/alert-config`, {
            method: 'PUT',
            headers,
            body: JSON.stringify(body),
        });

        if (resp.ok) {
            showStatus('Configuracion guardada exitosamente.', false);
            loadAlertConfig();
        } else {
            showStatus('Error al guardar. Intente de nuevo.', true);
        }
    } catch {
        showStatus('Error de conexion.', true);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Guardar configuracion';
    }
}

document.addEventListener('DOMContentLoaded', initPage);
