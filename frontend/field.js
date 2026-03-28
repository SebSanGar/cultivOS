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
           actionTimeline, intelligence, regenScore, seasonalData,
           missionPlan, interventionScores, microbiomeList, growthStage,
           feedbackList, treatmentHistory, flightsList, flightStats,
           anomaliesData, completenessData, regionalData] = await Promise.all([
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
        fetchJSON(`${base}/seasonal-comparison`),
        fetchJSON(`${base}/mission-plan`),
        fetchJSON(`${base}/intervention-scores`),
        fetchJSON(`${base}/microbiome`),
        fetchJSON(`${base}/growth-stage`),
        fetchJSON(`${base}/feedback`),
        fetchJSON(`${base}/treatments/treatment-history`),
        fetchJSON(`${base}/flights`),
        fetchJSON(`${base}/flights/stats`),
        fetchJSON(`${base}/anomalies`),
        fetchJSON(`/farms/${farmId}/data-completeness`),
        fetchJSON(`/farms/${farmId}/recommendations`),
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
    }
    renderNdviHistory(ndviList);

    // Thermal
    const latestThermal = thermalList && thermalList.length > 0 ? thermalList[thermalList.length - 1] : null;
    renderThermalHistory(thermalList);

    // Soil
    const latestSoil = soilList && soilList.length > 0 ? soilList[soilList.length - 1] : null;
    if (latestSoil) renderSoil(latestSoil);

    // Soil history timeline
    renderSoilHistory(soilList);

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

    // Regional context
    renderRegionalCard(regionalData, parseInt(fieldId));

    // Action timeline
    renderActionTimeline(actionTimeline);

    // Regenerative score
    renderRegenerativeScore(regenScore);

    // Seasonal comparison
    renderSeasonalComparison(seasonalData);

    // Mission plan
    renderMissionPlan(missionPlan);

    // Flight log history
    renderFlights(flightsList, flightStats);

    // Intervention scores
    renderInterventionScores(interventionScores);

    // Microbiome
    renderMicrobiome(microbiomeList);

    // Growth stage
    renderGrowthStage(growthStage);

    // Treatment history timeline
    renderTreatmentHistory(treatmentHistory);

    // Feedback — populate treatment dropdown and render entries
    renderFeedback(feedbackList, treatments);

    // Anomaly detection
    renderAnomalies(anomaliesData);

    // Data completeness
    renderDataCompleteness(completenessData, parseInt(fieldId));

    // Sensor fusion quality
    renderFusion(intelligence ? intelligence.fusion : null);

    // Health history chart
    if (healthHistory && healthHistory.scores && healthHistory.scores.length > 0) {
        renderHealthChart(healthHistory);
    }

    // Health drill-down records
    renderHealthHistory(healthList);
}

// -- Render functions --

function renderNdviDetail(ndvi) {
    const zones = ndvi.zones || {};
    return `
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
                <span class="campo-data-label">Desv. Estandar</span>
                <span class="campo-data-value">${ndvi.ndvi_std != null ? ndvi.ndvi_std.toFixed(3) : '--'}</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Estres</span>
                <span class="campo-data-value">${ndvi.stress_pct != null ? ndvi.stress_pct.toFixed(1) + '%' : '--'}</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Pixeles Total</span>
                <span class="campo-data-value">${ndvi.pixels_total != null ? ndvi.pixels_total.toLocaleString() : '--'}</span>
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
                    <span class="campo-zone-pct">${typeof pct === 'number' ? pct.toFixed(0) : pct}%</span>
                </div>
            `).join('')}
        </div>` : ''}`;
}

function renderNdviHistory(list) {
    const el = document.getElementById('ndvi-content');
    if (!list || list.length === 0) {
        el.innerHTML = '<div class="campo-placeholder">Sin datos NDVI</div>';
        return;
    }
    // Show latest as primary view, then historical records below
    const latest = list[list.length - 1];
    const older = list.slice(0, -1).reverse(); // newest first (excluding latest)

    let html = '<div class="sensor-latest-label">Ultimo analisis</div>';
    html += renderNdviDetail(latest);

    if (older.length > 0) {
        html += '<div class="sensor-history-label">Historial de analisis NDVI</div>';
        html += '<div class="sensor-timeline">';
        html += older.map(ndvi => {
            const date = ndvi.analyzed_at
                ? new Date(ndvi.analyzed_at).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' })
                : '--';
            const statusCls = ndvi.ndvi_mean >= 0.6 ? 'good' : ndvi.ndvi_mean >= 0.3 ? 'warning' : 'critical';
            const statusLabel = ndvi.ndvi_mean >= 0.6 ? 'Saludable' : ndvi.ndvi_mean >= 0.3 ? 'Moderado' : 'Estresado';
            return `<div class="sensor-timeline-item">
                <div class="sensor-timeline-date">${date}</div>
                <div class="sensor-timeline-body">
                    <div class="sensor-timeline-header" onclick="this.parentElement.querySelector('.sensor-timeline-detail').classList.toggle('open')">
                        <span class="health-badge ${statusCls}">${statusLabel}</span>
                        <span class="sensor-timeline-summary">NDVI ${ndvi.ndvi_mean.toFixed(3)} | Estres ${ndvi.stress_pct != null ? ndvi.stress_pct.toFixed(1) + '%' : '--'}</span>
                        <span class="sensor-timeline-expand">&#9660;</span>
                    </div>
                    <div class="sensor-timeline-detail">
                        ${renderNdviDetail(ndvi)}
                    </div>
                </div>
            </div>`;
        }).join('');
        html += '</div>';
    }
    el.innerHTML = html;
}

function renderThermalDetail(thermal) {
    const stressCls = thermal.stress_pct > 30 ? 'critical' : thermal.stress_pct > 10 ? 'warning' : 'good';
    return `
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
                <span class="campo-data-label">Desv. Estandar</span>
                <span class="campo-data-value">${thermal.temp_std != null ? thermal.temp_std.toFixed(1) + 'C' : '--'}</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Pixeles Estresados</span>
                <span class="campo-data-value health-badge ${stressCls}">${thermal.stress_pct.toFixed(1)}%</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Pixeles Total</span>
                <span class="campo-data-value">${thermal.pixels_total != null ? thermal.pixels_total.toLocaleString() : '--'}</span>
            </div>
        </div>
        ${thermal.irrigation_deficit ? '<div class="campo-alert-badge critical">Deficit de riego detectado</div>' : ''}`;
}

