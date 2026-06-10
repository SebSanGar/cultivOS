/* -- cultivOS Notification History -- notifications.js -- */

let allNotifications = [];

// H3 — Strip seed-script marker ` [DEMO]` from farm names before display.
function displayName(name) {
    if (!name) return name;
    return name.replace(/\s*\[DEMO\]$/i, '');
}

function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

// i18n helper — fetch the current-language string for a key.
function t(key) {
    return (window.cultivOS_i18n && window.cultivOS_i18n.t)
        ? window.cultivOS_i18n.t(key)
        : key;
}

// Re-localize any data-i18n nodes that were just injected into the DOM.
function localizeInjected() {
    if (window.cultivOS_i18n && window.cultivOS_i18n.applyAll) {
        window.cultivOS_i18n.applyAll();
    }
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
    listEl.innerHTML = '<div class="loading"><div class="loading-spinner"></div><span data-i18n="notif.loading">Loading notifications...</span></div>';
    localizeInjected();

    // Fetch all farms
    const farms = await fetchJSON('/api/farms');
    if (!farms || farms.length === 0) {
        listEl.innerHTML = '<div class="notif-empty" data-i18n="notif.emptyNoFarms">No farms registered. Create a farm first.</div>';
        localizeInjected();
        updateSummary([]);
        return;
    }

    // Fetch notifications from all farms in parallel
    const results = await Promise.all(
        farms.map(async (farm) => {
            const notifs = await fetchJSON(`/api/farms/${farm.id}/notifications`);
            if (!notifs) return [];
            return notifs.map(n => ({ ...n, farm_name: displayName(farm.name) }));
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
        listEl.innerHTML = '<div class="notif-empty" data-i18n="notif.emptyNoMatch">No notifications match the filters.</div>';
        localizeInjected();
        return;
    }

    const lang = (window.cultivOS_i18n && window.cultivOS_i18n.getLang)
        ? window.cultivOS_i18n.getLang() : 'es';
    const dateLocale = lang === 'en' ? 'en-US' : 'es-MX';

    const typeKeys = {
        health: 'notif.typeHealth',
        irrigation: 'notif.typeIrrigation',
        pest: 'notif.typePest',
        recommendation: 'notif.typeRecommendation',
        anomaly_health_drop: 'notif.typeAnomalyHealth',
        anomaly_ndvi_drop: 'notif.typeAnomalyNdvi',
    };
    const severityKeys = {
        critical: 'notif.severityCritical',
        warning: 'notif.severityWarning',
        info: 'notif.severityInfo',
    };

    listEl.innerHTML = notifs.map(n => {
        const severityCls = n.severity === 'critical' ? 'notif-severity-critical'
            : n.severity === 'warning' ? 'notif-severity-warning'
            : 'notif-severity-info';
        const typeLabel = typeKeys[n.alert_type] ? t(typeKeys[n.alert_type]) : n.alert_type;
        const severityLabel = severityKeys[n.severity] ? t(severityKeys[n.severity]) : n.severity;
        const date = new Date(n.created_at).toLocaleString(dateLocale, {
            day: '2-digit', month: 'short', year: 'numeric',
            hour: '2-digit', minute: '2-digit'
        });
        const ackBadge = n.acknowledged
            ? '<span class="notif-ack-badge" data-i18n="notif.ackBadge">Acknowledged</span>'
            : `<button class="notif-ack-btn" data-i18n="notif.ackBtn" onclick="acknowledgeNotif(${n.farm_id}, ${n.id}, this)">Acknowledge</button>`;

        return `<div class="notif-card ${severityCls} ${n.acknowledged ? 'notif-acknowledged' : ''}">
            <div class="notif-card-header">
                <span class="notif-type-badge">${esc(typeLabel)}</span>
                <span class="notif-severity-badge ${severityCls}">${esc(severityLabel)}</span>
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

    localizeInjected();
}

async function acknowledgeNotif(farmId, notifId, btn) {
    btn.disabled = true;
    btn.removeAttribute('data-i18n');
    btn.textContent = t('notif.processing');

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
            btn.setAttribute('data-i18n', 'notif.ackBtn');
            btn.textContent = t('notif.ackBtn');
        }
    } catch {
        btn.disabled = false;
        btn.setAttribute('data-i18n', 'notif.ackBtn');
        btn.textContent = t('notif.ackBtn');
    }
}

// Load on page ready
loadNotifications();
