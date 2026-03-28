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
let healthHistoryByField = {};
let trendByField = {};

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
    const farmsResp = await fetchJSON('/farms');
    farms = (farmsResp && farmsResp.data) ? farmsResp.data : (farmsResp || []);
    updateStats();
    renderFarms();
}

async function loadFieldsForFarm(farmId) {
    if (fieldsByFarm[farmId]) return fieldsByFarm[farmId];
    const fields = await fetchJSON(`/farms/${farmId}/fields`) || [];
    fieldsByFarm[farmId] = fields;

    // Load all data for each field in parallel
    await Promise.all(fields.map(async (f) => {
        const [healthList, ndviList, soilList, treatmentList, rotation, history, trend] = await Promise.all([
            fetchJSON(`/farms/${farmId}/fields/${f.id}/health`),
            fetchJSON(`/farms/${farmId}/fields/${f.id}/ndvi`),
            fetchJSON(`/farms/${farmId}/fields/${f.id}/soil`),
            fetchJSON(`/farms/${farmId}/fields/${f.id}/treatments`),
            fetchJSON(`/farms/${farmId}/fields/${f.id}/rotation`),
            fetchJSON(`/farms/${farmId}/fields/${f.id}/health/history`),
            fetchJSON(`/farms/${farmId}/fields/${f.id}/health/trend`),
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
        if (history && history.scores) {
            healthHistoryByField[f.id] = history.scores.map(s => s.score);
        }
        if (trend) {
            trendByField[f.id] = trend.trend;
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

// ── Sparkline builder ──
function buildSparkline(scores, trend) {
    if (!scores || scores.length < 2) return '';
    const recent = scores.slice(-5);
    const w = 60, h = 20, pad = 2;
    const min = Math.min(...recent);
    const max = Math.max(...recent);
    const range = max - min || 1;

    const points = recent.map((v, i) => {
        const x = pad + (i / (recent.length - 1)) * (w - 2 * pad);
        const y = pad + (1 - (v - min) / range) * (h - 2 * pad);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
    });

    let colorClass = 'sparkline-stable';
    if (trend === 'improving') colorClass = 'sparkline-improving';
    else if (trend === 'declining') colorClass = 'sparkline-declining';

    return `<svg class="sparkline ${colorClass}" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
        <polyline points="${points.join(' ')}" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>`;
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
        const sparkHtml = buildSparkline(healthHistoryByField[f.id], trendByField[f.id]);

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
        <div class="field-card-expanded" onclick="window.location.href='/campo?farm=${farmId}&field=${f.id}'" style="cursor:pointer" title="Ver detalle completo">
            <div class="field-card-header">
                <span class="field-name">${esc(f.name)}</span>
                ${f.crop_type ? `<span class="field-crop">${esc(f.crop_type)}</span>` : ''}
            </div>
            <div class="field-stats">
                <div>
                    <div class="field-stat-label">Salud</div>
                    <div class="field-stat-value">
                        <span class="health-badge ${cls}">${healthLabel(score)}</span>
                        ${sparkHtml}
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

// ── Heatmap rendering ──
async function loadHeatmap(farmId) {
    const data = await fetchJSON(`/farms/${farmId}/heatmap`);
    if (!data || !data.fields || data.fields.length === 0) {
        document.getElementById('heatmap-container').style.display = 'none';
        return;
    }
    renderHeatmap(data.fields, farmId);
}

function renderHeatmap(fields, farmId) {
    const container = document.getElementById('heatmap-container');
    const canvas = document.getElementById('heatmap-canvas');
    container.style.display = '';

    // Filter fields with valid centroids
    const mapped = fields.filter(f => f.centroid_lat != null && f.centroid_lon != null);
    if (mapped.length === 0) {
        canvas.innerHTML = '<div class="heatmap-empty">Sin coordenadas de campo disponibles</div>';
        return;
    }

    // Compute bounds
    const lats = mapped.map(f => f.centroid_lat);
    const lons = mapped.map(f => f.centroid_lon);
    const minLat = Math.min(...lats), maxLat = Math.max(...lats);
    const minLon = Math.min(...lons), maxLon = Math.max(...lons);

    const w = 400, h = 280, pad = 40;
    const latRange = maxLat - minLat || 0.01;
    const lonRange = maxLon - minLon || 0.01;

    const dots = mapped.map(f => {
        const x = pad + ((f.centroid_lon - minLon) / lonRange) * (w - 2 * pad);
        const y = pad + ((maxLat - f.centroid_lat) / latRange) * (h - 2 * pad);
        const cls = heatmapColorClass(f.health_score);
        const label = f.health_score != null ? Math.round(f.health_score) : '--';
        return `<g class="heatmap-field" onclick="window.location.href='/campo?farm=${farmId}&field=${f.field_id}'" style="cursor:pointer">
            <circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="18" class="heatmap-circle ${cls}"/>
            <text x="${x.toFixed(1)}" y="${(y + 1).toFixed(1)}" class="heatmap-label">${label}</text>
            <text x="${x.toFixed(1)}" y="${(y + 14).toFixed(1)}" class="heatmap-name">${esc(f.field_name)}</text>
        </g>`;
    });

    canvas.innerHTML = `<svg class="heatmap-svg" viewBox="0 0 ${w} ${h}" width="100%" preserveAspectRatio="xMidYMid meet">
        ${dots.join('')}
    </svg>`;
}

function heatmapColorClass(score) {
    if (score == null) return 'heatmap-none';
    if (score > 75) return 'heatmap-good';
    if (score >= 50) return 'heatmap-warning';
    return 'heatmap-critical';
}

// ── Fertilizer knowledge base ──
async function showFertilizers() {
    document.getElementById('tab-granjas').classList.remove('active');
    document.getElementById('tab-fertilizantes').classList.add('active');
    farmGrid.style.display = 'none';
    fieldPanel.style.display = 'none';
    document.getElementById('notification-panel').style.display = 'none';
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

// ── Weather widget ──
async function loadWeather(farmId) {
    const records = await fetchJSON(`/farms/${farmId}/weather`) || [];
    if (records.length === 0) {
        document.getElementById('weather-widget').style.display = 'none';
        return;
    }
    const w = records[0]; // latest record (sorted desc by recorded_at)
    const farm = farms.find(f => f.id === farmId);

    document.getElementById('weather-widget').style.display = '';
    document.getElementById('weather-farm-name').textContent = farm ? farm.name : '';
    document.getElementById('weather-temp').textContent = Math.round(w.temp_c) + '\u00B0C';
    document.getElementById('weather-desc').textContent = esc(w.description);
    document.getElementById('weather-humidity').textContent = Math.round(w.humidity_pct) + '%';
    document.getElementById('weather-wind').textContent = w.wind_kmh.toFixed(1) + ' km/h';

    const forecastEl = document.getElementById('weather-forecast');
    if (w.forecast_3day && w.forecast_3day.length > 0) {
        const dayLabels = ['Manana', 'Pasado', 'En 3 dias'];
        forecastEl.innerHTML = w.forecast_3day.map((day, i) => `
            <div class="forecast-day">
                <div class="forecast-day-label">${dayLabels[i] || 'Dia ' + (i + 1)}</div>
                <div class="forecast-day-temp">${Math.round(day.temp_c)}\u00B0C</div>
                <div class="forecast-day-desc">${esc(day.description)}</div>
                <div class="forecast-day-details">${Math.round(day.humidity_pct)}% hum &middot; ${day.wind_kmh.toFixed(0)} km/h</div>
            </div>
        `).join('');
    } else {
        forecastEl.innerHTML = '';
    }
}

// ── Notification panel ──
async function loadNotifications(farmId) {
    const panel = document.getElementById('notification-panel');
    const list = document.getElementById('notification-list');
    const items = await fetchJSON(`/farms/${farmId}/notifications`) || [];
    if (items.length === 0) {
        panel.style.display = 'none';
        return;
    }
    panel.style.display = '';
    renderNotifications(items, farmId);
}

function renderNotifications(items, farmId) {
    const list = document.getElementById('notification-list');
    list.innerHTML = items.map(n => {
        const date = new Date(n.created_at);
        const dateStr = date.toLocaleDateString('es-MX', { day: 'numeric', month: 'short' });
        const acked = n.acknowledged ? ' acknowledged' : '';
        return `
        <div class="notification-item${acked}" data-id="${n.id}">
            <div class="notification-severity severity-${n.severity}"></div>
            <div class="notification-body">
                <div class="notification-message">${esc(n.message)}</div>
                <div class="notification-meta">${esc(n.alert_type)} &middot; ${dateStr}</div>
            </div>
            ${!n.acknowledged ? `<button class="notification-ack-btn" onclick="acknowledgeNotification(${farmId}, ${n.id}, event)">Confirmar</button>` : ''}
        </div>`;
    }).join('');
}

async function acknowledgeNotification(farmId, notifId, event) {
    event.stopPropagation();
    const resp = await fetch(API + `/farms/${farmId}/notifications/${notifId}/acknowledge`, {
        method: 'POST'
    });
    if (resp.ok) {
        await loadNotifications(farmId);
    }
}

// ── Alert config form ──
async function loadAlertConfig(farmId) {
    const cfg = await fetchJSON(`/farms/${farmId}/alert-config`);
    if (cfg) {
        document.getElementById('cfg-health-floor').value = cfg.health_score_floor;
        document.getElementById('cfg-ndvi-min').value = cfg.ndvi_minimum;
        document.getElementById('cfg-temp-max').value = cfg.temp_max_c;
    }
}

function toggleAlertConfig() {
    const form = document.getElementById('alert-config-form');
    form.style.display = form.style.display === 'none' ? '' : 'none';
}

async function saveAlertConfig() {
    if (!selectedFarmId) return;
    const btn = document.getElementById('alert-config-save');
    btn.disabled = true;
    btn.textContent = 'Guardando...';
    const body = {
        health_score_floor: parseFloat(document.getElementById('cfg-health-floor').value),
        ndvi_minimum: parseFloat(document.getElementById('cfg-ndvi-min').value),
        temp_max_c: parseFloat(document.getElementById('cfg-temp-max').value),
    };
    await fetch(API + `/farms/${selectedFarmId}/alert-config`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body),
    });
    btn.disabled = false;
    btn.textContent = 'Guardar';
    document.getElementById('alert-config-form').style.display = 'none';
}

// ── Seasonal TEK calendar ──
const ALERT_TYPE_LABELS = {
    preparacion: 'Preparacion',
    siembra: 'Siembra',
    cosecha: 'Cosecha',
    mantenimiento: 'Mantenimiento',
};

async function loadSeasonalCalendar(farmId) {
    const container = document.getElementById('seasonal-calendar');
    const groups = document.getElementById('seasonal-groups');
    const badge = document.getElementById('seasonal-season-badge');

    const data = await fetchJSON(`/farms/${farmId}/seasonal-alerts`);
    if (!data || !data.alerts || data.alerts.length === 0) {
        groups.innerHTML = '<div class="seasonal-empty">Sin alertas estacionales activas para este periodo.</div>';
        badge.textContent = '';
        badge.className = 'seasonal-season-badge';
        container.style.display = '';
        return;
    }

    // Season badge
    badge.textContent = data.season === 'temporal' ? 'Temporal (lluvias)' : 'Secas';
    badge.className = 'seasonal-season-badge ' + data.season;

    // Group alerts by type
    const grouped = {};
    for (const alert of data.alerts) {
        if (!grouped[alert.alert_type]) grouped[alert.alert_type] = [];
        grouped[alert.alert_type].push(alert);
    }

    // Render order: preparacion, siembra, cosecha, mantenimiento
    const order = ['preparacion', 'siembra', 'cosecha', 'mantenimiento'];
    let html = '';
    for (const type of order) {
        const items = grouped[type];
        if (!items || items.length === 0) continue;
        html += `<div class="seasonal-group">
            <div class="seasonal-group-label">${esc(ALERT_TYPE_LABELS[type] || type)}</div>`;
        for (const a of items) {
            html += `<div class="seasonal-card">
                <div class="seasonal-type-dot ${a.alert_type}"></div>
                <div class="seasonal-card-body">
                    <div class="seasonal-card-header">
                        <span class="seasonal-crop-name">${esc(a.crop)}</span>
                        <span class="seasonal-month-range">${esc(a.month_range)}</span>
                    </div>
                    <div class="seasonal-message">${esc(a.message)}</div>
                </div>
            </div>`;
        }
        html += '</div>';
    }

    // Legend
    html += `<div class="seasonal-legend">
        <span class="seasonal-legend-item"><span class="seasonal-type-dot preparacion"></span> Preparacion</span>
        <span class="seasonal-legend-item"><span class="seasonal-type-dot siembra"></span> Siembra</span>
        <span class="seasonal-legend-item"><span class="seasonal-type-dot cosecha"></span> Cosecha</span>
        <span class="seasonal-legend-item"><span class="seasonal-type-dot mantenimiento"></span> Mantenimiento</span>
    </div>`;

    groups.innerHTML = html;
    container.style.display = '';
}

// ── Navigation ──
async function selectFarm(farmId) {
    selectedFarmId = farmId;
    fieldPanel.style.display = 'block';
    fieldList.innerHTML = '<div class="loading"><div class="loading-spinner"></div>Cargando campos...</div>';
    await Promise.all([loadFieldsForFarm(farmId), loadWeather(farmId), loadHeatmap(farmId), loadNotifications(farmId), loadAlertConfig(farmId), loadSeasonalCalendar(farmId)]);
    renderFields(farmId);
    updateStats();
    renderFarms();
    fieldPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function closeFarmDetail() {
    selectedFarmId = null;
    fieldPanel.style.display = 'none';
    document.getElementById('weather-widget').style.display = 'none';
    document.getElementById('heatmap-container').style.display = 'none';
    document.getElementById('notification-panel').style.display = 'none';
    document.getElementById('seasonal-calendar').style.display = 'none';
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