function renderThermalHistory(list) {
    const el = document.getElementById('thermal-content');
    if (!list || list.length === 0) {
        el.innerHTML = '<div class="campo-placeholder">Sin datos termicos</div>';
        return;
    }
    const latest = list[list.length - 1];
    const older = list.slice(0, -1).reverse();

    let html = '<div class="sensor-latest-label">Ultimo analisis</div>';
    html += renderThermalDetail(latest);

    if (older.length > 0) {
        html += '<div class="sensor-history-label">Historial de analisis termico</div>';
        html += '<div class="sensor-timeline">';
        html += older.map(t => {
            const date = t.analyzed_at
                ? new Date(t.analyzed_at).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' })
                : '--';
            const stCls = t.stress_pct > 30 ? 'critical' : t.stress_pct > 10 ? 'warning' : 'good';
            const stLabel = t.stress_pct > 30 ? 'Alto estres' : t.stress_pct > 10 ? 'Estres moderado' : 'Normal';
            return `<div class="sensor-timeline-item">
                <div class="sensor-timeline-date">${date}</div>
                <div class="sensor-timeline-body">
                    <div class="sensor-timeline-header" onclick="this.parentElement.querySelector('.sensor-timeline-detail').classList.toggle('open')">
                        <span class="health-badge ${stCls}">${stLabel}</span>
                        <span class="sensor-timeline-summary">${t.temp_mean.toFixed(1)}C prom | Estres ${t.stress_pct.toFixed(1)}%</span>
                        ${t.irrigation_deficit ? '<span class="campo-alert-badge critical" style="font-size:0.7rem;padding:1px 6px">Deficit</span>' : ''}
                        <span class="sensor-timeline-expand">&#9660;</span>
                    </div>
                    <div class="sensor-timeline-detail">
                        ${renderThermalDetail(t)}
                    </div>
                </div>
            </div>`;
        }).join('');
        html += '</div>';
    }
    el.innerHTML = html;
}

function renderSoil(soil) {
    const phCls = (soil.ph >= 6.0 && soil.ph <= 7.0) ? 'good' : (soil.ph >= 5.5 && soil.ph <= 7.5) ? 'warning' : 'critical';
    const nCls = (soil.nitrogen_ppm >= 25 && soil.nitrogen_ppm <= 50) ? 'good' : (soil.nitrogen_ppm >= 10 && soil.nitrogen_ppm <= 80) ? 'warning' : 'critical';
    const pCls = (soil.phosphorus_ppm >= 15 && soil.phosphorus_ppm <= 40) ? 'good' : (soil.phosphorus_ppm >= 5 && soil.phosphorus_ppm <= 60) ? 'warning' : 'critical';
    const kCls = (soil.potassium_ppm >= 120 && soil.potassium_ppm <= 250) ? 'good' : (soil.potassium_ppm >= 80 && soil.potassium_ppm <= 350) ? 'warning' : 'critical';
    const omCls = (soil.organic_matter_pct >= 3.0 && soil.organic_matter_pct <= 6.0) ? 'good' : (soil.organic_matter_pct >= 1.5 && soil.organic_matter_pct <= 8.0) ? 'warning' : 'critical';
    document.getElementById('soil-content').innerHTML = `
        <div class="campo-data-grid">
            <div class="campo-data-item">
                <span class="campo-data-label">pH</span>
                <span class="campo-data-value health-badge ${phCls}">${soil.ph}</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Materia Organica</span>
                <span class="campo-data-value health-badge ${omCls}">${soil.organic_matter_pct}%</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Nitrogeno</span>
                <span class="campo-data-value health-badge ${nCls}">${soil.nitrogen_ppm} ppm</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Fosforo</span>
                <span class="campo-data-value health-badge ${pCls}">${soil.phosphorus_ppm} ppm</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Potasio</span>
                <span class="campo-data-value health-badge ${kCls}">${soil.potassium_ppm} ppm</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Humedad</span>
                <span class="campo-data-value">${soil.moisture_pct}%</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Textura</span>
                <span class="campo-data-value">${esc(soil.texture || '--')}</span>
            </div>
        </div>
        ${soil.recommendations ? `<div class="campo-data-item" style="margin-top:0.75rem;grid-column:1/-1"><span class="campo-data-label">Recomendaciones</span><p class="campo-data-value">${esc(soil.recommendations)}</p></div>` : ''}`;
}

