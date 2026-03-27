/* ── cultivOS Dashboard — app.js ── */

const API = '/api';

// ── State ──
let farms = [];
let selectedFarmId = null;
let fieldsByFarm = {};
let healthByField = {};
let ndviByField = {};
let soilByField = {};
let treatmentsByField = {};
let rotationByField = {};

// ── DOM refs ──
const farmGrid = document.getElementById('farm-grid');
const fieldPanel = document.getElementById('field-panel');
const fieldPanelTitle = document.getElementById('field-panel-title');
const fieldList = document.getElementById('field-list');
const fertPanel = document.getElementById('fert-panel');
const fertList = document.getElementById('fert-list');
const statFarms = document.getElementById('stat-farms');
const statFields = document.getElementById('stat-fields');
const statAvgHealth = document.getElementById('stat-avg-health');
const statHectares = document.getElementById('stat-hectares');

// ── Helpers ──
function healthClass(score) {
    if (score == null) return 'none';
    if (score > 70) return 'good';
    if (score >= 40) return 'warning';
    return 'critical';
}

function healthLabel(score) {
    if (score == null) return '--';
    return Math.round(score);
}

function phClass(ph) {
    if (ph == null) return '';
    if (ph >= 6.0 && ph <= 7.0) return 'good';
    if (ph >= 5.5 && ph <= 7.5) return 'warning';
    return 'critical';
}

async function fetchJSON(path) {
    try {
        const resp = await fetch(API + path);
        if (!resp.ok) return null;
        return await resp.json();
    } catch {
        return null;
    }
}

// ── Data loading ──
async function loadFarms() {
    farmGrid.innerHTML = '<div class="loading"><div class="loading-spinner"></div>Cargando granjas...</div>';
    farms = await fetchJSON('/farms') || [];
    updateStats();
    renderFarms();
}

async function loadFieldsForFarm(farmId) {
    if (fieldsByFarm[farmId]) return fieldsByFarm[farmId];
    const fields = await fetchJSON(`/farms/${farmId}/fields`) || [];
    fieldsByFarm[farmId] = fields;

    // Load all data for each field in parallel
    await Promise.all(fields.map(async (f) => {
        const [healthList, ndviList, soilList, treatmentList, rotation] = await Promise.all([
            fetchJSON(`/farms/${farmId}/fields/${f.id}/health`),
            fetchJSON(`/farms/${farmId}/fields/${f.id}/ndvi`),
            fetchJSON(`/farms/${farmId}/fields/${f.id}/soil`),
            fetchJSON(`/farms/${farmId}/fields/${f.id}/treatments`),
            fetchJSON(`/farms/${farmId}/fields/${f.id}/rotation`),
        ]);
        if (healthList && healthList.length > 0) {
            healthByField[f.id] = healthList[healthList.length - 1];
        }
        if (ndviList && ndviList.length > 0) {
            ndviByField[f.id] = ndviList[ndviList.length - 1];
        }
        if (soilList && soilList.length > 0) {
            soilByField[f.id] = soilList[soilList.length - 1];
        }
        if (treatmentList && treatmentList.length > 0) {
            treatmentsByField[f.id] = treatmentList[treatmentList.length - 1];
        }
        if (rotation) {
            rotationByField[f.id] = rotation;
        }
    }));

    return fields;
}

// ── Stats ──
function updateStats() {
    statFarms.textContent = farms.length;
    const allFields = Object.values(fieldsByFarm).flat();
    statFields.textContent = allFields.length;

    const totalHa = farms.reduce((s, f) => s + (f.total_hectares || 0), 0);
    statHectares.textContent = Math.round(totalHa);

    const scores = Object.values(healthByField).map(h => h.score).filter(s => s != null);
    if (scores.length > 0) {
        const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
        statAvgHealth.textContent = Math.round(avg);
    } else {
        statAvgHealth.textContent = '--';
    }
}

