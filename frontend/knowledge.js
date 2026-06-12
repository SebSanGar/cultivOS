/* cultivOS — Knowledge Base Page */

const API = '';  // same-origin; was hardcoded to :8000 which broke on any other host/port (incl prod)

/* i18n helper — resolves a key to the current-language string, falling back
   to the provided default if the i18n module hasn't loaded yet. */
function t(key, fallback) {
    if (window.cultivOS_i18n && typeof window.cultivOS_i18n.t === 'function') {
        return window.cultivOS_i18n.t(key);
    }
    return fallback;
}

/* Pick the current-language variant of a backend DATA field (base_en / base_es / base). */
function loc(obj, base) {
    return (window.cultivOS_i18n && typeof window.cultivOS_i18n.localized === 'function')
        ? window.cultivOS_i18n.localized(obj, base)
        : (obj[base + '_es'] || obj[base] || '');
}

/* Display label for a crop DATA value ('maiz' -> 'Corn' in EN). */
function cropLabel(value) {
    return (window.cultivOS_i18n && typeof window.cultivOS_i18n.cropName === 'function')
        ? window.cultivOS_i18n.cropName(value)
        : (value || '');
}

/* Localize a list of crop DATA values for display. */
function cropList(values) {
    return (values || []).map(cropLabel).join(', ');
}

/* Display label for a practice_type slug ('water_management' -> 'Water management' in EN). */
const _PRACTICE_KEY = {
    water_management: 'know.practiceWaterMgmt',
    soil_management:  'know.practiceSoilMgmt',
    biological_control: 'know.practiceBioControl',
    knowledge_system: 'know.practiceKnowledgeSys',
    intercropping:    'know.practiceIntercropping',
};
function practiceTypeLabel(slug) {
    const key = _PRACTICE_KEY[slug];
    if (key) return t(key, slug);
    // Fallback: humanize unknown slugs (replace _ with space, title-case first word)
    return (slug || '').replace(/_/g, ' ').replace(/^\w/, c => c.toUpperCase());
}

/* Re-localize any data-i18n nodes injected after the i18n module's initial pass. */
function relocalize() {
    if (window.cultivOS_i18n && typeof window.cultivOS_i18n.applyAll === 'function') {
        window.cultivOS_i18n.applyAll();
    }
}

async function fetchJSON(url) {
    const resp = await fetch(url);
    if (!resp.ok) return [];
    return resp.json();
}

/* ── Render functions ── */

function renderAncestral(methods) {
    const container = document.getElementById('ancestral-cards');
    if (!methods || methods.length === 0) {
        container.innerHTML = `<p class="knowledge-empty">${t('know.emptyAncestral', 'No ancestral methods found.')}</p>`;
        return;
    }
    const lblRegion = t('know.lblRegion', 'Region:');
    const lblCrops = t('know.lblCrops', 'Crops:');
    const lblBenefits = t('know.lblBenefits', 'Benefits:');
    const lblScience = t('know.lblScience', 'Scientific basis:');
    container.innerHTML = methods.map(m => `
        <div class="knowledge-card" data-search="${(m.name + ' ' + m.description_es + ' ' + m.region + ' ' + m.practice_type + ' ' + (m.crops || []).join(' ')).toLowerCase()}">
            <div class="knowledge-card-header">
                <h3 class="knowledge-card-title">${loc(m, 'name')}</h3>
                <span class="knowledge-badge knowledge-badge-type">${practiceTypeLabel(m.practice_type)}</span>
            </div>
            <p class="knowledge-card-desc">${loc(m, 'description')}</p>
            <div class="knowledge-card-meta">
                <span class="knowledge-meta-item"><strong>${lblRegion}</strong> ${m.region}</span>
                <span class="knowledge-meta-item"><strong>${lblCrops}</strong> ${cropList(m.crops)}</span>
            </div>
            <p class="knowledge-card-benefits"><strong>${lblBenefits}</strong> ${loc(m, 'benefits')}</p>
            ${m.scientific_basis ? `<p class="knowledge-card-science"><strong>${lblScience}</strong> ${loc(m, 'scientific_basis')}</p>` : ''}
        </div>
    `).join('');
}