function renderSoilHistory(list) {
    const el = document.getElementById('soil-history-content');
    if (!list || list.length === 0) {
        el.innerHTML = '<div class="campo-placeholder">Sin historial de suelo</div>';
        return;
    }
    el.innerHTML = `<div class="soil-timeline">
        ${list.map((s, i) => {
            const date = s.sampled_at ? new Date(s.sampled_at).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' }) : '--';
            const phCls = (s.ph >= 6.0 && s.ph <= 7.0) ? 'good' : (s.ph >= 5.5 && s.ph <= 7.5) ? 'warning' : 'critical';
            return `<div class="soil-timeline-item">
                <div class="soil-timeline-date">${date}</div>
                <div class="soil-timeline-body">
                    <div class="soil-timeline-header" onclick="this.parentElement.querySelector('.soil-timeline-detail').classList.toggle('open')">
                        <span class="health-badge ${phCls}">pH ${s.ph != null ? s.ph : '--'}</span>
                        <span class="soil-timeline-om">${s.organic_matter_pct != null ? s.organic_matter_pct + '% MO' : ''}</span>
                        <span class="soil-timeline-texture">${esc(s.texture || '')}</span>
                        <span class="soil-timeline-expand">&#9660;</span>
                    </div>
                    <div class="soil-timeline-detail">
                        <div class="campo-data-grid">
                            ${s.nitrogen_ppm != null ? `<div class="campo-data-item"><span class="campo-data-label">N</span><span class="campo-data-value">${s.nitrogen_ppm} ppm</span></div>` : ''}
                            ${s.phosphorus_ppm != null ? `<div class="campo-data-item"><span class="campo-data-label">P</span><span class="campo-data-value">${s.phosphorus_ppm} ppm</span></div>` : ''}
                            ${s.potassium_ppm != null ? `<div class="campo-data-item"><span class="campo-data-label">K</span><span class="campo-data-value">${s.potassium_ppm} ppm</span></div>` : ''}
                            ${s.moisture_pct != null ? `<div class="campo-data-item"><span class="campo-data-label">Humedad</span><span class="campo-data-value">${s.moisture_pct}%</span></div>` : ''}
                            ${s.electrical_conductivity != null ? `<div class="campo-data-item"><span class="campo-data-label">CE</span><span class="campo-data-value">${s.electrical_conductivity} dS/m</span></div>` : ''}
                            ${s.depth_cm != null ? `<div class="campo-data-item"><span class="campo-data-label">Prof.</span><span class="campo-data-value">${s.depth_cm} cm</span></div>` : ''}
                        </div>
                        ${s.recommendations ? `<div class="soil-timeline-rec">${esc(s.recommendations)}</div>` : ''}
                        ${s.notes ? `<div class="soil-timeline-notes">${esc(s.notes)}</div>` : ''}
                    </div>
                </div>
            </div>`;
        }).join('')}
    </div>`;
}

