/* cultivOS — Knowledge Base Page */

const API = 'http://localhost:8000';

async function fetchJSON(url) {
    const resp = await fetch(url);
    if (!resp.ok) return [];
    return resp.json();
}

/* ── Render functions ── */

function renderAncestral(methods) {
    const container = document.getElementById('ancestral-cards');
    if (!methods || methods.length === 0) {
        container.innerHTML = '<p class="knowledge-empty">No se encontraron metodos ancestrales.</p>';
        return;
    }
    container.innerHTML = methods.map(m => `
        <div class="knowledge-card" data-search="${(m.name + ' ' + m.description_es + ' ' + m.region + ' ' + m.practice_type + ' ' + (m.crops || []).join(' ')).toLowerCase()}">
            <div class="knowledge-card-header">
                <h3 class="knowledge-card-title">${m.name}</h3>
                <span class="knowledge-badge knowledge-badge-type">${m.practice_type}</span>
            </div>
            <p class="knowledge-card-desc">${m.description_es}</p>
            <div class="knowledge-card-meta">
                <span class="knowledge-meta-item"><strong>Region:</strong> ${m.region}</span>
                <span class="knowledge-meta-item"><strong>Cultivos:</strong> ${(m.crops || []).join(', ')}</span>
            </div>
            <p class="knowledge-card-benefits"><strong>Beneficios:</strong> ${m.benefits_es}</p>
            ${m.scientific_basis ? `<p class="knowledge-card-science"><strong>Base cientifica:</strong> ${m.scientific_basis}</p>` : ''}
        </div>
    `).join('');
}

function renderCrops(crops) {
    const container = document.getElementById('crop-cards');
    if (!crops || crops.length === 0) {
        container.innerHTML = '<p class="knowledge-empty">No se encontraron cultivos.</p>';
        return;
    }
    container.innerHTML = crops.map(c => `
        <div class="knowledge-card" data-search="${(c.name + ' ' + c.family + ' ' + c.description_es + ' ' + (c.regions || []).join(' ') + ' ' + (c.companions || []).join(' ')).toLowerCase()}">
            <div class="knowledge-card-header">
                <h3 class="knowledge-card-title">${c.name}</h3>
                <span class="knowledge-badge knowledge-badge-family">${c.family}</span>
            </div>
            <p class="knowledge-card-desc">${c.description_es}</p>
            <div class="knowledge-card-meta">
                <span class="knowledge-meta-item"><strong>Temporada:</strong> ${c.growing_season}</span>
                <span class="knowledge-meta-item"><strong>Agua:</strong> ${c.water_needs}</span>
                ${c.days_to_harvest ? `<span class="knowledge-meta-item"><strong>Cosecha:</strong> ${c.days_to_harvest} dias</span>` : ''}
            </div>
            <div class="knowledge-card-meta">
                <span class="knowledge-meta-item"><strong>Regiones:</strong> ${(c.regions || []).join(', ')}</span>
                <span class="knowledge-meta-item"><strong>Companeros:</strong> ${(c.companions || []).join(', ')}</span>
            </div>
            ${c.optimal_temp_min != null ? `<p class="knowledge-card-temp"><strong>Temp optima:</strong> ${c.optimal_temp_min} - ${c.optimal_temp_max} C</p>` : ''}
        </div>
    `).join('');
}

function renderFertilizers(fertilizers) {
    const container = document.getElementById('fertilizer-cards');
    if (!fertilizers || fertilizers.length === 0) {
        container.innerHTML = '<p class="knowledge-empty">No se encontraron fertilizantes.</p>';
        return;
    }
    container.innerHTML = fertilizers.map(f => `
        <div class="knowledge-card" data-search="${(f.name + ' ' + f.description_es + ' ' + f.nutrient_profile + ' ' + (f.suitable_crops || []).join(' ')).toLowerCase()}">
            <div class="knowledge-card-header">
                <h3 class="knowledge-card-title">${f.name}</h3>
                <span class="knowledge-badge knowledge-badge-cost">$${f.cost_per_ha_mxn.toLocaleString()} MXN/ha</span>
            </div>
            <p class="knowledge-card-desc">${f.description_es}</p>
            <div class="knowledge-card-meta">
                <span class="knowledge-meta-item"><strong>Aplicacion:</strong> ${f.application_method}</span>
                <span class="knowledge-meta-item"><strong>Nutrientes:</strong> ${f.nutrient_profile}</span>
            </div>
            <p class="knowledge-card-crops"><strong>Cultivos:</strong> ${(f.suitable_crops || []).join(', ')}</p>
        </div>
    `).join('');
}