function renderCrops(crops) {
    const container = document.getElementById('crop-cards');
    if (!crops || crops.length === 0) {
        container.innerHTML = `<p class="knowledge-empty">${t('know.emptyCrops', 'No crops found.')}</p>`;
        return;
    }
    const lblSeason = t('know.lblSeason', 'Season:');
    const lblWater = t('know.lblWater', 'Water:');
    const lblHarvest = t('know.lblHarvest', 'Harvest:');
    const lblDays = t('know.unitDays', 'days');
    const lblRegions = t('know.lblRegions', 'Regions:');
    const lblCompanions = t('know.lblCompanions', 'Companions:');
    const lblOptimalTemp = t('know.lblOptimalTemp', 'Optimal temp:');
    container.innerHTML = crops.map(c => `
        <div class="knowledge-card" data-search="${(c.name + ' ' + c.family + ' ' + c.description_es + ' ' + (c.regions || []).join(' ') + ' ' + (c.companions || []).join(' ')).toLowerCase()}">
            <div class="knowledge-card-header">
                <h3 class="knowledge-card-title">${cropLabel(c.name)}</h3>
                <span class="knowledge-badge knowledge-badge-family">${c.family}</span>
            </div>
            <p class="knowledge-card-desc">${loc(c, 'description')}</p>
            <div class="knowledge-card-meta">
                <span class="knowledge-meta-item"><strong>${lblSeason}</strong> ${loc(c, 'growing_season')}</span>
                <span class="knowledge-meta-item"><strong>${lblWater}</strong> ${c.water_needs}</span>
                ${c.days_to_harvest ? `<span class="knowledge-meta-item"><strong>${lblHarvest}</strong> ${c.days_to_harvest} ${lblDays}</span>` : ''}
            </div>
            <div class="knowledge-card-meta">
                <span class="knowledge-meta-item"><strong>${lblRegions}</strong> ${(c.regions || []).join(', ')}</span>
                <span class="knowledge-meta-item"><strong>${lblCompanions}</strong> ${cropList(c.companions)}</span>
            </div>
            ${c.optimal_temp_min != null ? `<p class="knowledge-card-temp"><strong>${lblOptimalTemp}</strong> ${c.optimal_temp_min} - ${c.optimal_temp_max} C</p>` : ''}
        </div>
    `).join('');
}

function renderFertilizers(fertilizers) {
    const container = document.getElementById('fertilizer-cards');
    if (!fertilizers || fertilizers.length === 0) {
        container.innerHTML = `<p class="knowledge-empty">${t('know.emptyFertilizers', 'No fertilizers found.')}</p>`;
        return;
    }
    const lblApplication = t('know.lblApplication', 'Application:');
    const lblNutrients = t('know.lblNutrients', 'Nutrients:');
    const lblCrops = t('know.lblCrops', 'Crops:');
    container.innerHTML = fertilizers.map(f => `
        <div class="knowledge-card" data-search="${(f.name + ' ' + f.description_es + ' ' + f.nutrient_profile + ' ' + (f.suitable_crops || []).join(' ')).toLowerCase()}">
            <div class="knowledge-card-header">
                <h3 class="knowledge-card-title">${loc(f, 'name')}</h3>
                <span class="knowledge-badge knowledge-badge-cost">$${f.cost_per_ha_mxn.toLocaleString()} MXN/ha</span>
            </div>
            <p class="knowledge-card-desc">${loc(f, 'description')}</p>
            <div class="knowledge-card-meta">
                <span class="knowledge-meta-item"><strong>${lblApplication}</strong> ${loc(f, 'application_method')}</span>
                <span class="knowledge-meta-item"><strong>${lblNutrients}</strong> ${loc(f, 'nutrient_profile')}</span>
            </div>
            <p class="knowledge-card-crops"><strong>${lblCrops}</strong> ${cropList(f.suitable_crops)}</p>
        </div>
    `).join('');
}

function severityLabel(severity) {
    if (severity === 'alta') return t('know.severityHigh', 'High');
    if (severity === 'media') return t('know.severityMed', 'Medium');
    if (severity === 'baja') return t('know.severityLow', 'Low');
    return severity;
}