function renderDisease(risk) {
    const riskCls = risk.risk_level === 'alto' ? 'critical' : risk.risk_level === 'medio' ? 'warning' : 'good';
    const urgencyLabel = {'critico': 'Critico', 'alto': 'Alto', 'medio': 'Medio', 'bajo': 'Bajo'};

    // Risk items from the risks array
    let risksHtml = '';
    if (risk.risks && risk.risks.length > 0) {
        risksHtml = `<div class="disease-risks-list">
            ${risk.risks.map(r => {
                const urgCls = r.urgencia === 'critico' || r.urgencia === 'alto' ? 'critical'
                    : r.urgencia === 'medio' ? 'warning' : 'good';
                return `<div class="disease-riesgo-item">
                    <div class="disease-riesgo-header">
                        <span class="disease-riesgo-tipo">${esc(r.tipo)}</span>
                        <span class="health-badge ${urgCls}">${esc(urgencyLabel[r.urgencia] || r.urgencia)}</span>
                        ${r.organico ? '<span class="disease-organic-badge">Organico</span>' : ''}
                    </div>
                    <div class="disease-riesgo-desc">${esc(r.descripcion)}</div>
                    <div class="disease-riesgo-rec">
                        <span class="campo-data-label">Recomendacion:</span> ${esc(r.recomendacion)}
                    </div>
                </div>`;
            }).join('')}
        </div>`;
    }

    // Weather context
    let weatherHtml = '';
    if (risk.weather_context) {
        const wc = risk.weather_context;
        weatherHtml = `<div class="disease-weather-ctx">
            <span class="campo-data-label">Contexto climatico:</span>
            ${wc.temp_c.toFixed(1)} C | ${wc.humidity_pct.toFixed(0)}% humedad | ${wc.rainfall_mm.toFixed(1)} mm lluvia
        </div>`;
    }

    document.getElementById('disease-content').innerHTML = `
        <div class="campo-data-grid">
            <div class="campo-data-item">
                <span class="campo-data-label">Nivel de Riesgo</span>
                <span class="campo-data-value health-badge ${riskCls}">${esc(risk.risk_level || '--')}</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Evaluacion</span>
                <span class="campo-data-value">${esc(risk.mensaje || '--')}</span>
            </div>
        </div>
        ${risksHtml}
        ${weatherHtml}
        ${risk.nota ? `<div class="disease-nota">${esc(risk.nota)}</div>` : ''}`;
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

function renderTreatmentHistory(history) {
    const el = document.getElementById('treatment-history-content');
    if (!history || history.length === 0) {
        el.innerHTML = '<div class="campo-placeholder">Sin historial de tratamientos aplicados</div>';
        return;
    }
    el.innerHTML = `<div class="treatment-timeline">
        ${history.map(h => {
            const date = h.applied_at ? new Date(h.applied_at).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' }) : '--';
            const urgCls = h.urgencia === 'alta' ? 'critical' : (h.urgencia === 'media' ? 'warning' : 'good');
            return `<div class="treatment-timeline-item">
                <div class="treatment-timeline-date">${date}</div>
                <div class="treatment-timeline-body">
                    <div class="treatment-timeline-header">
                        <strong>${esc(h.problema)}</strong>
                        <span class="campo-alert-badge ${urgCls}">${esc(h.urgencia)}</span>
                        ${h.organic ? '<span class="organic-badge">Organico</span>' : ''}
                    </div>
                    <div class="treatment-timeline-detail">${esc(h.tratamiento)}</div>
                    ${h.applied_notes ? `<div class="treatment-timeline-notes">${esc(h.applied_notes)}</div>` : ''}
                </div>
            </div>`;
        }).join('')}
    </div>`;
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

function renderRegionalCard(data, currentFieldId) {
    const el = document.getElementById('regional-content');
    if (!data || !data.region) {
        el.innerHTML = '<div class="campo-placeholder">Sin datos regionales disponibles</div>';
        return;
    }

    const r = data.region;
    const climaLabels = {
        'tropical_subtropical': 'Tropical / Subtropical',
        'temperate_continental': 'Templado Continental',
        'generic': 'Variable',
    };

    // Filter recommendations to current field
    const fieldRecs = (data.recommendations || []).filter(rec => rec.field_id === currentFieldId);

    let recsHtml = '';
    if (fieldRecs.length > 0) {
        recsHtml = `
        <div class="regional-recs">
            <div class="regional-recs-title">Recomendaciones para este campo</div>
            ${fieldRecs.slice(0, 3).map(rec => `
                <div class="regional-rec-item">
                    <div class="regional-rec-header">
                        <span class="regional-rec-urgencia urgencia-${esc(rec.urgencia)}">${esc(rec.urgencia)}</span>
                        <span class="regional-rec-problema">${esc(rec.problema)}</span>
                    </div>
                    <div class="regional-rec-treatment">${esc(rec.tratamiento)}</div>
                    ${rec.contexto_regional ? `<div class="regional-rec-context">${esc(rec.contexto_regional)}</div>` : ''}
                    ${rec.costo_estimado_mxn ? `<div class="regional-rec-cost">$${rec.costo_estimado_mxn.toLocaleString()} MXN/ha</div>` : ''}
                </div>
            `).join('')}
        </div>`;
    }

    el.innerHTML = `
        <div class="regional-grid">
            <div class="regional-item">
                <span class="regional-label">Clima</span>
                <span class="regional-value">${esc(climaLabels[r.climate_zone] || r.climate_zone)}</span>
            </div>
            <div class="regional-item">
                <span class="regional-label">Suelo</span>
                <span class="regional-value">${esc(r.soil_type)}</span>
            </div>
            <div class="regional-item">
                <span class="regional-label">Temporada</span>
                <span class="regional-value">${esc(r.growing_season)}</span>
            </div>
            <div class="regional-item">
                <span class="regional-label">Cultivos clave</span>
                <span class="regional-value">${r.key_crops.map(c => esc(c)).join(', ')}</span>
            </div>
        </div>
        ${r.seasonal_notes ? `<div class="regional-notes">${esc(r.seasonal_notes)}</div>` : ''}
        ${recsHtml}`;
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

function renderHealthHistory(list) {
    // Health drill-down records below the chart
    const section = document.getElementById('section-health');
    if (!section || !list || list.length === 0) return;

    // Create a container for records below the chart
    let container = document.getElementById('health-drilldown');
    if (!container) {
        container = document.createElement('div');
        container.id = 'health-drilldown';
        section.appendChild(container);
    }

    const records = [...list].reverse(); // newest first
    let html = '<div class="sensor-history-label">Detalle por evaluacion</div>';
    html += '<div class="sensor-timeline">';
    html += records.map(h => {
        const date = h.scored_at
            ? new Date(h.scored_at).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' })
            : '--';
        const cls = healthClass(h.score);
        const trendLabel = h.trend === 'improving' ? 'Mejorando' : h.trend === 'declining' ? 'Declinando' : 'Estable';
        const trendSymbol = h.trend === 'improving' ? ' &#x25B2;' : h.trend === 'declining' ? ' &#x25BC;' : ' &#x25CF;';

        // Breakdown components
        const bd = h.breakdown || {};
        const bdHtml = Object.keys(bd).length > 0
            ? `<div class="campo-data-grid" style="margin-top:8px">
                ${Object.entries(bd).map(([k, v]) => `
                    <div class="campo-data-item">
                        <span class="campo-data-label">${esc(k.replace(/_/g, ' '))}</span>
                        <span class="campo-data-value">${typeof v === 'number' ? v.toFixed(1) : v}</span>
                    </div>`).join('')}
               </div>`
            : '';

        // Sources
        const srcHtml = h.sources && h.sources.length > 0
            ? `<div style="margin-top:6px"><span class="campo-data-label">Fuentes:</span> <span class="sensor-timeline-summary">${h.sources.join(', ')}</span></div>`
            : '';

        return `<div class="sensor-timeline-item">
            <div class="sensor-timeline-date">${date}</div>
            <div class="sensor-timeline-body">
                <div class="sensor-timeline-header" onclick="this.parentElement.querySelector('.sensor-timeline-detail').classList.toggle('open')">
                    <span class="health-badge ${cls}">${Math.round(h.score)}</span>
                    <span class="sensor-timeline-summary">${trendLabel}${trendSymbol}</span>
                    <span class="sensor-timeline-expand">&#9660;</span>
                </div>
                <div class="sensor-timeline-detail">
                    <div class="campo-data-grid">
                        ${h.ndvi_mean != null ? `<div class="campo-data-item"><span class="campo-data-label">NDVI</span><span class="campo-data-value">${h.ndvi_mean.toFixed(3)}</span></div>` : ''}
                        ${h.stress_pct != null ? `<div class="campo-data-item"><span class="campo-data-label">Estres</span><span class="campo-data-value">${h.stress_pct.toFixed(1)}%</span></div>` : ''}
                        ${h.soil_ph != null ? `<div class="campo-data-item"><span class="campo-data-label">pH Suelo</span><span class="campo-data-value">${h.soil_ph}</span></div>` : ''}
                        ${h.soil_organic_matter_pct != null ? `<div class="campo-data-item"><span class="campo-data-label">Materia Org.</span><span class="campo-data-value">${h.soil_organic_matter_pct}%</span></div>` : ''}
                    </div>
                    ${bdHtml}
                    ${srcHtml}
                </div>
            </div>
        </div>`;
    }).join('');
    html += '</div>';
    container.innerHTML = html;
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

function renderFusion(fusion) {
    const el = document.getElementById('fusion-content');
    if (!fusion) {
        el.innerHTML = '<div class="campo-placeholder">Sin datos de fusion disponibles</div>';
        return;
    }

    const conf = fusion.confidence;
    const confPct = Math.round(conf * 100);
    const confCls = conf >= 0.7 ? 'good' : conf >= 0.4 ? 'warning' : 'critical';

    // Sensor badges
    const sensorLabels = {ndvi: 'NDVI', thermal: 'Termico', soil: 'Suelo', weather: 'Clima'};
    const allSensors = ['ndvi', 'thermal', 'soil', 'weather'];
    const sensorBadgesHtml = allSensors.map(s => {
        const active = fusion.sensors_used.includes(s);
        return `<span class="fusion-sensor-badge ${active ? 'active' : 'inactive'}">${sensorLabels[s]}</span>`;
    }).join('');

    // Contradiction cards
    let contradictionsHtml = '';
    if (fusion.contradictions && fusion.contradictions.length > 0) {
        contradictionsHtml = `<div class="fusion-contradictions">
            <div class="fusion-contradictions-title">Inconsistencias Detectadas</div>
            ${fusion.contradictions.map(c => `
                <div class="fusion-contradiction-card">
                    <div class="fusion-contradiction-header">
                        <span class="fusion-contradiction-sensors">${c.sensors.map(s => sensorLabels[s] || s).join(' vs ')}</span>
                    </div>
                    <div class="fusion-contradiction-desc">${esc(c.description)}</div>
                </div>
            `).join('')}
        </div>`;
    }

    el.innerHTML = `
        <div class="fusion-panel">
            <div class="fusion-confidence-section">
                <div class="fusion-confidence-header">
                    <span class="fusion-confidence-label">Confianza</span>
                    <span class="fusion-confidence-value health-badge ${confCls}">${confPct}%</span>
                </div>
                <div class="fusion-confidence-track">
                    <div class="fusion-confidence-fill ${confCls}" style="width:${confPct}%"></div>
                </div>
                <div class="fusion-sensors">
                    <span class="fusion-sensors-label">${fusion.sensors_used.length}/4 sensores</span>
                    ${sensorBadgesHtml}
                </div>
            </div>
            <div class="fusion-assessment">${esc(fusion.assessment)}</div>
            ${contradictionsHtml}
        </div>`;
}

function renderSeasonalComparison(data) {
    const el = document.getElementById('seasonal-content');
    const yearSelect = document.getElementById('seasonal-year-select');

    if (!data) {
        el.innerHTML = '<div class="campo-placeholder">Sin datos de comparacion estacional</div>';
        yearSelect.style.display = 'none';
        return;
    }

    // Populate year selector if available_years present
    const years = data.available_years || [];
    if (years.length > 1) {
        const currentVal = yearSelect.value;
        yearSelect.innerHTML = '<option value="">Todos los anos</option>' +
            years.map(y => `<option value="${y}"${String(y) === currentVal ? ' selected' : ''}>${y}</option>`).join('');
        yearSelect.style.display = '';
        if (!yearSelect.dataset.bound) {
            yearSelect.dataset.bound = '1';
            yearSelect.addEventListener('change', async () => {
                el.innerHTML = '<div class="campo-placeholder">Cargando...</div>';
                const yearParam = yearSelect.value ? `?year=${yearSelect.value}` : '';
                const base = `/farms/${farmId}/fields/${fieldId}`;
                const newData = await fetchJSON(`${base}/seasonal-comparison${yearParam}`);
                renderSeasonalComparison(newData);
            });
        }
    } else {
        yearSelect.style.display = 'none';
    }

    const temporal = data.temporal || {};
    const secas = data.secas || {};

    // Check if both seasons have no data
    if (temporal.avg_health_score == null && secas.avg_health_score == null) {
        el.innerHTML = '<div class="campo-placeholder">Sin datos suficientes para comparar estaciones</div>';
        return;
    }

    function barPct(val, max) {
        if (val == null) return 0;
        return Math.min(100, Math.round((val / max) * 100));
    }

    function metricRow(label, tVal, sVal, max, unit) {
        const tPct = barPct(tVal, max);
        const sPct = barPct(sVal, max);
        const tDisplay = tVal != null ? tVal + (unit || '') : '--';
        const sDisplay = sVal != null ? sVal + (unit || '') : '--';
        return `
            <div class="seasonal-metric">
                <div class="seasonal-metric-label">${esc(label)}</div>
                <div class="seasonal-bars">
                    <div class="seasonal-bar-row">
                        <span class="seasonal-season-label">Temporal</span>
                        <div class="seasonal-bar-track">
                            <div class="seasonal-bar-fill seasonal-temporal" style="width:${tPct}%"></div>
                        </div>
                        <span class="seasonal-bar-value">${tDisplay}</span>
                    </div>
                    <div class="seasonal-bar-row">
                        <span class="seasonal-season-label">Secas</span>
                        <div class="seasonal-bar-track">
                            <div class="seasonal-bar-fill seasonal-secas" style="width:${sPct}%"></div>
                        </div>
                        <span class="seasonal-bar-value">${sDisplay}</span>
                    </div>
                </div>
            </div>`;
    }

    const maxTreatments = Math.max(temporal.treatment_count || 0, secas.treatment_count || 0, 1);
    const yearLabel = yearSelect.value ? ` (${yearSelect.value})` : ' (Todos)';

    el.innerHTML = `
        <div class="seasonal-card">
            ${metricRow('Salud Promedio', temporal.avg_health_score, secas.avg_health_score, 100, '')}
            ${metricRow('NDVI Promedio', temporal.avg_ndvi, secas.avg_ndvi, 1, '')}
            ${metricRow('Tratamientos', temporal.treatment_count, secas.treatment_count, maxTreatments, '')}
            <div class="seasonal-meta">
                <span class="seasonal-meta-item">Temporal (Jun-Oct): ${temporal.data_points || 0} registros</span>
                <span class="seasonal-meta-item">Secas (Nov-May): ${secas.data_points || 0} registros</span>
            </div>
        </div>`;
}

// -- Mission Plan --
function renderMissionPlan(plan) {
    const el = document.getElementById('mission-content');
    if (!plan) {
        el.innerHTML = '<div class="campo-placeholder">Sin plan de mision disponible</div>';
        return;
    }

    const droneLabels = {
        mavic_multispectral: 'DJI Mavic 3 Multispectral',
        mavic_thermal: 'DJI Mavic 3 Thermal',
        agras_t100: 'DJI Agras T100',
    };
    const missionLabels = {
        health_scan: 'Escaneo de salud',
        thermal_check: 'Revision termica',
        spray: 'Aplicacion de tratamiento',
        emergency_recon: 'Reconocimiento de emergencia',
    };

    const droneName = droneLabels[plan.drone_type] || plan.drone_type;
    const missionName = missionLabels[plan.mission_type] || plan.mission_type;
    const waypointCount = plan.waypoints ? plan.waypoints.length : 0;

    el.innerHTML = `
        <div class="mission-card">
            <div class="mission-header">
                <span class="mission-drone-badge">${esc(droneName)}</span>
                <span class="mission-type-badge">${esc(missionName)}</span>
            </div>
            <div class="campo-data-grid">
                <div class="campo-data-item">
                    <span class="campo-data-label">Duracion estimada</span>
                    <span class="campo-data-value">${plan.estimated_duration_min} min</span>
                </div>
                <div class="campo-data-item">
                    <span class="campo-data-label">Baterias necesarias</span>
                    <span class="campo-data-value">${plan.batteries_needed}</span>
                </div>
                <div class="campo-data-item">
                    <span class="campo-data-label">Altitud</span>
                    <span class="campo-data-value">${plan.altitude_m} m</span>
                </div>
                <div class="campo-data-item">
                    <span class="campo-data-label">Fotos estimadas</span>
                    <span class="campo-data-value">${plan.estimated_photos}</span>
                </div>
                <div class="campo-data-item">
                    <span class="campo-data-label">Distancia total</span>
                    <span class="campo-data-value">${(plan.total_distance_m / 1000).toFixed(1)} km</span>
                </div>
                <div class="campo-data-item">
                    <span class="campo-data-label">Velocidad</span>
                    <span class="campo-data-value">${plan.speed_ms} m/s</span>
                </div>
                <div class="campo-data-item">
                    <span class="campo-data-label">Cobertura</span>
                    <span class="campo-data-value">${plan.area_hectares} ha</span>
                </div>
                <div class="campo-data-item">
                    <span class="campo-data-label">Patron</span>
                    <span class="campo-data-value">${esc(plan.pattern)}</span>
                </div>
            </div>
            <div class="mission-waypoints-summary">
                <span class="campo-data-label">Waypoints: ${waypointCount}</span>
                <span class="campo-data-label">Solapamiento: ${plan.overlap_pct}%</span>
                <span class="campo-data-label">Espaciado: ${plan.line_spacing_m} m</span>
            </div>
        </div>`;
}

// -- Intervention Scores --
function renderInterventionScores(scores) {
    const el = document.getElementById('interventions-content');
    if (!scores || scores.length === 0) {
        el.innerHTML = '<div class="campo-placeholder">Sin intervenciones disponibles</div>';
        return;
    }

    const urgencyCls = (u) => {
        if (u === 'alta') return 'critical';
        if (u === 'media') return 'warning';
        return 'good';
    };

    el.innerHTML = `<div class="intervention-list">
        ${scores.map((s, i) => {
            const scorePct = Math.min(100, Math.round(s.intervention_score * 5));
            const probPct = Math.round(s.success_probability * 100);
            return `<div class="intervention-card">
                <div class="intervention-rank">#${i + 1}</div>
                <div class="intervention-body">
                    <div class="intervention-header">
                        <span class="intervention-problema">${esc(s.problema)}</span>
                        <span class="health-badge ${urgencyCls(s.urgencia)}">${esc(s.urgencia)}</span>
                    </div>
                    <div class="intervention-tratamiento">${esc(s.tratamiento)}</div>
                    <div class="intervention-metrics">
                        <div class="intervention-metric">
                            <span class="intervention-metric-label">Puntaje</span>
                            <div class="intervention-score-bar">
                                <div class="intervention-score-fill" style="width:${scorePct}%"></div>
                            </div>
                            <span class="intervention-metric-value">${s.intervention_score}</span>
                        </div>
                        <div class="intervention-metric">
                            <span class="intervention-metric-label">Probabilidad</span>
                            <span class="intervention-metric-value">${probPct}%</span>
                        </div>
                        <div class="intervention-metric">
                            <span class="intervention-metric-label">Mejora esperada</span>
                            <span class="intervention-metric-value">+${s.expected_health_delta}</span>
                        </div>
                        <div class="intervention-metric">
                            <span class="intervention-metric-label">Costo/ha</span>
                            <span class="intervention-metric-value">$${s.cost_per_hectare.toLocaleString()} MXN</span>
                        </div>
                    </div>
                </div>
            </div>`;
        }).join('')}
    </div>`;
}

// -- Microbiome --
function renderMicrobiome(data) {
    const el = document.getElementById('microbiome-content');
    if (!data || data.length === 0) return;

    const latest = data[0];
    const classMap = {
        healthy: { label: 'Saludable', cls: 'good' },
        moderate: { label: 'Moderado', cls: 'warning' },
        degraded: { label: 'Degradado', cls: 'critical' },
    };
    const info = classMap[latest.classification] || { label: latest.classification, cls: 'none' };

    el.innerHTML = `
        <div class="microbiome-header">
            <span class="health-badge ${info.cls}">${esc(info.label)}</span>
            <span class="microbiome-date">${new Date(latest.sampled_at).toLocaleDateString('es-MX')}</span>
        </div>
        <div class="campo-data-grid">
            <div class="campo-data-item">
                <span class="campo-data-label">Respiracion</span>
                <span class="campo-data-value">${latest.respiration_rate.toFixed(1)} mg CO2/kg/dia</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Carbono Microbiano</span>
                <span class="campo-data-value">${latest.microbial_biomass_carbon.toFixed(0)} mg C/kg</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Ratio Hongos/Bacterias</span>
                <span class="campo-data-value">${latest.fungi_bacteria_ratio.toFixed(2)}</span>
            </div>
        </div>
        ${data.length > 1 ? `
        <div class="microbiome-history">
            <div class="campo-data-label" style="margin-bottom:6px">Historial de muestras (${data.length})</div>
            ${data.slice(0, 5).map(s => {
                const si = classMap[s.classification] || { label: s.classification, cls: 'none' };
                return `<div class="microbiome-sample">
                    <span class="health-badge ${si.cls}" style="font-size:0.65rem;padding:1px 6px">${esc(si.label)}</span>
                    <span class="microbiome-sample-rate">${s.respiration_rate.toFixed(1)}</span>
                    <span class="microbiome-sample-date">${new Date(s.sampled_at).toLocaleDateString('es-MX')}</span>
                </div>`;
            }).join('')}
        </div>` : ''}`;
}

function renderGrowthStage(data) {
    const el = document.getElementById('growth-content');
    if (!data) return;

    const stageLabels = {
        siembra: 'Siembra',
        vegetativo: 'Vegetativo',
        floracion: 'Floracion',
        fructificacion: 'Fructificacion',
        cosecha: 'Cosecha',
    };
    const stageOrder = ['siembra', 'vegetativo', 'floracion', 'fructificacion', 'cosecha'];
    const stageIdx = stageOrder.indexOf(data.stage);
    const progressPct = stageIdx >= 0 ? Math.round(((stageIdx + 1) / stageOrder.length) * 100) : 0;

    const stageCls = stageIdx <= 0 ? 'warning' : stageIdx >= 4 ? 'good' : 'none';

    el.innerHTML = `
        <div class="growth-stage-header">
            <span class="health-badge ${stageCls}">${esc(data.stage_es)}</span>
            <span class="growth-crop">${esc(data.crop_type)}</span>
        </div>
        <div class="growth-progress">
            <div class="growth-progress-track">
                <div class="growth-progress-fill" style="width:${progressPct}%"></div>
            </div>
            <div class="growth-progress-labels">
                ${stageOrder.map((s, i) => `<span class="growth-stage-dot ${i <= stageIdx ? 'active' : ''}">${stageLabels[s]}</span>`).join('')}
            </div>
        </div>
        <div class="campo-data-grid">
            <div class="campo-data-item">
                <span class="campo-data-label">Dias desde siembra</span>
                <span class="campo-data-value">${data.days_since_planting}</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Dias en etapa</span>
                <span class="campo-data-value">${data.days_in_stage}</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Siguiente etapa</span>
                <span class="campo-data-value">${data.days_until_next_stage != null ? data.days_until_next_stage + ' dias' : 'Ultima etapa'}</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Multiplicador de riego</span>
                <span class="campo-data-value">${data.water_multiplier}x</span>
            </div>
        </div>
        <div class="growth-nutrient-focus">
            <span class="campo-data-label">Enfoque nutricional:</span> ${esc(data.nutrient_focus)}
        </div>`;
}

// -- Feedback --

function renderFeedback(feedbackList, treatments) {
    // Populate treatment dropdown
    const sel = document.getElementById('feedback-treatment');
    if (sel && treatments && treatments.length > 0) {
        treatments.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.id;
            opt.textContent = esc(t.tratamiento ? t.tratamiento.substring(0, 60) : `Tratamiento #${t.id}`);
            sel.appendChild(opt);
        });
    }

    const el = document.getElementById('feedback-content');
    if (!feedbackList || feedbackList.length === 0) {
        el.innerHTML = '<div class="campo-placeholder">Sin retroalimentacion</div>';
        return;
    }

    el.innerHTML = feedbackList.map(fb => {
        const stars = '★'.repeat(fb.rating) + '☆'.repeat(5 - fb.rating);
        const workedCls = fb.worked ? 'good' : 'critical';
        const workedLabel = fb.worked ? 'Funciono' : 'No funciono';
        const date = fb.created_at ? new Date(fb.created_at).toLocaleDateString('es-MX') : '';
        return `<div class="feedback-entry">
            <div class="feedback-entry-header">
                <span class="feedback-stars">${stars}</span>
                <span class="health-badge ${workedCls}">${workedLabel}</span>
                <span class="feedback-date">${date}</span>
            </div>
            ${fb.farmer_notes ? `<div class="feedback-notes">${esc(fb.farmer_notes)}</div>` : ''}
            ${fb.alternative_method ? `<div class="feedback-alt">Metodo alternativo: ${esc(fb.alternative_method)}</div>` : ''}
        </div>`;
    }).join('');
}

async function submitFeedback(e) {
    e.preventDefault();
    const treatmentId = document.getElementById('feedback-treatment').value;
    const rating = parseInt(document.getElementById('feedback-rating').value);
    const worked = document.getElementById('feedback-worked').checked;
    const notes = document.getElementById('feedback-notes').value || null;
    const alt = document.getElementById('feedback-alt').value || null;

    if (!treatmentId || !rating || rating < 1 || rating > 5) return;

    const base = `/farms/${farmId}/fields/${fieldId}/feedback`;
    try {
        const resp = await fetch(API + base, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                treatment_id: parseInt(treatmentId),
                rating: rating,
                worked: worked,
                farmer_notes: notes,
                alternative_method: alt,
            }),
        });
        if (resp.ok) {
            document.getElementById('feedback-form').reset();
            const updated = await fetchJSON(`/farms/${farmId}/fields/${fieldId}/feedback`);
            renderFeedback(updated, null);
        }
    } catch { /* silent */ }
}

