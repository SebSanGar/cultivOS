/* -- cultivOS Farm Recommendations -- recommendations.js -- */

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

const URGENCIA_COLORS = {
    alta: '#e74c3c',
    media: '#f0b429',
    baja: '#00c896',
    preventiva: '#4da6ff',
};

async function initPage() {
    const farms = await fetchJSON('/api/farms');
    const select = document.getElementById('recs-farm-select');
    if (farms && farms.length > 0) {
        farms.forEach(f => {
            const opt = document.createElement('option');
            opt.value = f.id;
            opt.textContent = f.name;
            select.appendChild(opt);
        });
        select.value = farms[0].id;
        loadRecommendations();
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

async function loadRecommendations() {
    const farmId = document.getElementById('recs-farm-select').value;
    const cardsEl = document.getElementById('recs-cards');
    const regionEl = document.getElementById('recs-region-info');

    if (!farmId) {
        cardsEl.innerHTML = '<div class="recs-placeholder">Seleccione una granja para ver las recomendaciones de Cerebro.</div>';
        regionEl.style.display = 'none';
        resetStats();
        return;
    }

    cardsEl.innerHTML = '<div class="recs-loading">Generando recomendaciones...</div>';

    const data = await fetchJSON(`/api/farms/${farmId}/recommendations`);

    if (!data || !data.recommendations || data.recommendations.length === 0) {
        cardsEl.innerHTML = '<div class="recs-empty">Sin recomendaciones para esta granja. Asegurese de tener datos de salud en los campos.</div>';
        regionEl.style.display = 'none';
        resetStats();
        return;
    }

    renderRegion(data.region, regionEl);
    updateStats(data.recommendations);
    renderCards(data.recommendations, cardsEl);
}

function resetStats() {
    document.getElementById('recs-total').textContent = '--';
    document.getElementById('recs-urgent').textContent = '--';
    document.getElementById('recs-organic').textContent = '--';
    document.getElementById('recs-fields').textContent = '--';
    document.getElementById('recs-cost').textContent = '--';
}

function updateStats(recs) {
    const total = recs.length;
    const urgent = recs.filter(r => r.urgencia === 'alta').length;
    const organic = recs.filter(r => r.organic).length;
    const fields = new Set(recs.map(r => r.field_id)).size;
    const totalCost = recs.reduce((sum, r) => sum + (r.costo_estimado_mxn || 0), 0);

    document.getElementById('recs-total').textContent = total;
    document.getElementById('recs-urgent').textContent = urgent;
    document.getElementById('recs-organic').textContent = organic;
    document.getElementById('recs-fields').textContent = fields;
    document.getElementById('recs-cost').textContent = '$' + totalCost.toLocaleString() + ' MXN';
}

function renderRegion(region, el) {
    if (!region) {
        el.style.display = 'none';
        return;
    }
    el.style.display = 'block';
    el.innerHTML = `
        <div class="recs-region-grid">
            <div class="recs-region-item"><span class="recs-region-label">Region</span> <span class="recs-region-value">${esc(region.region_name)}</span></div>
            <div class="recs-region-item"><span class="recs-region-label">Clima</span> <span class="recs-region-value">${esc(region.climate_zone)}</span></div>
            <div class="recs-region-item"><span class="recs-region-label">Suelo</span> <span class="recs-region-value">${esc(region.soil_type)}</span></div>
            <div class="recs-region-item"><span class="recs-region-label">Temporada</span> <span class="recs-region-value">${esc(region.growing_season)}</span></div>
            <div class="recs-region-item"><span class="recs-region-label">Cultivos clave</span> <span class="recs-region-value">${esc(region.key_crops.join(', '))}</span></div>
            ${region.seasonal_notes ? `<div class="recs-region-item recs-region-notes"><span class="recs-region-label">Notas</span> <span class="recs-region-value">${esc(region.seasonal_notes)}</span></div>` : ''}
        </div>
    `;
}

function renderCards(recs, container) {
    container.innerHTML = recs.map(rec => {
        const urgColor = URGENCIA_COLORS[rec.urgencia] || '#666';
        const organicBadge = rec.organic ? '<span class="recs-badge recs-badge-organic">Organico</span>' : '';
        const ancestralBadge = rec.metodo_ancestral ? `<span class="recs-badge recs-badge-ancestral">Ancestral: ${esc(rec.metodo_ancestral)}</span>` : '';

        return `
        <div class="recs-card">
            <div class="recs-card-header">
                <div class="recs-card-field">
                    <span class="recs-field-name">${esc(rec.field_name)}</span>
                    ${rec.crop_type ? `<span class="recs-crop-type">${esc(rec.crop_type)}</span>` : ''}
                </div>
                <div class="recs-card-badges">
                    <span class="recs-badge recs-badge-urgencia" style="background:${urgColor}">${esc(rec.urgencia)}</span>
                    ${organicBadge}
                    ${ancestralBadge}
                </div>
            </div>
            <div class="recs-card-body">
                <div class="recs-card-row">
                    <span class="recs-card-label">Problema</span>
                    <span class="recs-card-value">${esc(rec.problema)}</span>
                </div>
                <div class="recs-card-row">
                    <span class="recs-card-label">Causa probable</span>
                    <span class="recs-card-value">${esc(rec.causa_probable)}</span>
                </div>
                <div class="recs-card-row recs-card-treatment">
                    <span class="recs-card-label">Tratamiento</span>
                    <span class="recs-card-value">${esc(rec.tratamiento)}</span>
                </div>
                <div class="recs-card-row">
                    <span class="recs-card-label">Prevencion</span>
                    <span class="recs-card-value">${esc(rec.prevencion)}</span>
                </div>
                ${rec.contexto_regional ? `
                <div class="recs-card-row">
                    <span class="recs-card-label">Contexto regional</span>
                    <span class="recs-card-value">${esc(rec.contexto_regional)}</span>
                </div>` : ''}
                ${rec.base_cientifica ? `
                <div class="recs-card-row">
                    <span class="recs-card-label">Base cientifica</span>
                    <span class="recs-card-value">${esc(rec.base_cientifica)}</span>
                </div>` : ''}
                ${rec.timing_consejo ? `
                <div class="recs-card-row">
                    <span class="recs-card-label">Momento ideal</span>
                    <span class="recs-card-value">${esc(rec.timing_consejo)}</span>
                </div>` : ''}
            </div>
            <div class="recs-card-footer">
                <div class="recs-card-cost">$${(rec.costo_estimado_mxn || 0).toLocaleString()} MXN/ha</div>
                ${rec.costo_estimado_cad ? `<div class="recs-card-cost-cad">$${rec.costo_estimado_cad.toFixed(2)} CAD/ha</div>` : ''}
                <div class="recs-card-health">Salud: <span class="recs-health-score" style="color:${rec.health_score >= 70 ? '#00c896' : rec.health_score >= 40 ? '#f0b429' : '#e74c3c'}">${rec.health_score.toFixed(0)}/100</span></div>
            </div>
        </div>`;
    }).join('');
}

document.addEventListener('DOMContentLoaded', initPage);
