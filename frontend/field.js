/* -- cultivOS Field Detail -- field.js -- */

const API = '/api';

// -- Parse URL params --
const params = new URLSearchParams(window.location.search);
const farmId = params.get('farm');
const fieldId = params.get('field');

// -- Helpers --
function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

function healthClass(score) {
    if (score == null) return 'none';
    if (score > 70) return 'good';
    if (score >= 40) return 'warning';
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

// -- Load all field data --
async function loadFieldDetail() {
    if (!farmId || !fieldId) {
        document.getElementById('campo-title').textContent = 'Error: parametros faltantes';
        document.getElementById('campo-subtitle').textContent = 'URL debe incluir ?farm=ID&field=ID';
        return;
    }

    const base = `/farms/${farmId}/fields/${fieldId}`;

    // Fetch field info and all intelligence in parallel
    const [fields, healthList, ndviList, thermalList, soilList, treatments,
           irrigation, rotation, yieldPred, diseaseRisk, healthHistory,
           actionTimeline, intelligence, regenScore] = await Promise.all([
        fetchJSON(`/farms/${farmId}/fields`),
        fetchJSON(`${base}/health`),
        fetchJSON(`${base}/ndvi`),
        fetchJSON(`${base}/thermal`),
        fetchJSON(`${base}/soil`),
        fetchJSON(`${base}/treatments`),
        fetchJSON(`${base}/irrigation`),
        fetchJSON(`${base}/rotation`),
        fetchJSON(`${base}/yield`),
        fetchJSON(`${base}/disease-risk`),
        fetchJSON(`${base}/health/history`),
        fetchJSON(`${base}/action-timeline`),
        fetchJSON(`${base}/intelligence`),
        fetchJSON(`${base}/regenerative-score`),
    ]);

    // Find this field
    const field = fields ? fields.find(f => f.id === parseInt(fieldId)) : null;

    // Header
    if (field) {
        document.getElementById('campo-title').textContent = field.name;
        document.getElementById('campo-subtitle').textContent =
            (field.crop_type ? field.crop_type : '') + ' — ' + field.hectares + ' ha';
        document.getElementById('campo-hectares').textContent = field.hectares;
        document.getElementById('campo-crop').textContent = field.crop_type || '--';
    }

    // Back button links to farm
    document.getElementById('btn-back').onclick = function() {
        window.location.href = '/';
    };

    // Cerebro intelligence summary
    renderCerebro(intelligence);

    // Health score
    const latestHealth = healthList && healthList.length > 0 ? healthList[healthList.length - 1] : null;
    if (latestHealth) {
        const el = document.getElementById('campo-health');
        el.textContent = Math.round(latestHealth.score);
        el.className = 'stat-value health-badge ' + healthClass(latestHealth.score);
    }

    // NDVI
    const latestNdvi = ndviList && ndviList.length > 0 ? ndviList[ndviList.length - 1] : null;
    if (latestNdvi) {
        document.getElementById('campo-ndvi').textContent = latestNdvi.ndvi_mean.toFixed(2);
        renderNdvi(latestNdvi);
    }

    // Thermal
    const latestThermal = thermalList && thermalList.length > 0 ? thermalList[thermalList.length - 1] : null;
    if (latestThermal) renderThermal(latestThermal);

    // Soil
    const latestSoil = soilList && soilList.length > 0 ? soilList[soilList.length - 1] : null;
    if (latestSoil) renderSoil(latestSoil);

    // Disease risk
    if (diseaseRisk) renderDisease(diseaseRisk);

    // Irrigation
    if (irrigation) renderIrrigation(irrigation);

    // Yield
    if (yieldPred) renderYield(yieldPred);

    // Treatments
    if (treatments && treatments.length > 0) renderTreatments(treatments);

    // Rotation
    if (rotation && rotation.seasons) renderRotation(rotation);

    // Action timeline
    renderActionTimeline(actionTimeline);

    // Regenerative score
    renderRegenerativeScore(regenScore);

    // Health history chart
    if (healthHistory && healthHistory.scores && healthHistory.scores.length > 0) {
        renderHealthChart(healthHistory);
    }
}

// -- Render functions --

function renderNdvi(ndvi) {
    const zones = ndvi.zones || {};
    document.getElementById('ndvi-content').innerHTML = `
        <div class="campo-data-grid">
            <div class="campo-data-item">
                <span class="campo-data-label">NDVI Promedio</span>
                <span class="campo-data-value">${ndvi.ndvi_mean.toFixed(3)}</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Min</span>
                <span class="campo-data-value">${ndvi.ndvi_min.toFixed(3)}</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Max</span>
                <span class="campo-data-value">${ndvi.ndvi_max.toFixed(3)}</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Estres</span>
                <span class="campo-data-value">${ndvi.stress_pct != null ? ndvi.stress_pct.toFixed(1) + '%' : '--'}</span>
            </div>
        </div>
        ${Object.keys(zones).length > 0 ? `
        <div class="campo-zones">
            <div class="campo-data-label" style="margin-bottom:6px">Zonas de salud</div>
            ${Object.entries(zones).map(([zone, pct]) => `
                <div class="campo-zone-bar">
                    <span class="campo-zone-label">${esc(zone)}</span>
                    <div class="campo-zone-track">
                        <div class="campo-zone-fill zone-${zone.toLowerCase().replace(/\s+/g, '-')}" style="width:${pct}%"></div>
                    </div>
                    <span class="campo-zone-pct">${pct.toFixed(0)}%</span>
                </div>
            `).join('')}
        </div>` : ''}`;
}

function renderThermal(thermal) {
    const stressCls = thermal.stress_pct > 30 ? 'critical' : thermal.stress_pct > 10 ? 'warning' : 'good';
    document.getElementById('thermal-content').innerHTML = `
        <div class="campo-data-grid">
            <div class="campo-data-item">
                <span class="campo-data-label">Temp Promedio</span>
                <span class="campo-data-value">${thermal.temp_mean.toFixed(1)}C</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Min</span>
                <span class="campo-data-value">${thermal.temp_min.toFixed(1)}C</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Max</span>
                <span class="campo-data-value">${thermal.temp_max.toFixed(1)}C</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Pixeles Estresados</span>
                <span class="campo-data-value health-badge ${stressCls}">${thermal.stress_pct.toFixed(1)}%</span>
            </div>
        </div>
        ${thermal.irrigation_deficit ? '<div class="campo-alert-badge critical">Deficit de riego detectado</div>' : ''}`;
}

function renderSoil(soil) {
    const phCls = (soil.ph >= 6.0 && soil.ph <= 7.0) ? 'good' : (soil.ph >= 5.5 && soil.ph <= 7.5) ? 'warning' : 'critical';
    document.getElementById('soil-content').innerHTML = `
        <div class="campo-data-grid">
            <div class="campo-data-item">
                <span class="campo-data-label">pH</span>
                <span class="campo-data-value health-badge ${phCls}">${soil.ph}</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Materia Organica</span>
                <span class="campo-data-value">${soil.organic_matter_pct}%</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Nitrogeno</span>
                <span class="campo-data-value">${soil.nitrogen_ppm} ppm</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Fosforo</span>
                <span class="campo-data-value">${soil.phosphorus_ppm} ppm</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Potasio</span>
                <span class="campo-data-value">${soil.potassium_ppm} ppm</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Humedad</span>
                <span class="campo-data-value">${soil.moisture_pct}%</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Textura</span>
                <span class="campo-data-value">${esc(soil.texture || '--')}</span>
            </div>
        </div>`;
}

function renderDisease(risk) {
    const riskCls = risk.risk_level === 'alto' ? 'critical' : risk.risk_level === 'medio' ? 'warning' : 'good';
    document.getElementById('disease-content').innerHTML = `
        <div class="campo-data-grid">
            <div class="campo-data-item">
                <span class="campo-data-label">Nivel de Riesgo</span>
                <span class="campo-data-value health-badge ${riskCls}">${esc(risk.risk_level || '--')}</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Tipo</span>
                <span class="campo-data-value">${esc(risk.risk_type || '--')}</span>
            </div>
        </div>
        ${risk.description ? `<div class="campo-risk-desc">${esc(risk.description)}</div>` : ''}
        ${risk.recommendations && risk.recommendations.length > 0 ? `
            <div class="campo-risk-recs">
                ${risk.recommendations.map(r => `<div class="campo-risk-rec">${esc(r)}</div>`).join('')}
            </div>` : ''}`;
}

function renderIrrigation(irrigation) {
    const urgCls = irrigation.urgency === 'critico' ? 'critical' : irrigation.urgency === 'moderado' ? 'warning' : 'good';
    let scheduleHtml = '';
    if (irrigation.schedule && irrigation.schedule.length > 0) {
        scheduleHtml = `
        <div class="campo-schedule">
            ${irrigation.schedule.map(day => `
                <div class="campo-schedule-day">
                    <span class="campo-schedule-date">${esc(day.date || day.dia || '')}</span>
                    <span class="campo-schedule-liters">${day.liters_per_ha || day.litros_por_ha || 0} L/ha</span>
                </div>
            `).join('')}
        </div>`;
    }
    document.getElementById('irrigation-content').innerHTML = `
        <div class="campo-data-grid">
            <div class="campo-data-item">
                <span class="campo-data-label">Urgencia</span>
                <span class="campo-data-value health-badge ${urgCls}">${esc(irrigation.urgency || irrigation.urgencia || '--')}</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">L/ha Total Semana</span>
                <span class="campo-data-value">${irrigation.total_liters_week || irrigation.total_litros_semana || '--'}</span>
            </div>
        </div>
        ${irrigation.recommendation || irrigation.recomendacion ? `<div class="campo-risk-desc">${esc(irrigation.recommendation || irrigation.recomendacion)}</div>` : ''}
        ${scheduleHtml}`;
}

function renderYield(yieldData) {
    document.getElementById('yield-content').innerHTML = `
        <div class="campo-data-grid">
            <div class="campo-data-item">
                <span class="campo-data-label">Rendimiento Estimado</span>
                <span class="campo-data-value">${yieldData.predicted_yield_kg_ha ? yieldData.predicted_yield_kg_ha.toLocaleString() + ' kg/ha' : '--'}</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Rango</span>
                <span class="campo-data-value">${yieldData.low_estimate ? yieldData.low_estimate.toLocaleString() : '--'} — ${yieldData.high_estimate ? yieldData.high_estimate.toLocaleString() : '--'} kg/ha</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Cultivo</span>
                <span class="campo-data-value">${esc(yieldData.crop_type || '--')}</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Base SIAP</span>
                <span class="campo-data-value">${yieldData.baseline_yield_kg_ha ? yieldData.baseline_yield_kg_ha.toLocaleString() + ' kg/ha' : '--'}</span>
            </div>
        </div>`;
}

function renderTreatments(treatments) {
    document.getElementById('treatments-content').innerHTML = treatments.map(t => `
        <div class="campo-treatment-card">
            ${t.problema ? `<div class="campo-treatment-row"><strong>Problema:</strong> ${esc(t.problema)}</div>` : ''}
            ${t.tratamiento ? `<div class="campo-treatment-row"><strong>Tratamiento:</strong> ${esc(t.tratamiento)}</div>` : ''}
            ${t.costo_estimado_mxn ? `<div class="campo-treatment-row"><strong>Costo:</strong> $${t.costo_estimado_mxn.toLocaleString()} MXN/ha</div>` : ''}
            ${t.urgencia ? `<div class="campo-treatment-row"><span class="campo-alert-badge ${t.urgencia.toLowerCase() === 'inmediata' ? 'critical' : 'warning'}">${esc(t.urgencia)}</span></div>` : ''}
            ${t.prevencion ? `<div class="campo-treatment-row"><strong>Prevencion:</strong> ${esc(t.prevencion)}</div>` : ''}
        </div>
    `).join('');
}

function renderRotation(rotation) {
    document.getElementById('rotation-content').innerHTML = `
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
        </div>`;
}

function renderActionTimeline(timeline) {
    const el = document.getElementById('timeline-content');
    if (!timeline || !timeline.actions || timeline.actions.length === 0) {
        el.innerHTML = '<div class="campo-placeholder">Sin acciones programadas para esta semana</div>';
        return;
    }

    // Sort by priority (lower number = higher priority)
    const actions = [...timeline.actions].sort((a, b) => a.priority - b.priority);

    const priorityLabel = (p) => {
        if (p <= 1) return 'alta';
        if (p <= 2) return 'media';
        return 'baja';
    };

    const priorityCls = (p) => {
        if (p <= 1) return 'priority-alta';
        if (p <= 2) return 'priority-media';
        return 'priority-baja';
    };

    let weatherHtml = '';
    if (timeline.weather_summary) {
        const ws = timeline.weather_summary;
        weatherHtml = `
        <div class="timeline-weather">
            <span class="timeline-weather-item">${ws.total_rainfall_mm.toFixed(0)} mm lluvia</span>
            <span class="timeline-weather-item">${ws.min_temp_c.toFixed(0)}-${ws.max_temp_c.toFixed(0)}C</span>
            ${ws.rainy_days > 0 ? `<span class="timeline-weather-item timeline-rain">${ws.rainy_days} dias con lluvia</span>` : ''}
        </div>`;
    }

    el.innerHTML = `
        ${weatherHtml}
        <div class="timeline-list">
            ${actions.map(a => `
                <div class="timeline-action">
                    <div class="timeline-action-header">
                        <span class="timeline-priority-badge ${priorityCls(a.priority)}">${priorityLabel(a.priority)}</span>
                        <span class="timeline-action-type">${esc(a.action_type)}</span>
                    </div>
                    <div class="timeline-action-desc">${esc(a.description)}</div>
                    ${a.weather_note ? `<div class="timeline-weather-note">${esc(a.weather_note)}</div>` : ''}
                    ${a.urgencia ? `<div class="timeline-action-meta"><strong>Urgencia:</strong> ${esc(a.urgencia)}</div>` : ''}
                    ${a.costo_estimado_mxn ? `<div class="timeline-action-meta"><strong>Costo:</strong> $${a.costo_estimado_mxn.toLocaleString()} MXN/ha</div>` : ''}
                    ${a.stage_es ? `<div class="timeline-action-meta"><strong>Etapa:</strong> ${esc(a.stage_es)}${a.days_in_stage != null ? ' (dia ' + a.days_in_stage + ')' : ''}</div>` : ''}
                </div>
            `).join('')}
        </div>`;
}

function renderRegenerativeScore(data) {
    const el = document.getElementById('regenerative-content');
    if (!data) {
        el.innerHTML = '<div class="campo-placeholder">Sin datos de puntuacion regenerativa</div>';
        return;
    }

    const score = data.score;
    const scoreCls = score >= 70 ? 'good' : score >= 40 ? 'warning' : 'critical';
    const bd = data.breakdown;

    // Component labels (Spanish) and max values
    const components = [
        { key: 'organic_treatments', label: 'Tratamientos organicos', max: 25 },
        { key: 'ancestral_methods', label: 'Metodos ancestrales', max: 20 },
        { key: 'soil_organic_trend', label: 'Tendencia materia organica', max: 25 },
        { key: 'microbiome_health', label: 'Salud del microbioma', max: 20 },
        { key: 'treatment_diversity', label: 'Diversidad de tratamientos', max: 10 },
    ];

    const barsHtml = components.map(c => {
        const val = bd[c.key] || 0;
        const pct = Math.round((val / c.max) * 100);
        return `
            <div class="regen-component">
                <div class="regen-component-header">
                    <span class="regen-component-label">${c.label}</span>
                    <span class="regen-component-value">${val.toFixed(1)}/${c.max}</span>
                </div>
                <div class="regen-bar-track">
                    <div class="regen-bar-fill regen-bar-${pct >= 70 ? 'good' : pct >= 40 ? 'warning' : 'critical'}" style="width:${pct}%"></div>
                </div>
            </div>`;
    }).join('');

    const recsHtml = data.recommendations && data.recommendations.length > 0
        ? `<div class="regen-recs">
            <div class="regen-recs-title">Recomendaciones</div>
            ${data.recommendations.map(r => `<div class="regen-rec-item">${esc(r)}</div>`).join('')}
           </div>`
        : '';

    el.innerHTML = `
        <div class="regen-card">
            <div class="regen-hero">
                <div class="regen-score health-badge ${scoreCls}">${Math.round(score)}</div>
                <div class="regen-score-label">/ 100</div>
            </div>
            <div class="regen-components">${barsHtml}</div>
            ${recsHtml}
        </div>`;
}

function renderHealthChart(history) {
    const scores = history.scores;
    const labels = scores.map((s, i) => s.date || '#' + (i + 1));
    const data = scores.map(s => s.score);

    const ctx = document.getElementById('health-chart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Salud',
                data: data,
                borderColor: '#16a34a',
                backgroundColor: 'rgba(22, 163, 74, 0.1)',
                fill: true,
                tension: 0.3,
                pointRadius: 4,
                pointBackgroundColor: '#16a34a',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    ticks: { stepSize: 20 }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

// -- Cerebro Intelligence Summary --
function renderCerebro(intel) {
    const el = document.getElementById('cerebro-content');
    if (!intel) {
        el.innerHTML = '<div class="campo-placeholder">Sin datos de inteligencia disponibles</div>';
        return;
    }

    // Health score — big number + trend
    const h = intel.health;
    const healthCls = h ? (h.score > 70 ? 'good' : h.score >= 40 ? 'warning' : 'critical') : 'none';
    const trendArrow = h ? (h.trend === 'improving' ? ' &#x25B2;' : h.trend === 'declining' ? ' &#x25BC;' : ' &#x25CF;') : '';
    const trendCls = h ? (h.trend === 'improving' ? 'cerebro-trend-up' : h.trend === 'declining' ? 'cerebro-trend-down' : 'cerebro-trend-stable') : '';

    // NDVI badge
    const ndvi = intel.ndvi;
    const ndviStatus = ndvi ? (ndvi.ndvi_mean >= 0.6 ? 'Saludable' : ndvi.ndvi_mean >= 0.3 ? 'Moderado' : 'Estresado') : null;
    const ndviCls = ndvi ? (ndvi.ndvi_mean >= 0.6 ? 'good' : ndvi.ndvi_mean >= 0.3 ? 'warning' : 'critical') : '';

    // Soil summary
    const soil = intel.soil;

    // Weather
    const weather = intel.weather;

    // Growth stage
    const gs = intel.growth_stage;

    // Disease risk
    const dr = intel.disease_risk;
    const drCls = dr ? (dr.risk_level === 'alto' ? 'critical' : dr.risk_level === 'medio' ? 'warning' : 'good') : '';

    // Treatment count
    const treatCount = intel.treatments ? intel.treatments.length : 0;

    el.innerHTML = `
        <div class="cerebro-grid">
            <div class="cerebro-hero">
                <div class="cerebro-score-wrap">
                    <div class="cerebro-score health-badge ${healthCls}">${h ? Math.round(h.score) : '--'}</div>
                    <div class="cerebro-score-label">Salud <span class="${trendCls}">${trendArrow}</span></div>
                </div>
            </div>
            <div class="cerebro-badges">
                ${ndvi ? `<div class="cerebro-badge"><span class="cerebro-badge-label">NDVI</span><span class="health-badge ${ndviCls}">${ndvi.ndvi_mean.toFixed(2)} — ${ndviStatus}</span></div>` : ''}
                ${soil ? `<div class="cerebro-badge"><span class="cerebro-badge-label">pH</span><span class="campo-data-value">${soil.ph}</span></div>` : ''}
                ${soil && soil.organic_matter_pct != null ? `<div class="cerebro-badge"><span class="cerebro-badge-label">Materia Org.</span><span class="campo-data-value">${soil.organic_matter_pct}%</span></div>` : ''}
                ${weather ? `<div class="cerebro-badge"><span class="cerebro-badge-label">Clima</span><span class="campo-data-value">${Math.round(weather.temp_c)}C &middot; ${Math.round(weather.humidity_pct)}% hum</span></div>` : ''}
                ${gs ? `<div class="cerebro-badge"><span class="cerebro-badge-label">Etapa</span><span class="campo-data-value">${esc(gs.stage_es)}</span></div>` : ''}
                ${dr ? `<div class="cerebro-badge"><span class="cerebro-badge-label">Riesgo</span><span class="health-badge ${drCls}">${esc(dr.risk_level)}</span></div>` : ''}
                ${treatCount > 0 ? `<div class="cerebro-badge"><span class="cerebro-badge-label">Tratamientos</span><span class="campo-data-value">${treatCount} activos</span></div>` : ''}
            </div>
        </div>`;
}

// -- Init --
loadFieldDetail();