// -- Flight Log History --
function renderFlights(flights, stats) {
    const statsEl = document.getElementById('flights-stats');
    const contentEl = document.getElementById('flights-content');

    // Render stats summary
    if (stats && stats.total_flights > 0) {
        const droneLabels = {
            'mavic_multispectral': 'Mavic 3 Multispectral',
            'mavic_thermal': 'Mavic 3 Thermal',
            'agras_t100': 'Agras T100',
        };
        const breakdownHtml = stats.drone_breakdown
            ? Object.entries(stats.drone_breakdown).map(([drone, count]) =>
                `<span class="flight-drone-chip">${esc(droneLabels[drone] || drone)}: ${count}</span>`
            ).join(' ')
            : '';
        statsEl.innerHTML = `
            <div class="campo-data-grid">
                <div class="campo-data-item">
                    <span class="campo-data-label">Total Vuelos</span>
                    <span class="campo-data-value">${stats.total_flights}</span>
                </div>
                <div class="campo-data-item">
                    <span class="campo-data-label">Horas de Vuelo</span>
                    <span class="campo-data-value">${stats.total_hours.toFixed(1)} h</span>
                </div>
                <div class="campo-data-item">
                    <span class="campo-data-label">Cobertura Total</span>
                    <span class="campo-data-value">${stats.total_area_covered_ha.toFixed(1)} ha</span>
                </div>
            </div>
            ${breakdownHtml ? `<div class="flight-drone-breakdown">${breakdownHtml}</div>` : ''}`;
    } else {
        statsEl.innerHTML = '';
    }

    // Render flight list
    if (!flights || flights.length === 0) {
        contentEl.innerHTML = '<div class="campo-placeholder">Sin vuelos registrados</div>';
        return;
    }

    const missionLabels = {
        'health_scan': 'Escaneo de salud',
        'thermal_check': 'Revision termica',
        'spray': 'Aplicacion',
    };
    const droneLabels = {
        'mavic_multispectral': 'Mavic 3 Multispectral',
        'mavic_thermal': 'Mavic 3 Thermal',
        'agras_t100': 'Agras T100',
    };
    const statusLabels = {
        'pending': 'Pendiente',
        'processing': 'Procesando',
        'complete': 'Completo',
        'failed': 'Fallido',
    };
    const statusCls = {
        'complete': 'good',
        'processing': 'warning',
        'failed': 'critical',
        'pending': 'none',
    };

    contentEl.innerHTML = `<div class="flight-log-list">
        ${flights.map(f => {
            const date = f.flight_date
                ? new Date(f.flight_date).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' })
                : '--';
            const sCls = statusCls[f.status] || 'none';
            return `<div class="flight-log-item">
                <div class="flight-log-date">${date}</div>
                <div class="flight-log-body">
                    <div class="flight-log-header">
                        <strong>${esc(droneLabels[f.drone_type] || f.drone_type)}</strong>
                        <span class="flight-mission-badge">${esc(missionLabels[f.mission_type] || f.mission_type)}</span>
                        <span class="health-badge ${sCls}">${esc(statusLabels[f.status] || f.status)}</span>
                    </div>
                    <div class="flight-log-details">
                        <span>${f.duration_minutes} min</span>
                        <span>${f.altitude_m} m alt</span>
                        <span>${f.images_count} fotos</span>
                        <span>${f.coverage_pct}% cobertura</span>
                    </div>
                </div>
            </div>`;
        }).join('')}
    </div>`;
}

