/* -- cultivOS Notification History -- notifications.js -- */

let allNotifications = [];

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

async function loadNotifications() {
    const listEl = document.getElementById('notif-list');
    listEl.innerHTML = '<div class="loading"><div class="loading-spinner"></div>Cargando notificaciones...</div>';

    // Fetch all farms
    const farms = await fetchJSON('/api/farms');
    if (!farms || farms.length === 0) {
        listEl.innerHTML = '<div class="notif-empty">Sin granjas registradas. Cree una granja primero.</div>';
        updateSummary([]);
        return;
    }

    // Fetch notifications from all farms in parallel
    const results = await Promise.all(
        farms.map(async (farm) => {
            const notifs = await fetchJSON(`/api/farms/${farm.id}/notifications`);
            if (!notifs) return [];
            return notifs.map(n => ({ ...n, farm_name: farm.name }));
        })
    );

    allNotifications = results.flat().sort((a, b) =>
        new Date(b.created_at) - new Date(a.created_at)
    );

    updateSummary(allNotifications);
    applyFilters();
}

function updateSummary(notifs) {
    document.getElementById('notif-total').textContent = notifs.length;
    document.getElementById('notif-pending').textContent =
        notifs.filter(n => !n.acknowledged).length;
    document.getElementById('notif-critical').textContent =
        notifs.filter(n => n.severity === 'critical').length;
    document.getElementById('notif-acknowledged').textContent =
        notifs.filter(n => n.acknowledged).length;
}

function applyFilters() {
    const severity = document.getElementById('notif-filter-severity').value;
    const type = document.getElementById('notif-filter-type').value;
    const status = document.getElementById('notif-filter-status').value;

    let filtered = allNotifications;
    if (severity) filtered = filtered.filter(n => n.severity === severity);
    if (type) filtered = filtered.filter(n => n.alert_type === type);
    if (status === 'pending') filtered = filtered.filter(n => !n.acknowledged);
    if (status === 'acknowledged') filtered = filtered.filter(n => n.acknowledged);

    renderList(filtered);
}

function renderList(notifs) {
    const listEl = document.getElementById('notif-list');

    if (notifs.length === 0) {
        listEl.innerHTML = '<div class="notif-empty">Sin notificaciones que coincidan con los filtros.</div>';
        return;
    }

    listEl.innerHTML = notifs.map(n => {
        const severityCls = n.severity === 'critical' ? 'notif-severity-critical'
            : n.severity === 'warning' ? 'notif-severity-warning'
            : 'notif-severity-info';
        const typeLabels = {
            health: 'Salud',
            irrigation: 'Riego',
            pest: 'Plagas',
            recommendation: 'Recomendacion',
            anomaly_health_drop: 'Anomalia Salud',
            anomaly_ndvi_drop: 'Anomalia NDVI',
        };
        const typeLabel = typeLabels[n.alert_type] || n.alert_type;
        const date = new Date(n.created_at).toLocaleString('es-MX', {
            day: '2-digit', month: 'short', year: 'numeric',
            hour: '2-digit', minute: '2-digit'
        });
        const ackBadge = n.acknowledged
            ? '<span class="notif-ack-badge">Reconocida</span>'
            : `<button class="notif-ack-btn" onclick="acknowledgeNotif(${n.farm_id}, ${n.id}, this)">Reconocer</button>`;

        return `<div class="notif-card ${severityCls} ${n.acknowledged ? 'notif-acknowledged' : ''}">
            <div class="notif-card-header">
                <span class="notif-type-badge">${esc(typeLabel)}</span>
                <span class="notif-severity-badge ${severityCls}">${esc(n.severity)}</span>
                <span class="notif-farm-name">${esc(n.farm_name)}</span>
                <span class="notif-date">${date}</span>
            </div>
            <div class="notif-card-body">
                <p class="notif-message">${esc(n.message)}</p>
            </div>
            <div class="notif-card-footer">
                ${ackBadge}
            </div>
        </div>`;
    }).join('');
}

async function acknowledgeNotif(farmId, notifId, btn) {
    btn.disabled = true;
    btn.textContent = 'Procesando...';

    const token = localStorage.getItem('cultivOS_token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = 'Bearer ' + token;

    try {
        const resp = await fetch(`/api/farms/${farmId}/notifications/${notifId}/acknowledge`, {
            method: 'POST',
            headers,
        });
        if (resp.ok) {
            // Update local state
            const notif = allNotifications.find(n => n.id === notifId && n.farm_id === farmId);
            if (notif) notif.acknowledged = true;
            updateSummary(allNotifications);
            applyFilters();
        } else {
            btn.disabled = false;
            btn.textContent = 'Reconocer';
        }
    } catch {
        btn.disabled = false;
        btn.textContent = 'Reconocer';
    }
}

// Auth check
(function checkAuth() {
    const token = localStorage.getItem('cultivOS_token');
    const user = localStorage.getItem('cultivOS_user');
    if (user) {
        document.getElementById('nav-username').textContent = user;
    }
    const logoutLink = document.getElementById('nav-logout');
    if (logoutLink) {
        logoutLink.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('cultivOS_token');
            localStorage.removeItem('cultivOS_user');
            window.location.href = '/login';
        });
    }
})();

// Load on page ready
loadNotifications();
