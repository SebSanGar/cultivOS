/* ── cultivOS Dashboard — app.js ── */

const API = '/api';

// ── State ──
let farms = [];
let selectedFarmId = null;
let fieldsByFarm = {};       // farmId -> [fields]
let healthByField = {};      // fieldId -> latestHealthScore
let ndviByField = {};        // fieldId -> latestNDVI

// ── DOM refs ──
const farmGrid = document.getElementById('farm-grid');
const fieldPanel = document.getElementById('field-panel');
const fieldPanelTitle = document.getElementById('field-panel-title');
const fieldList = document.getElementById('field-list');
const statFarms = document.getElementById('stat-farms');
const statFields = document.getElementById('stat-fields');
const statAvgHealth = document.getElementById('stat-avg-health');

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

    // Load health and NDVI for each field in parallel
    await Promise.all(fields.map(async (f) => {
        const [healthList, ndviList] = await Promise.all([
            fetchJSON(`/farms/${farmId}/fields/${f.id}/health`),
            fetchJSON(`/farms/${farmId}/fields/${f.id}/ndvi`),
        ]);
        if (healthList && healthList.length > 0) {
            healthByField[f.id] = healthList[healthList.length - 1];
        }
        if (ndviList && ndviList.length > 0) {
            ndviByField[f.id] = ndviList[ndviList.length - 1];
        }
    }));

    return fields;
}

// ── Stats ──
function updateStats() {
    statFarms.textContent = farms.length;
    const totalFields = Object.values(fieldsByFarm).reduce((s, f) => s + f.length, 0);
    statFields.textContent = totalFields;

    const scores = Object.values(healthByField).map(h => h.score);
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

        return `
        <div class="farm-card" onclick="selectFarm(${farm.id})">
            <div class="farm-card-header">
                <div>
                    <div class="farm-name">${esc(farm.name)}</div>
                    <div class="farm-location">${esc(farm.municipality || farm.state)}</div>
                </div>
                <div class="health-badge ${cls}" data-health-score="${avgScore != null ? Math.round(avgScore) : ''}">
                    Salud: ${healthLabel(avgScore)}
                </div>
            </div>
            <div class="farm-meta">
                <div class="farm-meta-item">${farm.total_hectares} ha</div>
                <div class="farm-meta-item">${fields.length} campos</div>
            </div>
        </div>`;
    }).join('');
}

// ── Field panel rendering ──
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
        const score = health ? health.score : null;
        const cls = healthClass(score);
        const ndviVal = ndvi ? ndvi.ndvi_mean.toFixed(2) : '--';

        return `
        <div class="field-card">
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
        </div>`;
    }).join('');
}

// ── Navigation ──
async function selectFarm(farmId) {
    selectedFarmId = farmId;
    fieldPanel.style.display = 'block';
    fieldList.innerHTML = '<div class="loading"><div class="loading-spinner"></div>Cargando campos...</div>';
    await loadFieldsForFarm(farmId);
    renderFields(farmId);
    updateStats();
    // Re-render farm cards to show updated health badges
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
    // Pre-load fields for all farms
    await Promise.all(farms.map(f => loadFieldsForFarm(f.id)));
    updateStats();
    renderFarms();
}

init();
