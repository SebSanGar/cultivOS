/* -- cultivOS Platform Status -- status.js -- */

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

function formatUptime(seconds) {
    if (seconds == null) return '--';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) return h + 'h ' + m + 'm';
    if (m > 0) return m + 'm ' + s + 's';
    return s + 's';
}

function formatTimestamp(iso) {
    if (!iso) return 'Sin datos';
    const d = new Date(iso);
    const now = new Date();
    const diffMs = now - d;
    const diffH = Math.floor(diffMs / 3600000);
    const diffD = Math.floor(diffMs / 86400000);
    if (diffD > 30) return d.toLocaleDateString('es-MX');
    if (diffD > 0) return 'hace ' + diffD + 'd';
    if (diffH > 0) return 'hace ' + diffH + 'h';
    return 'hace <1h';
}

function freshnessClass(iso) {
    if (!iso) return 'status-stale';
    const diffMs = Date.now() - new Date(iso).getTime();
    const diffD = diffMs / 86400000;
    if (diffD <= 1) return 'status-fresh';
    if (diffD <= 7) return 'status-aging';
    return 'status-stale';
}

// Core endpoints to check
const ENDPOINTS = [
    { path: '/api/status', name: 'Estado' },
    { path: '/api/farms', name: 'Granjas' },
    { path: '/api/knowledge/fertilizers', name: 'Fertilizantes' },
    { path: '/api/knowledge/crops', name: 'Cultivos' },
    { path: '/api/knowledge/ancestral', name: 'Metodos Ancestrales' },
];

async function checkEndpoint(ep) {
    try {
        const token = localStorage.getItem('cultivOS_token');
        const headers = {};
        if (token) headers['Authorization'] = 'Bearer ' + token;
        const resp = await fetch(ep.path, { headers });
        return { ...ep, ok: resp.ok, status: resp.status };
    } catch {
        return { ...ep, ok: false, status: 0 };
    }
}

async function loadStatus() {
    // Fetch platform status
    const data = await fetchJSON('/api/status');

    if (data) {
        document.getElementById('status-api-version').textContent = data.api_version || '--';
        document.getElementById('status-uptime').textContent = formatUptime(data.uptime_seconds);
        document.getElementById('status-farms').textContent = data.total_farms;
        document.getElementById('status-fields').textContent = data.total_fields;

        // DB health — if we got a response, DB is connected
        document.getElementById('status-db-indicator').classList.add('status-ok');
        document.getElementById('status-db-badge').textContent = 'OK';
        document.getElementById('status-db-badge').classList.add('status-badge-ok');
        document.getElementById('status-api-indicator').classList.add('status-ok');

        // Data freshness
        const latest = data.latest_data || {};
        ['soil', 'ndvi', 'thermal', 'weather'].forEach(function(key) {
            const el = document.getElementById('status-' + key + '-ts');
            el.textContent = formatTimestamp(latest[key]);
            el.className = 'status-ts ' + freshnessClass(latest[key]);
        });
    } else {
        document.getElementById('status-db-indicator').classList.add('status-err');
        document.getElementById('status-db-badge').textContent = 'Error';
        document.getElementById('status-db-badge').classList.add('status-badge-err');
    }

    // Check endpoints
    const results = await Promise.all(ENDPOINTS.map(checkEndpoint));
    const container = document.getElementById('status-endpoints');
    const okCount = results.filter(function(r) { return r.ok; }).length;
    document.getElementById('status-endpoints-count').textContent = okCount + '/' + results.length;

    container.innerHTML = results.map(function(r) {
        var cls = r.ok ? 'status-ep-ok' : 'status-ep-err';
        return '<div class="status-check-row">' +
            '<span class="status-check-label">' + r.name + '</span>' +
            '<span class="status-ep-badge ' + cls + '">' + (r.ok ? r.status : 'Error') + '</span>' +
            '</div>';
    }).join('');
}

// Load on page ready
loadStatus();
