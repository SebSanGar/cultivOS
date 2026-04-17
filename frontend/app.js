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
let soilTrajectoryByField = {};

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
        const [healthList, ndviList, soilList, treatmentList, rotation, history, trend, soilTraj] = await Promise.all([
            fetchJSON(`/farms/${farmId}/fields/${f.id}/health`),
            fetchJSON(`/farms/${farmId}/fields/${f.id}/ndvi`),
            fetchJSON(`/farms/${farmId}/fields/${f.id}/soil`),
            fetchJSON(`/farms/${farmId}/fields/${f.id}/treatments`),
            fetchJSON(`/farms/${farmId}/fields/${f.id}/rotation`),
            fetchJSON(`/farms/${farmId}/fields/${f.id}/health/history`),
            fetchJSON(`/farms/${farmId}/fields/${f.id}/health/trend`),
            fetchJSON(`/farms/${farmId}/fields/${f.id}/soil-trajectory`),
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
        if (soilTraj && soilTraj.months) {
            soilTrajectoryByField[f.id] = soilTraj;
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
                <div class="empty-state-title">Bienvenido a cultivOS</div>
                <div class="empty-state-text">Toca <strong>Cargar datos de ejemplo</strong> para ver cultivOS en accion con una granja de Jalisco. O usa el <a href="/recorrido">asistente guiado</a> para crear la tuya en 3 pasos.</div>
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

// ── Soil sparkline (OM / pH monthly trajectory) ──
function buildSoilSparkline(series, trend) {
    const values = (series || []).filter(v => v != null);
    if (values.length < 2) return '';
    const w = 60, h = 18, pad = 2;
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;
    const points = values.map((v, i) => {
        const x = pad + (i / (values.length - 1)) * (w - 2 * pad);
        const y = pad + (1 - (v - min) / range) * (h - 2 * pad);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
    });
    let colorClass = 'sparkline-stable';
    if (trend === 'improving') colorClass = 'sparkline-improving';
    else if (trend === 'declining') colorClass = 'sparkline-declining';
    return `<svg class="soil-sparkline ${colorClass}" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
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
            const traj = soilTrajectoryByField[f.id];
            const phSeries = traj ? traj.months.map(m => m.avg_ph) : [];
            const omSeries = traj ? traj.months.map(m => m.avg_organic_matter_pct) : [];
            const phSpark = buildSoilSparkline(phSeries, traj && traj.ph_trend);
            const omSpark = buildSoilSparkline(omSeries, traj && traj.organic_matter_trend);
            soilHtml = `
            <div class="field-section">
                <div class="field-section-title">Analisis de Suelo</div>
                <div class="soil-grid">
                    <div class="soil-item">
                        <span class="soil-label">pH</span>
                        <span class="soil-value health-badge ${phCls}">${soil.ph} ${phSpark}</span>
                    </div>
                    <div class="soil-item">
                        <span class="soil-label">Materia Organica</span>
                        <span class="soil-value">${soil.organic_matter_pct}% ${omSpark}</span>
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

// ── Alert history timeline ──
const ALERT_TYPE_MAP = {
    low_health: { label: 'Salud Baja', cls: 'alert-type-health' },
    irrigation: { label: 'Riego', cls: 'alert-type-irrigation' },
    anomaly_health_drop: { label: 'Anomalia Salud', cls: 'alert-type-anomaly' },
    anomaly_ndvi_drop: { label: 'Anomalia NDVI', cls: 'alert-type-anomaly' },
};

async function loadAlertHistory(farmId) {
    const panel = document.getElementById('alert-history');
    const list = document.getElementById('alert-history-list');
    const countEl = document.getElementById('alert-history-count');
    const alerts = await fetchJSON(`/farms/${farmId}/alerts`) || [];
    if (alerts.length === 0) {
        panel.style.display = '';
        countEl.textContent = '';
        list.innerHTML = '<div class="alert-history-empty">Sin alertas registradas</div>';
        return;
    }
    panel.style.display = '';
    countEl.textContent = alerts.length;
    list.innerHTML = alerts.map(a => {
        const dt = new Date(a.sent_at);
        const dateStr = dt.toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' });
        const timeStr = dt.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
        const typeInfo = ALERT_TYPE_MAP[a.alert_type] || { label: a.alert_type, cls: 'alert-type-default' };
        const statusCls = a.status === 'sent' ? 'alert-status-sent' : 'alert-status-pending';
        const statusLabel = a.status === 'sent' ? 'Enviado' : 'Pendiente';
        return `
        <div class="alert-history-item">
            <div class="alert-history-dot ${typeInfo.cls}"></div>
            <div class="alert-history-content">
                <div class="alert-history-top">
                    <span class="alert-history-type-badge ${typeInfo.cls}">${esc(typeInfo.label)}</span>
                    <span class="alert-history-status ${statusCls}">${statusLabel}</span>
                </div>
                <div class="alert-history-message">${esc(a.message)}</div>
                <div class="alert-history-date">${dateStr} &middot; ${timeStr}</div>
            </div>
        </div>`;
    }).join('');
}

// ── Alert check trigger ──
const ALERT_CHECK_TYPES = {
    health: { label: 'Salud', icon: '\u2764', endpoint: 'check' },
    irrigation: { label: 'Riego', icon: '\u{1F4A7}', endpoint: 'check-irrigation' },
    anomalies: { label: 'Anomalias', icon: '\u26A0', endpoint: 'check-anomalies' },
};

async function checkAlerts() {
    if (!selectedFarmId) return;
    const btn = document.getElementById('btn-check-alerts');
    const results = document.getElementById('alert-check-results');
    btn.disabled = true;
    btn.textContent = 'Verificando...';
    results.innerHTML = '<div class="loading"><div class="loading-spinner"></div>Ejecutando verificaciones...</div>';

    const responses = await Promise.all(
        Object.entries(ALERT_CHECK_TYPES).map(async ([key, cfg]) => {
            try {
                const resp = await fetch(`${API}/farms/${selectedFarmId}/alerts/${cfg.endpoint}`, { method: 'POST' });
                if (!resp.ok) return { key, cfg, data: null, error: resp.status };
                return { key, cfg, data: await resp.json(), error: null };
            } catch {
                return { key, cfg, data: null, error: 'network' };
            }
        })
    );

    let totalAlerts = 0;
    let totalFields = 0;
    const cards = responses.map(({ key, cfg, data, error }) => {
        if (error) {
            return `<div class="alert-check-card info">
                <div class="alert-check-icon">${cfg.icon}</div>
                <div class="alert-check-body">
                    <div class="alert-check-card-title">${esc(cfg.label)}</div>
                    <div class="alert-check-card-msg">No se pudo verificar</div>
                </div>
            </div>`;
        }
        const alerts = data.alerts_created || [];
        totalAlerts += alerts.length;
        totalFields = Math.max(totalFields, data.fields_checked || 0);

        if (alerts.length === 0) {
            return `<div class="alert-check-card ok">
                <div class="alert-check-icon">${cfg.icon}</div>
                <div class="alert-check-body">
                    <div class="alert-check-card-title">${esc(cfg.label)} — Sin problemas</div>
                    <div class="alert-check-card-msg">${data.fields_checked} campo(s) revisado(s), todo en orden</div>
                </div>
            </div>`;
        }

        const severity = alerts.length >= 3 ? 'critical' : alerts.length >= 1 ? 'warning' : 'ok';
        const msgs = alerts.map(a => esc(a.message)).join('<br>');
        return `<div class="alert-check-card ${severity}">
            <div class="alert-check-icon">${cfg.icon}</div>
            <div class="alert-check-body">
                <div class="alert-check-card-title">${esc(cfg.label)} — ${alerts.length} alerta(s)</div>
                <div class="alert-check-card-msg">${msgs}</div>
            </div>
        </div>`;
    });

    const summaryText = totalAlerts === 0
        ? `${totalFields} campo(s) verificado(s) — sin alertas activas`
        : `${totalAlerts} alerta(s) encontrada(s) en ${totalFields} campo(s)`;

    results.innerHTML = cards.join('') +
        `<div class="alert-check-summary">${summaryText}</div>`;

    btn.disabled = false;
    btn.textContent = 'Verificar Alertas';

    // Refresh alert history to show newly created alerts
    loadAlertHistory(selectedFarmId);
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
// ── Economic Impact card ──
function formatMXN(n) {
    if (n == null) return '$0';
    return '$' + Number(n).toLocaleString('es-MX');
}

async function loadEconomicImpact(farmId) {
    const container = document.getElementById('economic-impact-panel');
    const data = await fetchJSON(`/farms/${farmId}/economic-impact`);
    if (!data) {
        container.style.display = 'none';
        return;
    }

    container.style.display = '';
    document.getElementById('econ-farm-name').textContent = '';
    document.getElementById('econ-water').textContent = formatMXN(data.water_savings_mxn);
    document.getElementById('econ-fertilizer').textContent = formatMXN(data.fertilizer_savings_mxn);
    document.getElementById('econ-yield').textContent = formatMXN(data.yield_improvement_mxn);
    document.getElementById('econ-total').textContent = formatMXN(data.total_savings_mxn) + ' MXN';
    document.getElementById('econ-nota').textContent = data.nota || '';
}

// ── Carbon sequestration summary ──
async function loadCarbonSummary(farmId) {
    const container = document.getElementById('carbon-summary-panel');
    const data = await fetchJSON(`/farms/${farmId}/carbon`);
    if (!data || data.total_fields === 0) {
        container.style.display = 'none';
        return;
    }

    container.style.display = '';
    document.getElementById('carbon-co2e').textContent = data.total_co2e_tonnes.toFixed(1);
    document.getElementById('carbon-rate').textContent = data.soc_per_ha_rate.toFixed(2);
    document.getElementById('carbon-avg-soc').textContent = data.avg_soc_tonnes_per_ha.toFixed(1);

    const listEl = document.getElementById('carbon-fields-list');
    const trendIcon = { ganando: '+', estable: '=', perdiendo: '-', datos_insuficientes: '?' };
    const trendColor = { ganando: 'var(--accent)', estable: 'var(--text-muted)', perdiendo: '#e74c3c', datos_insuficientes: 'var(--text-muted)' };
    listEl.innerHTML = data.fields.map(f => `
        <div class="carbon-field-row">
            <span class="carbon-field-name">${esc(f.field_name)}</span>
            <span class="carbon-field-soc">${f.soc_tonnes_per_ha} t/ha</span>
            <span class="carbon-field-co2e">${f.co2e_tonnes} t CO2e</span>
            <span class="carbon-field-trend" style="color:${trendColor[f.tendencia] || 'var(--text-muted)'}">${trendIcon[f.tendencia] || '?'} ${f.clasificacion}</span>
        </div>
    `).join('');
}

// ── Multi-field comparison table ──
let comparisonSortField = 'health';
let comparisonSortAsc = false;
let comparisonData = [];

async function loadFieldComparison(farmId) {
    const container = document.getElementById('field-comparison-panel');
    const fields = fieldsByFarm[farmId] || [];
    if (fields.length === 0) {
        container.style.display = 'none';
        return;
    }

    const completeness = await fetchJSON(`/farms/${farmId}/data-completeness`);
    const completenessMap = {};
    if (completeness && completeness.fields) {
        completeness.fields.forEach(f => { completenessMap[f.field_id] = f; });
    }

    comparisonData = fields.map(f => {
        const health = healthByField[f.id];
        const ndvi = ndviByField[f.id];
        const soil = soilByField[f.id];
        const comp = completenessMap[f.id];
        const treatments = treatmentsByField[f.id];
        return {
            field_id: f.id,
            name: f.name,
            crop_type: f.crop_type || '--',
            hectares: f.hectares || 0,
            health_score: health ? health.score : null,
            health_trend: health ? (health.trend || trendByField[f.id]) : null,
            ndvi_mean: ndvi ? ndvi.ndvi_mean : null,
            soil_ph: soil ? soil.ph : null,
            treatment_count: treatments ? 1 : 0,
            completeness_score: comp ? comp.score : 0,
        };
    });

    comparisonSortField = 'health';
    comparisonSortAsc = false;
    renderFieldComparison(farmId);
    container.style.display = '';
}

function sortComparison(field) {
    if (comparisonSortField === field) {
        comparisonSortAsc = !comparisonSortAsc;
    } else {
        comparisonSortField = field;
        comparisonSortAsc = false;
    }
    renderFieldComparison(selectedFarmId);
}

function renderFieldComparison(farmId) {
    const content = document.getElementById('field-comparison-content');
    const sorted = [...comparisonData].sort((a, b) => {
        let va, vb;
        switch (comparisonSortField) {
            case 'name': va = a.name.toLowerCase(); vb = b.name.toLowerCase(); break;
            case 'health': va = a.health_score ?? -1; vb = b.health_score ?? -1; break;
            case 'ndvi': va = a.ndvi_mean ?? -1; vb = b.ndvi_mean ?? -1; break;
            case 'soil': va = a.soil_ph ?? -1; vb = b.soil_ph ?? -1; break;
            case 'treatments': va = a.treatment_count; vb = b.treatment_count; break;
            case 'completeness': va = a.completeness_score; vb = b.completeness_score; break;
            default: va = a.health_score ?? -1; vb = b.health_score ?? -1;
        }
        if (typeof va === 'string') return comparisonSortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
        return comparisonSortAsc ? va - vb : vb - va;
    });

    const arrow = (field) => comparisonSortField === field ? (comparisonSortAsc ? ' ▲' : ' ▼') : '';
    const trendIcon = (t) => {
        if (t === 'improving') return '<span style="color:var(--play-green)">↑</span>';
        if (t === 'declining') return '<span style="color:#e74c3c">↓</span>';
        if (t === 'stable') return '<span style="color:var(--watch-yellow)">→</span>';
        return '';
    };

    content.innerHTML = `
        <table class="comparison-table">
            <thead>
                <tr>
                    <th onclick="sortComparison('name')" class="comparison-sortable">Campo${arrow('name')}</th>
                    <th onclick="sortComparison('health')" class="comparison-sortable">Salud${arrow('health')}</th>
                    <th onclick="sortComparison('ndvi')" class="comparison-sortable">NDVI${arrow('ndvi')}</th>
                    <th onclick="sortComparison('soil')" class="comparison-sortable">pH${arrow('soil')}</th>
                    <th onclick="sortComparison('treatments')" class="comparison-sortable">Tratamientos${arrow('treatments')}</th>
                    <th onclick="sortComparison('completeness')" class="comparison-sortable">Datos${arrow('completeness')}</th>
                </tr>
            </thead>
            <tbody>
                ${sorted.map(f => `
                    <tr class="comparison-row" onclick="window.location.href='/campo?farm=${farmId}&field=${f.field_id}'" style="cursor:pointer">
                        <td>
                            <div class="comparison-field-name">${esc(f.name)}</div>
                            <div class="comparison-field-crop">${esc(f.crop_type)}</div>
                        </td>
                        <td>
                            <span class="health-badge ${healthClass(f.health_score)}">${healthLabel(f.health_score)}</span>
                            ${trendIcon(f.health_trend)}
                        </td>
                        <td>${f.ndvi_mean != null ? f.ndvi_mean.toFixed(2) : '--'}</td>
                        <td>${f.soil_ph != null ? f.soil_ph.toFixed(1) : '--'}</td>
                        <td>${f.treatment_count}</td>
                        <td>
                            <div class="comparison-completeness">
                                <div class="comparison-completeness-bar">
                                    <div class="comparison-completeness-fill" style="width:${Math.round(f.completeness_score)}%"></div>
                                </div>
                                <span class="comparison-completeness-pct">${Math.round(f.completeness_score)}%</span>
                            </div>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>`;
}

// ── Dashboard summary panel ──
async function loadDashboardSummary(farmId) {
    const container = document.getElementById('dashboard-summary');
    const data = await fetchJSON(`/farms/${farmId}/dashboard`);
    if (!data) {
        container.style.display = 'none';
        return;
    }

    container.style.display = '';
    document.getElementById('summary-farm-name').textContent = data.farm.name || '';
    document.getElementById('summary-fields').textContent = data.fields.length;

    const totalHa = data.fields.reduce((s, f) => s + (f.hectares || 0), 0);
    document.getElementById('summary-hectares').textContent = Math.round(totalHa);

    const healthEl = document.getElementById('summary-health');
    if (data.overall_health != null) {
        healthEl.textContent = Math.round(data.overall_health);
        healthEl.className = 'summary-stat-value health-' + healthClass(data.overall_health);
    } else {
        healthEl.textContent = '--';
        healthEl.className = 'summary-stat-value';
    }

    const crops = [...new Set(data.fields.map(f => f.crop_type).filter(Boolean))];
    document.getElementById('summary-crops').textContent = crops.length;

    // Treatment count
    document.getElementById('summary-treatments').textContent = data.treatment_count || 0;

    // Top risk field
    const riskEl = document.getElementById('summary-top-risk');
    if (data.top_risk) {
        const trendLabel = data.top_risk.trend === 'declining' ? 'En declive' : data.top_risk.trend === 'improving' ? 'Mejorando' : 'Estable';
        riskEl.innerHTML = `<div class="summary-risk-title">Mayor riesgo</div>
            <div class="summary-risk-item">
                <span class="summary-risk-name">${esc(data.top_risk.field_name)}</span>
                <span class="summary-alert-score health-badge critical">${Math.round(data.top_risk.score)}</span>
                <span class="summary-alert-trend">${trendLabel}</span>
            </div>`;
        riskEl.style.display = '';
    } else {
        riskEl.style.display = 'none';
    }

    // Show urgent fields (health < 50) as alerts
    const alertsEl = document.getElementById('summary-alerts');
    const urgentFields = data.fields.filter(f => f.latest_health_score && f.latest_health_score.score < 50);
    if (urgentFields.length > 0) {
        alertsEl.innerHTML = '<div class="summary-alerts-title">Campos que necesitan atencion</div>' +
            urgentFields.map(f => `
                <div class="summary-alert-item">
                    <span class="summary-alert-name">${esc(f.name)}</span>
                    <span class="summary-alert-score health-badge critical">${Math.round(f.latest_health_score.score)}</span>
                    <span class="summary-alert-trend">${f.latest_health_score.trend === 'declining' ? 'En declive' : f.latest_health_score.trend === 'improving' ? 'Mejorando' : 'Estable'}</span>
                </div>
            `).join('');
    } else {
        alertsEl.innerHTML = '';
    }
}

async function selectFarm(farmId) {
    selectedFarmId = farmId;
    fieldPanel.style.display = 'block';
    fieldList.innerHTML = '<div class="loading"><div class="loading-spinner"></div>Cargando campos...</div>';
    document.getElementById('alert-check-panel').style.display = '';
    await Promise.all([loadFieldsForFarm(farmId), loadWeather(farmId), loadHeatmap(farmId), loadNotifications(farmId), loadAlertConfig(farmId), loadSeasonalCalendar(farmId), loadAlertHistory(farmId), loadDashboardSummary(farmId), loadEconomicImpact(farmId), loadCarbonSummary(farmId), loadFieldComparison(farmId)]);
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
    document.getElementById('alert-history').style.display = 'none';
    document.getElementById('dashboard-summary').style.display = 'none';
    document.getElementById('summary-top-risk').style.display = 'none';
    document.getElementById('economic-impact-panel').style.display = 'none';
    document.getElementById('carbon-summary-panel').style.display = 'none';
    document.getElementById('field-comparison-panel').style.display = 'none';
    document.getElementById('alert-check-panel').style.display = 'none';
}

// ── Escape HTML ──
function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

// ── CSV Export ──
async function exportFarmCSV() {
    if (!selectedFarmId) return;
    const btn = document.getElementById('btn-export-csv');
    btn.disabled = true;
    btn.textContent = 'Exportando...';
    try {
        const resp = await fetch(`/api/farms/${selectedFarmId}/export?format=csv`);
        if (!resp.ok) throw new Error(`Error ${resp.status}`);
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const disposition = resp.headers.get('content-disposition') || '';
        const match = disposition.match(/filename="(.+?)"/);
        a.download = match ? match[1] : `export_granja_${selectedFarmId}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    } catch (e) {
        console.error('Export failed:', e);
        alert('No se pudo exportar los datos. Intenta de nuevo.');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Exportar Datos';
    }
}

// ── PDF Report Download ──
async function downloadFarmPDF() {
    if (!selectedFarmId) return;
    const btn = document.getElementById('btn-farm-pdf');
    btn.disabled = true;
    btn.textContent = 'Generando...';
    try {
        const resp = await fetch(`/api/farms/${selectedFarmId}/report`, { method: 'POST' });
        if (!resp.ok) throw new Error(`Error ${resp.status}`);
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `reporte_granja_${selectedFarmId}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    } catch (e) {
        console.error('PDF download failed:', e);
        alert('No se pudo generar el reporte. Intente de nuevo.');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Descargar Reporte PDF';
    }
}

// ── Portfolio PDF Report Download ──
async function downloadPortfolioPDF() {
    const btn = document.getElementById('btn-portfolio-pdf');
    btn.disabled = true;
    btn.textContent = 'Generando...';
    try {
        const resp = await fetch('/api/reports/portfolio', { method: 'POST' });
        if (!resp.ok) throw new Error(`Error ${resp.status}`);
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'reporte_portafolio.pdf';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    } catch (e) {
        console.error('Portfolio PDF download failed:', e);
        alert('No se pudo generar el reporte de portafolio. Intente de nuevo.');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Descargar Reporte de Portafolio';
    }
}

// ── Farm & Field Creation ──
function getAuthHeaders() {
    const token = localStorage.getItem('cultivOS_token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return headers;
}

async function seedDemoData() {
    const btn = document.getElementById('btn-seed-demo');
    btn.disabled = true;
    btn.textContent = 'Cargando...';
    try {
        const resp = await fetch(API + '/demo/seed', { method: 'POST' });
        const data = await resp.json();
        if (resp.status === 201) {
            btn.textContent = 'Datos cargados';
            await loadFarms();
            await Promise.all(farms.map(f => loadFieldsForFarm(f.id)));
            updateStats();
            renderFarms();
        } else {
            btn.textContent = 'Ya existen datos demo';
        }
    } catch {
        btn.textContent = 'Error al cargar';
    }
    setTimeout(() => {
        btn.disabled = false;
        btn.textContent = 'Cargar datos de ejemplo';
    }, 3000);
}

function toggleFarmForm() {
    const form = document.getElementById('farm-create-form');
    form.style.display = form.style.display === 'none' ? 'grid' : 'none';
    document.getElementById('farm-create-error').style.display = 'none';
}

function toggleFieldForm() {
    const form = document.getElementById('field-create-form');
    form.style.display = form.style.display === 'none' ? 'grid' : 'none';
    document.getElementById('field-create-error').style.display = 'none';
}

async function createFarm(event) {
    event.preventDefault();
    const btn = document.getElementById('btn-create-farm');
    const errEl = document.getElementById('farm-create-error');
    errEl.style.display = 'none';
    btn.disabled = true;
    btn.textContent = 'Creando...';

    const body = {
        name: document.getElementById('farm-name').value.trim(),
        owner_name: document.getElementById('farm-owner').value.trim() || null,
        total_hectares: parseFloat(document.getElementById('farm-hectares').value) || 0,
        municipality: document.getElementById('farm-municipality').value.trim() || null,
        state: document.getElementById('farm-state').value.trim() || 'Jalisco',
    };

    try {
        const resp = await fetch(API + '/farms', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(body),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: 'Error desconocido' }));
            throw new Error(err.detail || JSON.stringify(err));
        }
        document.getElementById('farm-create-form').reset();
        document.getElementById('farm-state').value = 'Jalisco';
        toggleFarmForm();
        await loadFarms();
        await Promise.all(farms.map(f => loadFieldsForFarm(f.id)));
        updateStats();
        renderFarms();
    } catch (e) {
        errEl.textContent = e.message;
        errEl.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Crear Granja';
    }
}

async function createField(event) {
    event.preventDefault();
    if (!selectedFarmId) return;
    const btn = document.getElementById('btn-create-field');
    const errEl = document.getElementById('field-create-error');
    errEl.style.display = 'none';
    btn.disabled = true;
    btn.textContent = 'Creando...';

    const body = {
        name: document.getElementById('field-name').value.trim(),
        crop_type: document.getElementById('field-crop-type').value.trim() || null,
        hectares: parseFloat(document.getElementById('field-hectares').value) || 0,
    };

    try {
        const resp = await fetch(API + `/farms/${selectedFarmId}/fields`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(body),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: 'Error desconocido' }));
            throw new Error(err.detail || JSON.stringify(err));
        }
        document.getElementById('field-create-form').reset();
        toggleFieldForm();
        delete fieldsByFarm[selectedFarmId];
        await selectFarm(selectedFarmId);
    } catch (e) {
        errEl.textContent = e.message;
        errEl.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Crear Campo';
    }
}

// ── Init ──
async function init() {
    await loadFarms();
    await Promise.all(farms.map(f => loadFieldsForFarm(f.id)));
    updateStats();
    renderFarms();
}

init();
