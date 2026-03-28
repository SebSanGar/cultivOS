/* -- cultivOS Drone Flight Log -- flights.js -- */

let allFlights = [];
let currentSort = { key: 'flight_date', asc: false };

function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

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

const DRONE_LABELS = {
    mavic_multispectral: 'Mavic 3 Multispectral',
    mavic_thermal: 'Mavic 3 Thermal',
    agras_t100: 'Agras T100',
};

const MISSION_LABELS = {
    health_scan: 'Escaneo de salud',
    thermal_check: 'Revision termica',
    spray: 'Aplicacion',
};

const STATUS_LABELS = {
    pending: 'Pendiente',
    processing: 'Procesando',
    complete: 'Completo',
    failed: 'Fallido',
};

const STATUS_COLORS = {
    pending: '#f0b429',
    processing: '#4da6ff',
    complete: '#00c896',
    failed: '#e74c3c',
};

async function loadFlights() {
    const tbody = document.getElementById('flights-table-body');
    tbody.innerHTML = '<tr><td colspan="10" class="flights-loading">Cargando vuelos...</td></tr>';

    const farms = await fetchJSON('/api/farms');
    if (!farms || farms.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="flights-empty">Sin granjas registradas. Cree una granja primero.</td></tr>';
        updateStats([]);
        return;
    }

    const collected = [];
    for (const farm of farms) {
        const fields = await fetchJSON(`/api/farms/${farm.id}/fields`);
        if (!fields) continue;
        for (const field of fields) {
            const flights = await fetchJSON(`/api/farms/${farm.id}/fields/${field.id}/flights`);
            if (!flights) continue;
            for (const f of flights) {
                collected.push({
                    ...f,
                    farm_name: farm.name,
                    farm_id: farm.id,
                    field_name: field.name,
                    field_id: field.id,
                });
            }
        }
    }

    allFlights = collected;
    applyFilters();
}

function applyFilters() {
    const droneFilter = document.getElementById('flights-filter-drone').value;
    const missionFilter = document.getElementById('flights-filter-mission').value;

    let filtered = allFlights;
    if (droneFilter) filtered = filtered.filter(f => f.drone_type === droneFilter);
    if (missionFilter) filtered = filtered.filter(f => f.mission_type === missionFilter);

    filtered = sortFlights(filtered);
    updateStats(filtered);
    renderTable(filtered);
}

function sortFlights(flights) {
    const { key, asc } = currentSort;
    return [...flights].sort((a, b) => {
        let va = a[key], vb = b[key];
        if (typeof va === 'string') va = va.toLowerCase();
        if (typeof vb === 'string') vb = vb.toLowerCase();
        if (va < vb) return asc ? -1 : 1;
        if (va > vb) return asc ? 1 : -1;
        return 0;
    });
}

function sortBy(key) {
    if (currentSort.key === key) {
        currentSort.asc = !currentSort.asc;
    } else {
        currentSort = { key, asc: true };
    }
    applyFilters();
}

function updateStats(flights) {
    document.getElementById('flights-total').textContent = flights.length;

    const totalMinutes = flights.reduce((s, f) => s + (f.duration_minutes || 0), 0);
    document.getElementById('flights-hours').textContent = (totalMinutes / 60).toFixed(1);

    const totalHa = flights.reduce((s, f) => s + (f.coverage_pct || 0), 0);
    document.getElementById('flights-hectares').textContent = totalHa.toFixed(1);

    const totalImages = flights.reduce((s, f) => s + (f.images_count || 0), 0);
    document.getElementById('flights-images').textContent = totalImages.toLocaleString();

    const drones = new Set(flights.map(f => f.drone_type));
    document.getElementById('flights-drones').textContent = drones.size;
}

function renderTable(flights) {
    const tbody = document.getElementById('flights-table-body');

    if (flights.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="flights-empty">Sin vuelos registrados. Los vuelos aparecen al registrar misiones de drones.</td></tr>';
        return;
    }

    tbody.innerHTML = flights.map(f => {
        const date = f.flight_date ? new Date(f.flight_date).toLocaleDateString('es-MX', { year: 'numeric', month: 'short', day: 'numeric' }) : '--';
        const drone = DRONE_LABELS[f.drone_type] || esc(f.drone_type);
        const mission = MISSION_LABELS[f.mission_type] || esc(f.mission_type);
        const status = STATUS_LABELS[f.status] || esc(f.status);
        const statusColor = STATUS_COLORS[f.status] || '#666';
        const duration = f.duration_minutes ? `${f.duration_minutes} min` : '--';
        const altitude = f.altitude_m ? `${f.altitude_m} m` : '--';
        const coverage = f.coverage_pct != null ? `${f.coverage_pct}%` : '--';
        const images = f.images_count != null ? f.images_count : '--';

        return `<tr>
            <td class="flights-cell-date">${date}</td>
            <td>${esc(f.farm_name)}</td>
            <td><a href="/campo?farm=${f.farm_id}&field=${f.field_id}" class="flights-field-link">${esc(f.field_name)}</a></td>
            <td><span class="flights-drone-badge">${drone}</span></td>
            <td>${mission}</td>
            <td class="flights-cell-mono">${duration}</td>
            <td class="flights-cell-mono">${altitude}</td>
            <td class="flights-cell-mono">${coverage}</td>
            <td class="flights-cell-mono">${images}</td>
            <td><span class="flights-status" style="color:${statusColor}">${status}</span></td>
        </tr>`;
    }).join('');
}

// Auth check
(function checkAuth() {
    const token = localStorage.getItem('cultivOS_token');
    const username = localStorage.getItem('cultivOS_username');
    if (username) {
        const el = document.getElementById('nav-username');
        if (el) el.textContent = username;
    }
    const logoutBtn = document.getElementById('nav-logout');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            localStorage.removeItem('cultivOS_token');
            localStorage.removeItem('cultivOS_username');
            window.location.href = '/login';
        });
    }
})();

// Load on page ready
loadFlights();