// -- PDF Download --
async function downloadReport() {
    if (!farmId) return;
    const btn = document.getElementById('btn-download-report');
    btn.textContent = 'Generando...';
    btn.disabled = true;
    try {
        const resp = await fetch(API + `/farms/${farmId}/report`, { method: 'POST' });
        if (!resp.ok) throw new Error('Error generando reporte');
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `reporte_granja_${farmId}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    } catch (err) {
        alert('No se pudo generar el reporte. Intente de nuevo.');
    } finally {
        btn.textContent = 'Descargar Reporte';
        btn.disabled = false;
    }
}

// -- Anomaly Detection --
function renderAnomalies(data) {
    const el = document.getElementById('anomalies-content');
    if (!data || ((!data.health_anomalies || data.health_anomalies.length === 0) &&
                  (!data.ndvi_anomalies || data.ndvi_anomalies.length === 0))) {
        el.innerHTML = '<div class="campo-placeholder">Sin anomalias detectadas</div>';
        return;
    }

    const all = [];

    if (data.health_anomalies) {
        data.health_anomalies.forEach(a => {
            all.push(`<div class="anomaly-card anomaly-health">
                <div class="anomaly-card-header">
                    <span class="campo-alert-badge critical">Salud</span>
                    <span class="anomaly-type">${esc(a.type === 'health_drop' ? 'Caida de Salud' : a.type)}</span>
                </div>
                <div class="anomaly-card-detail">
                    <span class="anomaly-metric">${a.previous_score} → ${a.current_score}</span>
                    <span class="anomaly-drop">-${a.drop} pts</span>
                </div>
                <div class="anomaly-card-rec">${esc(a.recommendation)}</div>
            </div>`);
        });
    }

    if (data.ndvi_anomalies) {
        data.ndvi_anomalies.forEach(a => {
            all.push(`<div class="anomaly-card anomaly-ndvi">
                <div class="anomaly-card-header">
                    <span class="campo-alert-badge warning">NDVI</span>
                    <span class="anomaly-type">${esc(a.type === 'ndvi_drop' ? 'Caida de NDVI' : a.type)}</span>
                </div>
                <div class="anomaly-card-detail">
                    <span class="anomaly-metric">${a.historical_avg.toFixed(2)} → ${a.current_ndvi.toFixed(2)}</span>
                    <span class="anomaly-drop">-${a.drop_pct}%</span>
                </div>
                <div class="anomaly-card-rec">${esc(a.recommendation)}</div>
            </div>`);
        });
    }

    el.innerHTML = all.join('');
}

function renderDataCompleteness(data, currentFieldId) {
    const el = document.getElementById('completeness-content');
    if (!data || !data.fields || data.fields.length === 0) {
        el.innerHTML = '<div class="campo-placeholder">Sin datos de completitud</div>';
        return;
    }

    const fieldData = data.fields.find(f => f.field_id === currentFieldId);
    if (!fieldData) {
        el.innerHTML = '<div class="campo-placeholder">Sin datos de completitud para este campo</div>';
        return;
    }

    const sensors = [
        { key: 'has_soil', label: 'Suelo', present: fieldData.has_soil },
        { key: 'has_ndvi', label: 'NDVI', present: fieldData.has_ndvi },
        { key: 'has_thermal', label: 'Termico', present: fieldData.has_thermal },
        { key: 'has_treatments', label: 'Tratamientos', present: fieldData.has_treatments },
        { key: 'has_weather', label: 'Clima', present: fieldData.has_weather },
    ];

    const scoreCls = fieldData.score >= 80 ? 'good' : fieldData.score >= 40 ? 'warning' : 'critical';

    el.innerHTML = `
        <div class="completeness-header">
            <span class="completeness-score completeness-${scoreCls}">${fieldData.score}%</span>
            <span class="completeness-label">datos disponibles</span>
        </div>
        <div class="completeness-sensors">
            ${sensors.map(s => `
                <div class="completeness-sensor ${s.present ? 'completeness-present' : 'completeness-missing'}">
                    <span class="completeness-dot"></span>
                    <span class="completeness-sensor-label">${s.label}</span>
                </div>
            `).join('')}
        </div>`;
}

// -- Init --
loadFieldDetail();