// ── Farm card rendering ──
function renderFarms() {
    if (farms.length === 0) {
        farmGrid.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">&#x1f33e;</div>
                <div class="empty-state-title">Sin granjas registradas</div>
                <div class="empty-state-text">Usa la API para crear tu primera granja: POST /api/farms</div>
            </div>`;
        return;
    }

    farmGrid.innerHTML = farms.map(farm => {
        const fields = fieldsByFarm[farm.id] || [];
        const scores = fields
            .map(f => healthByField[f.id])
            .filter(Boolean)
            .map(h => h.score);
        const avgScore = scores.length > 0
            ? scores.reduce((a, b) => a + b, 0) / scores.length
            : null;
        const cls = healthClass(avgScore);
        const crops = [...new Set(fields.map(f => f.crop_type).filter(Boolean))].join(', ');

        return `
        <div class="farm-card" onclick="selectFarm(${farm.id})">
            <div class="farm-card-header">
                <div>
                    <div class="farm-name">${esc(farm.name)}</div>
                    <div class="farm-location">${esc(farm.municipality || '')}${farm.municipality && farm.state ? ', ' : ''}${esc(farm.state || '')}</div>
                </div>
                <div class="health-badge ${cls}">
                    Salud: ${healthLabel(avgScore)}
                </div>
            </div>
            <div class="farm-meta">
                <div class="farm-meta-item">${farm.total_hectares} ha</div>
                <div class="farm-meta-item">${fields.length} campos</div>
                ${crops ? `<div class="farm-meta-item">${esc(crops)}</div>` : ''}
            </div>
            ${farm.owner_name ? `<div class="farm-owner">${esc(farm.owner_name)}</div>` : ''}
        </div>`;
    }).join('');
}

// ── Field panel rendering — the brain view ──
function renderFields(farmId) {
    const farm = farms.find(f => f.id === farmId);
    const fields = fieldsByFarm[farmId] || [];

    fieldPanelTitle.textContent = `Campos — ${farm ? farm.name : ''}`;

    if (fields.length === 0) {
        fieldList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-title">Sin campos</div>
                <div class="empty-state-text">Agrega campos a esta granja via la API.</div>
            </div>`;
        return;
    }

    fieldList.innerHTML = fields.map(f => {
        const health = healthByField[f.id];
        const ndvi = ndviByField[f.id];
        const soil = soilByField[f.id];
        const treatment = treatmentsByField[f.id];
        const rotation = rotationByField[f.id];
        const score = health ? health.score : null;
        const cls = healthClass(score);
        const ndviVal = ndvi ? ndvi.ndvi_mean.toFixed(2) : '--';

        // Soil section
        let soilHtml = '';
        if (soil) {
            const phCls = phClass(soil.ph);
            soilHtml = `
            <div class="field-section">
                <div class="field-section-title">Analisis de Suelo</div>
                <div class="soil-grid">
                    <div class="soil-item">
                        <span class="soil-label">pH</span>
                        <span class="soil-value health-badge ${phCls}">${soil.ph}</span>
                    </div>
                    <div class="soil-item">
                        <span class="soil-label">Materia Organica</span>
                        <span class="soil-value">${soil.organic_matter_pct}%</span>
                    </div>
                    <div class="soil-item">
                        <span class="soil-label">N</span>
                        <span class="soil-value">${soil.nitrogen_ppm} ppm</span>
                    </div>
                    <div class="soil-item">
                        <span class="soil-label">P</span>
                        <span class="soil-value">${soil.phosphorus_ppm} ppm</span>
                    </div>
                    <div class="soil-item">
                        <span class="soil-label">K</span>
                        <span class="soil-value">${soil.potassium_ppm} ppm</span>
                    </div>
                    <div class="soil-item">
                        <span class="soil-label">Humedad</span>
                        <span class="soil-value">${soil.moisture_pct}%</span>
                    </div>
                    <div class="soil-item">
                        <span class="soil-label">Textura</span>
                        <span class="soil-value">${esc(soil.texture || '--')}</span>
                    </div>
                </div>
            </div>`;
        }

        // Treatment section
        let treatmentHtml = '';
        if (treatment) {
            treatmentHtml = `
            <div class="field-section">
                <div class="field-section-title">Recomendacion de Tratamiento</div>
                <div class="treatment-card">
                    ${treatment.problema ? `<div class="treatment-row"><strong>Problema:</strong> ${esc(treatment.problema)}</div>` : ''}
                    ${treatment.tratamiento ? `<div class="treatment-row"><strong>Tratamiento:</strong> ${esc(treatment.tratamiento)}</div>` : ''}
                    ${treatment.costo_estimado_mxn ? `<div class="treatment-row"><strong>Costo:</strong> $${treatment.costo_estimado_mxn.toLocaleString()} MXN/ha</div>` : ''}
                    ${treatment.urgencia ? `<div class="treatment-row urgency-${treatment.urgencia.toLowerCase()}">${esc(treatment.urgencia)}</div>` : ''}
                    ${treatment.prevencion ? `<div class="treatment-row"><strong>Prevencion:</strong> ${esc(treatment.prevencion)}</div>` : ''}
                </div>
            </div>`;
        }

        // Rotation section
        let rotationHtml = '';
        if (rotation && rotation.seasons) {
            rotationHtml = `
            <div class="field-section">
                <div class="field-section-title">Plan de Rotacion</div>
                <div class="rotation-timeline">
                    ${rotation.seasons.map((s, i) => `
                        <div class="rotation-season">
                            <div class="rotation-num">${i + 1}</div>
                            <div>
                                <div class="rotation-crop">${esc(s.crop || s.cultivo || '')}</div>
                                <div class="rotation-reason">${esc(s.reason || s.razon || '')}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>`;
        }

        return `
        <div class="field-card-expanded">
            <div class="field-card-header">
                <span class="field-name">${esc(f.name)}</span>
                ${f.crop_type ? `<span class="field-crop">${esc(f.crop_type)}</span>` : ''}
            </div>
            <div class="field-stats">
                <div>
                    <div class="field-stat-label">Salud</div>
                    <div class="field-stat-value">
                        <span class="health-badge ${cls}">${healthLabel(score)}</span>
                    </div>
                </div>
                <div>
                    <div class="field-stat-label">NDVI</div>
                    <div class="field-stat-value">${ndviVal}</div>
                </div>
                <div>
                    <div class="field-stat-label">Hectareas</div>
                    <div class="field-stat-value">${f.hectares}</div>
                </div>
            </div>
            ${score != null ? `
            <div class="health-bar">
                <div class="health-bar-fill ${cls}" style="width:${Math.round(score)}%"></div>
            </div>` : ''}
            ${soilHtml}
            ${treatmentHtml}
            ${rotationHtml}
        </div>`;
    }).join('');
}

// ── Fertilizer knowledge base ──
async function showFertilizers() {
    document.getElementById('tab-granjas').classList.remove('active');
    document.getElementById('tab-fertilizantes').classList.add('active');
    farmGrid.style.display = 'none';
    fieldPanel.style.display = 'none';
    fertPanel.style.display = 'block';

    fertList.innerHTML = '<div class="loading"><div class="loading-spinner"></div>Cargando...</div>';
    const ferts = await fetchJSON('/knowledge/fertilizers') || [];

    if (ferts.length === 0) {
        fertList.innerHTML = '<div class="empty-state"><div class="empty-state-title">Sin datos</div></div>';
        return;
    }

    fertList.innerHTML = ferts.map(f => `
        <div class="fert-card">
            <div class="fert-name">${esc(f.name)}</div>
            <div class="fert-desc">${esc(f.description_es || f.description || '')}</div>
            <div class="fert-meta">
                ${f.application_method ? `<div><strong>Aplicacion:</strong> ${esc(f.application_method)}</div>` : ''}
                ${f.cost_per_ha_mxn ? `<div><strong>Costo:</strong> $${f.cost_per_ha_mxn.toLocaleString()} MXN/ha</div>` : ''}
                ${f.suitable_crops ? `<div><strong>Cultivos:</strong> ${esc(Array.isArray(f.suitable_crops) ? f.suitable_crops.join(', ') : f.suitable_crops)}</div>` : ''}
            </div>
        </div>
    `).join('');
}

function closeFertilizers() {
    document.getElementById('tab-fertilizantes').classList.remove('active');
    document.getElementById('tab-granjas').classList.add('active');
    fertPanel.style.display = 'none';
    farmGrid.style.display = '';
}

// ── Navigation ──
async function selectFarm(farmId) {
    selectedFarmId = farmId;
    fieldPanel.style.display = 'block';
    fieldList.innerHTML = '<div class="loading"><div class="loading-spinner"></div>Cargando campos...</div>';
    await loadFieldsForFarm(farmId);
    renderFields(farmId);
    updateStats();
    renderFarms();
    fieldPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function closeFarmDetail() {
    selectedFarmId = null;
    fieldPanel.style.display = 'none';
}

// ── Escape HTML ──
function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

// ── Init ──
async function init() {
    await loadFarms();
    await Promise.all(farms.map(f => loadFieldsForFarm(f.id)));
    updateStats();
    renderFarms();
}

init();