function renderDiseases(diseases) {
    const container = document.getElementById('disease-cards');
    if (!container) return;
    if (!diseases || diseases.length === 0) {
        container.innerHTML = `<p class="knowledge-empty">${t('know.emptyDiseases', 'No diseases found.')}</p>`;
        return;
    }
    const lblCrops = t('know.lblCrops', 'Crops:');
    const lblRegion = t('know.lblRegion', 'Region:');
    const lblSymptoms = t('know.lblSymptoms', 'Symptoms:');
    const lblTreatments = t('know.lblTreatments', 'Treatments:');
    container.innerHTML = diseases.map(d => {
        const severityClass = d.severity === 'alta' ? 'severity-high' : d.severity === 'media' ? 'severity-med' : 'severity-low';
        return `
        <div class="knowledge-card" data-search="${(d.name + ' ' + d.description_es + ' ' + (d.affected_crops || []).join(' ') + ' ' + (d.symptoms || []).join(' ')).toLowerCase()}">
            <div class="knowledge-card-header">
                <h3 class="knowledge-card-title">${loc(d, 'name')}</h3>
                <span class="knowledge-badge ${severityClass}">${severityLabel(d.severity)}</span>
            </div>
            <p class="knowledge-card-desc">${loc(d, 'description')}</p>
            <div class="knowledge-card-meta">
                <span class="knowledge-meta-item"><strong>${lblCrops}</strong> ${cropList(d.affected_crops)}</span>
                <span class="knowledge-meta-item"><strong>${lblRegion}</strong> ${d.region}</span>
            </div>
            <p class="knowledge-card-symptoms"><strong>${lblSymptoms}</strong> ${(d.symptoms || []).join(', ')}</p>
            <div class="knowledge-card-treatments">
                <strong>${lblTreatments}</strong>
                ${(d.treatments || []).map(tr =>
                    `<span class="treatment-tag${tr.organic ? ' organic' : ''}">${loc(tr, 'name')}</span>`
                ).join(' ')}
            </div>
        </div>`;
    }).join('');
}

function renderIdentifyResults(matches) {
    const container = document.getElementById('identify-results');
    if (!container) return;
    if (!matches || matches.length === 0) {
        container.innerHTML = `<p class="knowledge-empty">${t('know.emptyMatches', 'No matches found.')}</p>`;
        return;
    }
    const resultsTitle = t('know.resultsTitle', 'Results');
    const lblMatchedSymptoms = t('know.lblMatchedSymptoms', 'Matched symptoms:');
    container.innerHTML = `<h3 class="identify-results-title">${resultsTitle}</h3>` +
        matches.filter(m => m.confidence > 0).map(m => `
        <div class="identify-match">
            <div class="identify-match-header">
                <strong>${m.name}</strong>
                <span class="confidence-bar" style="width:${Math.round(m.confidence * 100)}%">${Math.round(m.confidence * 100)}%</span>
            </div>
            <p>${loc(m, 'description')}</p>
            <p><strong>${lblMatchedSymptoms}</strong> ${(m.symptoms_matched || []).join(', ')}</p>
            <div class="knowledge-card-treatments">
                ${(m.treatments || []).map(tr =>
                    `<span class="treatment-tag${tr.organic ? ' organic' : ''}">${loc(tr, 'name')}</span>`
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
        document.getElementById('identify-results').innerHTML = `<p class="knowledge-empty">${t('know.identifyError', 'Error identifying.')}</p>`;
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

/* Cached datasets so injected cards can be re-rendered on language toggle. */
let knowledgeData = { ancestral: [], crops: [], fertilizers: [], diseases: [] };

function renderAll() {
    renderAncestral(knowledgeData.ancestral);
    renderCrops(knowledgeData.crops);
    renderFertilizers(knowledgeData.fertilizers);
    renderDiseases(knowledgeData.diseases);
    updateStats(
        knowledgeData.ancestral,
        knowledgeData.crops,
        knowledgeData.fertilizers,
        knowledgeData.diseases
    );
    // Re-apply filters and localize any static data-i18n nodes added by render.
    filterAll();
    relocalize();
}

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

    // Re-render injected cards (whose labels are resolved at render time via t())
    // whenever the user toggles language. The i18n module switches language on
    // click, so we re-render right after to pick up the new strings.
    document.querySelectorAll('.nav-lang-toggle').forEach(toggle => {
        toggle.addEventListener('click', () => {
            // Defer so i18n's own click handler runs (and sets the new lang) first.
            setTimeout(renderAll, 0);
        });
    });

    const [ancestral, crops, fertilizers, diseases] = await Promise.all([
        fetchJSON(`${API}/api/knowledge/ancestral`),
        fetchJSON(`${API}/api/knowledge/crops`),
        fetchJSON(`${API}/api/knowledge/fertilizers`),
        fetchJSON(`${API}/api/knowledge/diseases`),
    ]);

    knowledgeData = { ancestral, crops, fertilizers, diseases };
    renderAll();
});
