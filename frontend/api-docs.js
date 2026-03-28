/* -- cultivOS API Docs Page -- api-docs.js -- */

async function fetchJSON(path) {
    try {
        const resp = await fetch(path);
        if (!resp.ok) return null;
        return await resp.json();
    } catch {
        return null;
    }
}

const TAG_ICONS = {
    farms: '&#9878;',
    auth: '&#9919;',
    ndvi: '&#9733;',
    thermal: '&#9832;',
    health: '&#10010;',
    soil: '&#9830;',
    weather: '&#9788;',
    treatments: '&#9883;',
    intelligence: '&#9881;',
    dashboard: '&#9635;',
    alerts: '&#9888;',
    knowledge: '&#9734;',
    diseases: '&#9763;',
    flights: '&#9992;',
    missions: '&#9992;',
    carbon: '&#9752;',
    yield: '&#9650;',
    economics: '&#9733;',
    reports: '&#9776;',
    demo: '&#9654;',
    default: '&#9654;'
};

const TAG_COLORS = {
    farms: '#4da6ff',
    health: '#00c896',
    intelligence: '#00c896',
    treatments: '#00c896',
    soil: '#f0b429',
    ndvi: '#4da6ff',
    thermal: '#ff6b6b',
    weather: '#4da6ff',
    alerts: '#ff6b6b',
    economics: '#f0b429',
    carbon: '#00c896',
    default: '#888'
};

async function initPage() {
    const spec = await fetchJSON('/openapi.json');
    if (!spec) {
        document.getElementById('api-categories').innerHTML =
            '<div class="api-loading">No se pudo cargar la especificacion OpenAPI. Intente de nuevo.</div>';
        return;
    }

    const paths = spec.paths || {};
    const tags = spec.tags || [];

    // Count endpoints
    let endpointCount = 0;
    for (const path of Object.values(paths)) {
        endpointCount += Object.keys(path).filter(m =>
            ['get', 'post', 'put', 'delete', 'patch'].includes(m)
        ).length;
    }

    document.getElementById('api-endpoint-count').textContent = endpointCount;
    document.getElementById('api-tag-count').textContent = tags.length;
    document.getElementById('api-version').textContent = spec.info?.version || '0.1.0';

    // Count endpoints per tag
    const tagCounts = {};
    for (const [pathStr, methods] of Object.entries(paths)) {
        for (const [method, op] of Object.entries(methods)) {
            if (!['get', 'post', 'put', 'delete', 'patch'].includes(method)) continue;
            const opTags = op.tags || ['other'];
            for (const t of opTags) {
                tagCounts[t] = (tagCounts[t] || 0) + 1;
            }
        }
    }

    // Render category cards
    const container = document.getElementById('api-categories');
    if (tags.length === 0) {
        container.innerHTML = '<div class="api-loading">No hay categorias definidas.</div>';
        return;
    }

    container.innerHTML = tags.map(tag => {
        const name = tag.name;
        const desc = tag.description || '';
        const count = tagCounts[name] || 0;
        const icon = TAG_ICONS[name] || TAG_ICONS.default;
        const color = TAG_COLORS[name] || TAG_COLORS.default;
        return `<div class="api-category-card">
            <div class="api-category-header">
                <span class="api-category-icon" style="color:${color}">${icon}</span>
                <span class="api-category-name">${escapeHtml(name)}</span>
                <span class="api-category-count">${count} endpoint${count !== 1 ? 's' : ''}</span>
            </div>
            <p class="api-category-desc">${escapeHtml(desc)}</p>
        </div>`;
    }).join('');

    setupNav();
}

function escapeHtml(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
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

document.addEventListener('DOMContentLoaded', initPage);
