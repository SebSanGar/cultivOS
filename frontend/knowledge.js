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

/* ── Search / Filter ── */

function filterCards(query) {
    const q = query.toLowerCase().trim();
    document.querySelectorAll('.knowledge-card').forEach(card => {
        const text = card.getAttribute('data-search') || '';
        card.style.display = text.includes(q) ? '' : 'none';
    });
}

/* ── Init ── */

document.addEventListener('DOMContentLoaded', async () => {
    const searchInput = document.getElementById('knowledge-search');
    if (searchInput) {
        searchInput.addEventListener('input', e => filterCards(e.target.value));
    }

    const [ancestral, crops, fertilizers] = await Promise.all([
        fetchJSON(`${API}/api/knowledge/ancestral`),
        fetchJSON(`${API}/api/knowledge/crops`),
        fetchJSON(`${API}/api/knowledge/fertilizers`),
    ]);

    renderAncestral(ancestral);
    renderCrops(crops);
    renderFertilizers(fertilizers);
});