function renderDiseases(diseases) {
    const container = document.getElementById('disease-cards');
    if (!container) return;
    if (!diseases || diseases.length === 0) {
        container.innerHTML = '<p class="knowledge-empty">No se encontraron enfermedades.</p>';
        return;
    }
    container.innerHTML = diseases.map(d => {
        const severityClass = d.severity === 'alta' ? 'severity-high' : d.severity === 'media' ? 'severity-med' : 'severity-low';
        return `
        <div class="knowledge-card" data-search="${(d.name + ' ' + d.description_es + ' ' + (d.affected_crops || []).join(' ') + ' ' + (d.symptoms || []).join(' ')).toLowerCase()}">
            <div class="knowledge-card-header">
                <h3 class="knowledge-card-title">${d.name}</h3>
                <span class="knowledge-badge ${severityClass}">${d.severity}</span>
            </div>
            <p class="knowledge-card-desc">${d.description_es}</p>
            <div class="knowledge-card-meta">
                <span class="knowledge-meta-item"><strong>Cultivos:</strong> ${(d.affected_crops || []).join(', ')}</span>
                <span class="knowledge-meta-item"><strong>Region:</strong> ${d.region}</span>
            </div>
            <p class="knowledge-card-symptoms"><strong>Sintomas:</strong> ${(d.symptoms || []).join(', ')}</p>
            <div class="knowledge-card-treatments">
                <strong>Tratamientos:</strong>
                ${(d.treatments || []).map(t =>
                    `<span class="treatment-tag${t.organic ? ' organic' : ''}">${t.name}</span>`
                ).join(' ')}
            </div>
        </div>`;
    }).join('');
}

function renderIdentifyResults(matches) {
    const container = document.getElementById('identify-results');
    if (!container) return;
    if (!matches || matches.length === 0) {
        container.innerHTML = '<p class="knowledge-empty">No se encontraron coincidencias.</p>';
        return;
    }
    container.innerHTML = '<h3 class="identify-results-title">Resultados</h3>' +
        matches.filter(m => m.confidence > 0).map(m => `
        <div class="identify-match">
            <div class="identify-match-header">
                <strong>${m.name}</strong>
                <span class="confidence-bar" style="width:${Math.round(m.confidence * 100)}%">${Math.round(m.confidence * 100)}%</span>
            </div>
            <p>${m.description_es}</p>
            <p><strong>Sintomas coincidentes:</strong> ${(m.symptoms_matched || []).join(', ')}</p>
            <div class="knowledge-card-treatments">
                ${(m.treatments || []).map(t =>
                    `<span class="treatment-tag${t.organic ? ' organic' : ''}">${t.name}</span>`
                ).join(' ')}
            </div>
        </div>
    `).join('');
}

async function handleIdentify(e) {
    e.preventDefault();
    const symptomsInput = document.getElementById('identify-symptoms').value.trim();
    const cropInput = document.getElementById('identify-crop').value.trim();
    if (!symptomsInput) return;
    const symptoms = symptomsInput.split(',').map(s => s.trim()).filter(Boolean);
    const body = { symptoms };
    if (cropInput) body.crop = cropInput;
    const resp = await fetch(`${API}/api/knowledge/diseases/identify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!resp.ok) {
        document.getElementById('identify-results').innerHTML = '<p class="knowledge-empty">Error al identificar.</p>';
        return;
    }
    const matches = await resp.json();
    renderIdentifyResults(matches);
}

/* ── Stats ── */

function updateStats(ancestral, crops, fertilizers, diseases) {
    const el = id => document.getElementById(id);
    if (el('stat-ancestrales')) el('stat-ancestrales').textContent = (ancestral || []).length;
    if (el('stat-cultivos')) el('stat-cultivos').textContent = (crops || []).length;
    if (el('stat-fertilizantes')) el('stat-fertilizantes').textContent = (fertilizers || []).length;
    if (el('stat-enfermedades')) el('stat-enfermedades').textContent = (diseases || []).length;
}

/* ── Search / Filter ── */

function filterAll() {
    const searchInput = document.getElementById('search-input');
    const categoryFilter = document.getElementById('category-filter');
    const q = (searchInput ? searchInput.value : '').toLowerCase().trim();
    const cat = categoryFilter ? categoryFilter.value : '';

    // Filter sections by category
    document.querySelectorAll('.knowledge-section[data-category]').forEach(section => {
        if (cat && section.getAttribute('data-category') !== cat) {
            section.style.display = 'none';
        } else {
            section.style.display = '';
        }
    });

    // Filter cards by search text
    document.querySelectorAll('.knowledge-card').forEach(card => {
        const text = card.getAttribute('data-search') || '';
        card.style.display = text.includes(q) ? '' : 'none';
    });
}

/* ── Init ── */

document.addEventListener('DOMContentLoaded', async () => {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', filterAll);
    }

    const categoryFilter = document.getElementById('category-filter');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', filterAll);
    }

    const identifyForm = document.getElementById('identify-form');
    if (identifyForm) {
        identifyForm.addEventListener('submit', handleIdentify);
    }

    const [ancestral, crops, fertilizers, diseases] = await Promise.all([
        fetchJSON(`${API}/api/knowledge/ancestral`),
        fetchJSON(`${API}/api/knowledge/crops`),
        fetchJSON(`${API}/api/knowledge/fertilizers`),
        fetchJSON(`${API}/api/knowledge/diseases`),
    ]);

    renderAncestral(ancestral);
    renderCrops(crops);
    renderFertilizers(fertilizers);
    renderDiseases(diseases);
    updateStats(ancestral, crops, fertilizers, diseases);
});
