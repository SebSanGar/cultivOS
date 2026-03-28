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
           anomaliesData, completenessData, regionalData, carbonData, weatherRecords,
           seasonalAlertsData, seasonalPerfData] = await Promise.all([
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
        fetchJSON(`${base}/carbon`),
        fetchJSON(`/farms/${farmId}/weather`),
        fetchJSON(`/farms/${farmId}/seasonal-alerts`),
        fetchJSON(`${base}/seasonal`),
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

    // Field boundary map
    renderFieldMap(field);

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
    renderNdviChart(ndviList);
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

    // Treatment timing — needs pending treatments + weather forecast
    const pendingTreatments = treatments ? treatments.filter(t => !t.applied_at) : [];
    const latestWeather = weatherRecords && weatherRecords.length > 0 ? weatherRecords[0] : null;
    if (pendingTreatments.length > 0) {
        loadTreatmentTiming(pendingTreatments, latestWeather);
    }

    // Yield
    if (yieldPred) renderYield(yieldPred);

    // Treatments
    if (treatments && treatments.length > 0) renderTreatments(treatments);

    // Rotation
    if (rotation && rotation.plan && rotation.plan.length) renderRotation(rotation);

    // Regional context
    renderRegionalCard(regionalData, parseInt(fieldId));

    // Seasonal risk alerts
    renderSeasonalAlerts(seasonalAlertsData);

    // Action timeline
    renderActionTimeline(actionTimeline);

    // Regenerative score
    renderRegenerativeScore(regenScore);

    // Soil carbon
    renderCarbon(carbonData);

    // Seasonal comparison
    renderSeasonalComparison(seasonalData);

    // Seasonal performance chart (year-over-year)
    renderSeasonalPerformance(seasonalPerfData);

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

    // Weather forecast card
    renderWeatherCard(weatherRecords);

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

function renderNdviChart(list) {
    const canvas = document.getElementById('ndvi-chart');
    if (!canvas) return;
    if (!list || list.length < 2) {
        canvas.parentElement.style.display = 'none';
        return;
    }
    // Sort chronologically
    const sorted = [...list].sort((a, b) => new Date(a.analyzed_at) - new Date(b.analyzed_at));
    const labels = sorted.map(r => {
        const d = new Date(r.analyzed_at);
        return d.toLocaleDateString('es-MX', { day: 'numeric', month: 'short' });
    });
    const ndviData = sorted.map(r => r.ndvi_mean);
    const stressData = sorted.map(r => r.stress_pct);

    new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'NDVI Promedio',
                    data: ndviData,
                    borderColor: '#16a34a',
                    backgroundColor: 'rgba(22, 163, 74, 0.15)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4,
                    pointBackgroundColor: '#16a34a',
                    yAxisID: 'y',
                },
                {
                    label: 'Estres %',
                    data: stressData,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.08)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 3,
                    pointBackgroundColor: '#ef4444',
                    borderDash: [5, 3],
                    yAxisID: 'y1',
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            scales: {
                y: {
                    min: 0,
                    max: 1,
                    ticks: { stepSize: 0.2 },
                    title: { display: true, text: 'NDVI' },
                },
                y1: {
                    min: 0,
                    max: 100,
                    position: 'right',
                    ticks: { stepSize: 20, callback: v => v + '%' },
                    title: { display: true, text: 'Estres' },
                    grid: { drawOnChartArea: false },
                },
            },
            plugins: {
                legend: { display: true, position: 'bottom' },
            },
        },
    });
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

// -- Soil Entry Form --
function initSoilForm() {
    const form = document.getElementById('soil-entry-form');
    if (!form) return;
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        const btn = document.getElementById('soil-submit-btn');
        const msg = document.getElementById('soil-form-msg');
        btn.disabled = true;
        btn.textContent = 'Guardando...';
        msg.textContent = '';
        msg.className = 'soil-form-msg';

        const payload = { sampled_at: document.getElementById('soil-sampled-at').value };
        if (!payload.sampled_at) {
            msg.textContent = 'Fecha de muestreo es requerida';
            msg.classList.add('error');
            btn.disabled = false;
            btn.textContent = 'Guardar Analisis';
            return;
        }

        const numFields = [
            ['soil-ph', 'ph'], ['soil-organic-matter', 'organic_matter_pct'],
            ['soil-nitrogen', 'nitrogen_ppm'], ['soil-phosphorus', 'phosphorus_ppm'],
            ['soil-potassium', 'potassium_ppm'], ['soil-moisture', 'moisture_pct'],
            ['soil-ec', 'electrical_conductivity'], ['soil-depth', 'depth_cm'],
        ];
        for (const [elId, key] of numFields) {
            const val = document.getElementById(elId).value;
            if (val !== '') payload[key] = parseFloat(val);
        }
        const texture = document.getElementById('soil-texture').value;
        if (texture) payload.texture = texture;
        const notes = document.getElementById('soil-notes').value;
        if (notes) payload.notes = notes;

        try {
            const resp = await fetch(`${API}/farms/${farmId}/fields/${fieldId}/soil`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (resp.ok) {
                msg.textContent = 'Analisis guardado';
                msg.classList.add('success');
                form.reset();
                // Refresh soil history
                const soilList = await fetchJSON(`/farms/${farmId}/fields/${fieldId}/soil`);
                renderSoilHistory(soilList);
                const latestSoil = soilList && soilList.length > 0 ? soilList[soilList.length - 1] : null;
                if (latestSoil) renderSoil(latestSoil);
            } else {
                const err = await resp.json().catch(() => null);
                msg.textContent = err && err.detail ? (typeof err.detail === 'string' ? err.detail : 'Error de validacion') : 'Error al guardar';
                msg.classList.add('error');
            }
        } catch {
            msg.textContent = 'Error de conexion';
            msg.classList.add('error');
        }
        btn.disabled = false;
        btn.textContent = 'Guardar Analisis';
    });
}

initSoilForm();

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
    document.getElementById('treatments-content').innerHTML = treatments.map(t => {
        const isApplied = !!t.applied_at;
        const appliedDate = isApplied ? new Date(t.applied_at).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' }) : '';
        return `
        <div class="campo-treatment-card ${isApplied ? 'treatment-applied' : ''}">
            ${isApplied ? `<div class="treatment-applied-badge">Aplicado ${appliedDate}</div>` : ''}
            ${t.problema ? `<div class="campo-treatment-row"><strong>Problema:</strong> ${esc(t.problema)}</div>` : ''}
            ${t.tratamiento ? `<div class="campo-treatment-row"><strong>Tratamiento:</strong> ${esc(t.tratamiento)}</div>` : ''}
            ${t.costo_estimado_mxn ? `<div class="campo-treatment-row"><strong>Costo:</strong> $${t.costo_estimado_mxn.toLocaleString()} MXN/ha</div>` : ''}
            ${t.urgencia ? `<div class="campo-treatment-row"><span class="campo-alert-badge ${t.urgencia.toLowerCase() === 'inmediata' ? 'critical' : 'warning'}">${esc(t.urgencia)}</span></div>` : ''}
            ${t.prevencion ? `<div class="campo-treatment-row"><strong>Prevencion:</strong> ${esc(t.prevencion)}</div>` : ''}
            ${isApplied ? `
                ${t.applied_notes ? `<div class="campo-treatment-row treatment-notes"><strong>Notas:</strong> ${esc(t.applied_notes)}</div>` : ''}
            ` : `
                <div class="treatment-apply-section" id="apply-section-${t.id}">
                    <button class="treatment-apply-btn" onclick="toggleApplyForm(${t.id})">Marcar como aplicado</button>
                    <div class="treatment-apply-form" id="apply-form-${t.id}" style="display:none">
                        <label>Fecha de aplicacion:
                            <input type="date" id="apply-date-${t.id}" value="${new Date().toISOString().split('T')[0]}">
                        </label>
                        <label>Notas (opcional):
                            <textarea id="apply-notes-${t.id}" rows="2" placeholder="Observaciones de campo..."></textarea>
                        </label>
                        <div class="treatment-apply-actions">
                            <button class="treatment-confirm-btn" onclick="markTreatmentApplied(${t.id})">Confirmar</button>
                            <button class="treatment-cancel-btn" onclick="toggleApplyForm(${t.id})">Cancelar</button>
                        </div>
                    </div>
                </div>
            `}
        </div>`;
    }).join('');
}

function toggleApplyForm(treatmentId) {
    const form = document.getElementById(`apply-form-${treatmentId}`);
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
}

async function markTreatmentApplied(treatmentId) {
    const dateVal = document.getElementById(`apply-date-${treatmentId}`).value;
    const notes = document.getElementById(`apply-notes-${treatmentId}`).value.trim();
    if (!dateVal) return;

    const btn = document.querySelector(`#apply-section-${treatmentId} .treatment-confirm-btn`);
    if (btn) { btn.disabled = true; btn.textContent = 'Guardando...'; }

    try {
        const resp = await fetch(`${API}/farms/${farmId}/fields/${fieldId}/treatments/${treatmentId}/applied`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ applied_at: new Date(dateVal).toISOString(), notes: notes || null }),
        });
        if (!resp.ok) throw new Error('Error al marcar tratamiento');
        // Refresh treatments list
        const treatments = await fetchJSON(`/farms/${farmId}/fields/${fieldId}/treatments`);
        if (treatments) renderTreatments(treatments);
        // Refresh treatment history
        const history = await fetchJSON(`/farms/${farmId}/fields/${fieldId}/treatments/treatment-history`);
        renderTreatmentHistory(history);
    } catch (e) {
        if (btn) { btn.disabled = false; btn.textContent = 'Confirmar'; }
        alert('Error al registrar la aplicacion del tratamiento');
    }
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
        <div class="rotation-current">
            <span class="rotation-label">Cultivo actual:</span>
            <span class="rotation-value">${esc(rotation.last_crop)}</span>
        </div>
        <div class="rotation-timeline">
            ${rotation.plan.map((s, i) => `
                <div class="rotation-season">
                    <div class="rotation-num">${i + 1}</div>
                    <div>
                        <div class="rotation-crop">${esc(s.crop)}</div>
                        <div class="rotation-purpose">${esc(s.purpose)}</div>
                        <div class="rotation-meta">
                            <span class="rotation-months">${esc(s.months)}</span>
                            <span class="rotation-season-label">${esc(s.season)}</span>
                        </div>
                        <div class="rotation-reason">${esc(s.reason)}</div>
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

function renderCarbon(data) {
    const el = document.getElementById('carbon-content');
    if (!data || !data.soc_actual) {
        el.innerHTML = `<div class="campo-placeholder">${data && data.resumen ? esc(data.resumen) : 'Sin datos de carbono del suelo'}</div>`;
        return;
    }

    const soc = data.soc_actual;
    const tendencia = data.tendencia;
    const co2e = (soc.soc_tonnes_per_ha * 3.67).toFixed(1);

    const trendIcons = { ganando: '+', estable: '=', perdiendo: '-', datos_insuficientes: '?' };
    const trendLabels = { ganando: 'Ganando carbono', estable: 'Estable', perdiendo: 'Perdiendo carbono', datos_insuficientes: 'Datos insuficientes' };
    const trendCls = tendencia === 'ganando' ? 'good' : tendencia === 'estable' ? 'warning' : tendencia === 'perdiendo' ? 'critical' : '';

    const classCls = soc.clasificacion === 'alto' ? 'good' : soc.clasificacion === 'adecuado' ? 'warning' : 'critical';
    const classLabels = { bajo: 'Bajo', adecuado: 'Adecuado', alto: 'Alto' };

    const cambioHtml = data.cambio_soc_tonnes_per_ha !== 0
        ? `<div class="campo-data-row">
               <span class="campo-data-label">Cambio SOC</span>
               <span class="campo-data-value">${data.cambio_soc_tonnes_per_ha > 0 ? '+' : ''}${data.cambio_soc_tonnes_per_ha.toFixed(2)} t/ha</span>
           </div>`
        : '';

    const recsHtml = data.recomendaciones && data.recomendaciones.length > 0
        ? `<div class="carbon-recs">
               ${data.recomendaciones.map(r => `<div class="carbon-rec-item">${esc(r)}</div>`).join('')}
           </div>`
        : '';

    el.innerHTML = `
        <div class="carbon-card">
            <div class="carbon-hero">
                <div class="carbon-soc-value">${soc.soc_tonnes_per_ha.toFixed(1)}</div>
                <div class="carbon-soc-unit">t SOC/ha</div>
                <div class="health-badge ${classCls}" style="margin-top:4px">${classLabels[soc.clasificacion] || soc.clasificacion}</div>
            </div>
            <div class="carbon-details">
                <div class="campo-data-row">
                    <span class="campo-data-label">CO2 equivalente</span>
                    <span class="campo-data-value">${co2e} t CO2e/ha</span>
                </div>
                <div class="campo-data-row">
                    <span class="campo-data-label">Materia organica</span>
                    <span class="campo-data-value">${soc.organic_matter_pct.toFixed(1)}%</span>
                </div>
                <div class="campo-data-row">
                    <span class="campo-data-label">Profundidad</span>
                    <span class="campo-data-value">${soc.depth_cm} cm</span>
                </div>
                <div class="campo-data-row">
                    <span class="campo-data-label">Tendencia</span>
                    <span class="campo-data-value carbon-trend-${trendCls}">${trendIcons[tendencia]} ${trendLabels[tendencia]}</span>
                </div>
                ${cambioHtml}
                <div class="campo-data-row">
                    <span class="campo-data-label">Registros</span>
                    <span class="campo-data-value">${data.registros}</span>
                </div>
            </div>
            ${recsHtml}
            <div class="carbon-summary">${esc(data.resumen)}</div>
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

    // Treatment count + next action
    const treats = intel.treatments || [];
    const treatCount = treats.length;
    const urgencyOrder = {alta: 0, media: 1, baja: 2};
    const nextAction = treats.length > 0
        ? treats.slice().sort((a, b) => (urgencyOrder[a.urgencia] ?? 3) - (urgencyOrder[b.urgencia] ?? 3))[0]
        : null;

    // Yield estimate
    const yld = intel.yield_prediction;

    // Sensor confidence (fusion)
    const fusion = intel.fusion;
    const confPct = fusion ? Math.round(fusion.confidence * 100) : null;
    const confCls = fusion ? (fusion.confidence >= 0.7 ? 'good' : fusion.confidence >= 0.4 ? 'warning' : 'critical') : '';

    // Top risk — derive from disease risk or health trend
    let topRisk = null;
    if (dr && dr.risk_level !== 'bajo') {
        topRisk = dr.mensaje || `Riesgo de enfermedad: ${dr.risk_level}`;
    } else if (h && h.trend === 'declining') {
        topRisk = 'Salud en declive — revisar condiciones del campo';
    } else if (ndvi && ndvi.stress_pct > 30) {
        topRisk = `${ndvi.stress_pct.toFixed(0)}% del campo bajo estres vegetativo`;
    }

    el.innerHTML = `
        <div class="cerebro-grid">
            <div class="cerebro-hero">
                <div class="cerebro-score-wrap">
                    <div class="cerebro-score health-badge ${healthCls}">${h ? Math.round(h.score) : '--'}</div>
                    <div class="cerebro-score-label">Salud <span class="${trendCls}">${trendArrow}</span></div>
                </div>
                ${confPct != null ? `<div class="cerebro-confidence"><span class="health-badge ${confCls}">${confPct}%</span> <span class="cerebro-conf-label">Confianza</span></div>` : ''}
            </div>
            <div class="cerebro-badges">
                ${ndvi ? `<div class="cerebro-badge"><span class="cerebro-badge-label">NDVI</span><span class="health-badge ${ndviCls}">${ndvi.ndvi_mean.toFixed(2)} — ${ndviStatus}</span></div>` : ''}
                ${soil ? `<div class="cerebro-badge"><span class="cerebro-badge-label">pH</span><span class="campo-data-value">${soil.ph}</span></div>` : ''}
                ${soil && soil.organic_matter_pct != null ? `<div class="cerebro-badge"><span class="cerebro-badge-label">Materia Org.</span><span class="campo-data-value">${soil.organic_matter_pct}%</span></div>` : ''}
                ${weather ? `<div class="cerebro-badge"><span class="cerebro-badge-label">Clima</span><span class="campo-data-value">${Math.round(weather.temp_c)}C &middot; ${Math.round(weather.humidity_pct)}% hum</span></div>` : ''}
                ${gs ? `<div class="cerebro-badge"><span class="cerebro-badge-label">Etapa</span><span class="campo-data-value">${esc(gs.stage_es)}</span></div>` : ''}
                ${dr ? `<div class="cerebro-badge"><span class="cerebro-badge-label">Riesgo</span><span class="health-badge ${drCls}">${esc(dr.risk_level)}</span></div>` : ''}
                ${yld ? `<div class="cerebro-badge"><span class="cerebro-badge-label">Rendimiento</span><span class="campo-data-value">${Math.round(yld.kg_per_ha).toLocaleString()} kg/ha</span></div>` : ''}
                ${treatCount > 0 ? `<div class="cerebro-badge"><span class="cerebro-badge-label">Tratamientos</span><span class="campo-data-value">${treatCount} activos</span></div>` : ''}
            </div>
        </div>
        <div class="cerebro-insights">
            ${topRisk ? `<div class="cerebro-insight-item cerebro-risk"><span class="cerebro-insight-label">Riesgo Principal</span><span class="cerebro-insight-text">${esc(topRisk)}</span></div>` : ''}
            ${nextAction ? `<div class="cerebro-insight-item cerebro-action"><span class="cerebro-insight-label">Accion Recomendada</span><span class="cerebro-insight-text">${esc(nextAction.tratamiento)} — ${esc(nextAction.problema)} <span class="health-badge ${nextAction.urgencia === 'alta' ? 'critical' : nextAction.urgencia === 'media' ? 'warning' : 'good'}">${esc(nextAction.urgencia)}</span></span></div>` : ''}
            ${yld ? `<div class="cerebro-insight-item"><span class="cerebro-insight-label">Estimacion de Rendimiento</span><span class="cerebro-insight-text">${Math.round(yld.min_kg_per_ha).toLocaleString()} — ${Math.round(yld.max_kg_per_ha).toLocaleString()} kg/ha (${esc(yld.nota)})</span></div>` : ''}
            ${!topRisk && !nextAction && !yld ? '<div class="campo-placeholder">Sin datos de inteligencia avanzada disponibles</div>' : ''}
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

// -- Seasonal Performance Chart (year-over-year grouped bar) --
let seasonalPerfChartInstance = null;

function renderSeasonalPerformance(data) {
    const el = document.getElementById('seasonal-perf-content');
    const canvas = document.getElementById('seasonal-perf-chart');

    if (!data || !data.seasons || data.seasons.length === 0) {
        el.innerHTML = '<div class="campo-placeholder">Sin datos de rendimiento estacional</div>';
        canvas.style.display = 'none';
        return;
    }

    el.innerHTML = '';
    canvas.style.display = '';

    // Group by year, each year has temporal + secas
    const years = [...new Set(data.seasons.map(s => s.year))].sort();
    const temporalScores = years.map(y => {
        const entry = data.seasons.find(s => s.year === y && s.season === 'temporal');
        return entry ? entry.avg_score : null;
    });
    const secasScores = years.map(y => {
        const entry = data.seasons.find(s => s.year === y && s.season === 'secas');
        return entry ? entry.avg_score : null;
    });

    if (seasonalPerfChartInstance) {
        seasonalPerfChartInstance.destroy();
    }

    const ctx = canvas.getContext('2d');
    seasonalPerfChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: years.map(String),
            datasets: [
                {
                    label: 'Temporal (Jun-Oct)',
                    data: temporalScores,
                    backgroundColor: 'rgba(0, 200, 150, 0.7)',
                    borderColor: 'rgba(0, 200, 150, 1)',
                    borderWidth: 1,
                },
                {
                    label: 'Secas (Nov-May)',
                    data: secasScores,
                    backgroundColor: 'rgba(240, 180, 41, 0.7)',
                    borderColor: 'rgba(240, 180, 41, 1)',
                    borderWidth: 1,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: { color: '#aaa', font: { size: 11 } },
                },
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            const val = ctx.parsed.y;
                            return val != null ? `${ctx.dataset.label}: ${val.toFixed(1)}` : `${ctx.dataset.label}: --`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    ticks: { color: '#aaa' },
                    grid: { color: 'rgba(255,255,255,0.06)' },
                },
                y: {
                    min: 0,
                    max: 100,
                    ticks: { color: '#aaa' },
                    grid: { color: 'rgba(255,255,255,0.06)' },
                    title: { display: true, text: 'Salud Promedio', color: '#aaa' },
                },
            },
        },
    });
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

    const stageOrder = ['siembra', 'vegetativo', 'floracion', 'fructificacion', 'cosecha'];
    const stageIdx = stageOrder.indexOf(data.stage);
    const stageCls = stageIdx <= 0 ? 'warning' : stageIdx >= 4 ? 'good' : 'none';

    const headerHtml = `
        <div class="growth-stage-header">
            <span class="health-badge ${stageCls}">${esc(data.stage_es)}</span>
            <span class="growth-crop">${esc(data.crop_type)}</span>
            <span class="growth-day-count">Dia ${data.days_since_planting}</span>
        </div>`;

    let timelineHtml = '';
    if (data.all_stages && data.all_stages.length > 0) {
        const totalDays = data.all_stages[data.all_stages.length - 1].end_day;
        const progressPct = totalDays > 0 ? Math.min(100, Math.round((data.days_since_planting / totalDays) * 100)) : 0;

        const segmentsHtml = data.all_stages.map((s, i) => {
            const duration = s.end_day - s.start_day;
            const widthPct = totalDays > 0 ? (duration / totalDays) * 100 : 20;
            const isCurrent = s.is_current;
            const isPast = stageIdx > i;
            const cls = isCurrent ? 'current' : isPast ? 'past' : 'future';
            return `<div class="growth-timeline-segment ${cls}" style="width:${widthPct.toFixed(1)}%" title="${esc(s.name_es)}: ${duration} dias, Riego ${s.water_multiplier}x">
                <span class="growth-timeline-label">${esc(s.name_es)}</span>
                <span class="growth-timeline-days">${duration}d</span>
            </div>`;
        }).join('');

        timelineHtml = `
        <div class="growth-timeline">
            <div class="growth-timeline-bar">${segmentsHtml}</div>
            <div class="growth-timeline-needle" style="left:${progressPct}%"></div>
        </div>`;
    }

    let detailsHtml = '';
    if (data.all_stages && data.all_stages.length > 0) {
        detailsHtml = `<div class="growth-timeline-details">
            ${data.all_stages.map(s => {
                const cls = s.is_current ? 'current' : '';
                const waterCls = s.water_multiplier >= 1.2 ? 'high' : s.water_multiplier <= 0.6 ? 'low' : 'mid';
                return `<div class="growth-timeline-detail ${cls}">
                    <span class="growth-timeline-detail-name">${esc(s.name_es)}</span>
                    <span class="growth-timeline-detail-water ${waterCls}">${s.water_multiplier}x</span>
                    <span class="growth-timeline-detail-nutrient">${esc(s.nutrient_focus)}</span>
                </div>`;
            }).join('')}
        </div>`;
    }

    const summaryHtml = `
        <div class="campo-data-grid">
            <div class="campo-data-item">
                <span class="campo-data-label">Dias en etapa</span>
                <span class="campo-data-value">${data.days_in_stage}</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Siguiente etapa</span>
                <span class="campo-data-value">${data.days_until_next_stage != null ? data.days_until_next_stage + ' dias' : 'Ultima etapa'}</span>
            </div>
            <div class="campo-data-item">
                <span class="campo-data-label">Riego actual</span>
                <span class="campo-data-value">${data.water_multiplier}x</span>
            </div>
        </div>`;

    el.innerHTML = `${headerHtml}${timelineHtml}${detailsHtml}${summaryHtml}`;
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

// ── Treatment Timing ────────────────────────────────────────────────

function classifyTreatmentType(tratamiento) {
    const t = (tratamiento || '').toLowerCase();
    if (t.includes('foliar') || t.includes('aspersi') || t.includes('neem') || t.includes('spray')) {
        return 'foliar_spray';
    }
    if (t.includes('drench') || t.includes('riego') || t.includes('solucion')) {
        return 'soil_drench';
    }
    return 'organic_amendment';
}

const TREATMENT_TYPE_LABELS = {
    organic_amendment: 'Enmienda organica',
    foliar_spray: 'Aplicacion foliar',
    soil_drench: 'Riego al suelo',
};

async function loadTreatmentTiming(pendingTreatments, latestWeather) {
    const forecast = latestWeather && latestWeather.forecast_3day && latestWeather.forecast_3day.length > 0
        ? latestWeather.forecast_3day
        : [];

    // Group treatments by type
    const byType = {};
    for (const t of pendingTreatments) {
        const type = classifyTreatmentType(t.tratamiento);
        if (!byType[type]) byType[type] = [];
        byType[type].push(t);
    }

    // Fetch timing for each unique type
    const types = Object.keys(byType);
    const results = await Promise.all(types.map(type =>
        fetch(API + '/intel/treatment-timing', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                treatment_type: type,
                forecast_3day: forecast.map(d => ({
                    description: d.description || '',
                    temp_c: d.temp_c || 28,
                    humidity_pct: d.humidity_pct || 55,
                    wind_kmh: d.wind_kmh || 8,
                })),
            }),
        }).then(r => r.ok ? r.json() : null).catch(() => null)
    ));

    // Combine type info with timing results
    const timingData = types.map((type, i) => ({
        type,
        label: TREATMENT_TYPE_LABELS[type] || type,
        treatments: byType[type],
        timing: results[i],
    }));

    renderTreatmentTiming(timingData, forecast);
}

function renderTreatmentTiming(timingData, forecast) {
    const el = document.getElementById('treatment-timing-content');
    if (!el) return;

    if (!timingData || timingData.length === 0) {
        el.innerHTML = '<div class="campo-placeholder">Sin tratamientos pendientes</div>';
        return;
    }

    const dayLabels = ['Hoy', 'Manana', 'Pasado manana'];

    // Rain warning from forecast
    const rainyDays = forecast
        .map((d, i) => ({ idx: i, rain: d.rainfall_mm || 0, desc: d.description || '' }))
        .filter(d => d.rain > 0 || d.desc.toLowerCase().includes('lluvia'));

    let rainWarningHtml = '';
    if (rainyDays.length > 0) {
        const rainDayNames = rainyDays.map(d => dayLabels[d.idx] || `Dia ${d.idx + 1}`).join(', ');
        rainWarningHtml = `<div class="timing-rain-warning">Lluvia esperada: ${esc(rainDayNames)}</div>`;
    }

    // Forecast bar
    let forecastHtml = '';
    if (forecast.length > 0) {
        forecastHtml = `<div class="timing-forecast">${forecast.map((d, i) => {
            const hasRain = (d.rainfall_mm || 0) > 0 || (d.description || '').toLowerCase().includes('lluvia');
            return `<div class="timing-forecast-day ${hasRain ? 'timing-rain-day' : ''}">
                <span class="timing-forecast-label">${dayLabels[i] || 'Dia ' + (i + 1)}</span>
                <span class="timing-forecast-temp">${Math.round(d.temp_c)}C</span>
                ${hasRain ? '<span class="timing-forecast-rain">lluvia</span>' : ''}
            </div>`;
        }).join('')}</div>`;
    }

    // Timing cards per type
    const cardsHtml = timingData.map(item => {
        const t = item.timing;
        if (!t) {
            return `<div class="timing-card">
                <div class="timing-card-type">${esc(item.label)}</div>
                <div class="campo-placeholder">Sin pronostico disponible</div>
                <div class="timing-card-treatments">${item.treatments.map(tr =>
                    `<span class="timing-treatment-name">${esc(tr.tratamiento)}</span>`
                ).join('')}</div>
            </div>`;
        }

        const bestDayLabel = dayLabels[t.best_day] || `Dia ${t.best_day + 1}`;
        const avoidHtml = t.avoid_days && t.avoid_days.length > 0
            ? `<div class="timing-avoid">Evitar: ${t.avoid_days.map(d => dayLabels[d] || `Dia ${d + 1}`).join(', ')}</div>`
            : '';

        return `<div class="timing-card">
            <div class="timing-card-type">${esc(item.label)}</div>
            <div class="timing-card-best">
                <span class="timing-best-day">${esc(bestDayLabel)}</span>
                <span class="timing-best-time">${esc(t.best_time)}</span>
            </div>
            <div class="timing-card-reason">${esc(t.reason)}</div>
            ${avoidHtml}
            <div class="timing-card-treatments">${item.treatments.map(tr =>
                `<span class="timing-treatment-name">${esc(tr.tratamiento)}</span>`
            ).join('')}</div>
        </div>`;
    }).join('');

    el.innerHTML = `${rainWarningHtml}${forecastHtml}${cardsHtml}`;
}

// -- Weather Forecast Card --
function renderWeatherCard(weatherRecords) {
    const el = document.getElementById('weather-content');
    if (!el) return;
    if (!weatherRecords || weatherRecords.length === 0) {
        el.innerHTML = '<div class="campo-placeholder">Sin datos de clima</div>';
        return;
    }
    const w = weatherRecords[0];
    const dayLabels = ['Manana', 'Pasado', 'En 3 dias'];

    // Current conditions
    const currentHtml = `
    <div class="weather-current">
        <div class="weather-current-temp">${Math.round(w.temp_c)}°C</div>
        <div class="weather-current-desc">${esc(w.description)}</div>
        <div class="weather-current-details">
            <span class="weather-detail">Humedad: ${Math.round(w.humidity_pct)}%</span>
            <span class="weather-detail">Viento: ${Math.round(w.wind_kmh)} km/h</span>
            ${w.rainfall_mm > 0 ? `<span class="weather-detail weather-rain">Lluvia: ${w.rainfall_mm.toFixed(1)} mm</span>` : ''}
        </div>
    </div>`;

    // 3-day forecast bars
    let forecastHtml = '';
    if (w.forecast_3day && w.forecast_3day.length > 0) {
        const maxTemp = Math.max(...w.forecast_3day.map(d => d.temp_c));
        const minTemp = Math.min(...w.forecast_3day.map(d => d.temp_c));
        const range = maxTemp - minTemp || 1;

        forecastHtml = `<div class="weather-forecast">
            <div class="weather-forecast-title">Pronostico 3 dias</div>
            <div class="weather-forecast-days">${w.forecast_3day.map((d, i) => {
                const barPct = Math.round(((d.temp_c - minTemp) / range) * 60 + 30);
                const hasRain = d.rainfall_mm > 0;
                return `<div class="weather-day ${hasRain ? 'weather-day-rain' : ''}">
                    <span class="weather-day-label">${dayLabels[i] || 'Dia ' + (i + 1)}</span>
                    <div class="weather-day-bar-track">
                        <div class="weather-day-bar" style="width:${barPct}%"></div>
                    </div>
                    <span class="weather-day-temp">${Math.round(d.temp_c)}°C</span>
                    <span class="weather-day-desc">${esc(d.description)}</span>
                    ${hasRain ? `<span class="weather-day-rain-amt">${d.rainfall_mm.toFixed(1)} mm</span>` : ''}
                    <span class="weather-day-humidity">${Math.round(d.humidity_pct)}%</span>
                </div>`;
            }).join('')}</div>
        </div>`;
    }

    el.innerHTML = `${currentHtml}${forecastHtml}`;
}

// -- Field boundary map --
function renderFieldMap(field) {
    const mapEl = document.getElementById('field-map');
    const placeholder = document.getElementById('map-placeholder');
    if (!field || !field.boundary_coordinates || field.boundary_coordinates.length < 3) {
        if (mapEl) mapEl.style.display = 'none';
        if (placeholder) placeholder.style.display = 'block';
        return;
    }

    // Leaflet expects [lat, lng] but boundary_coordinates are [lon, lat]
    const latlngs = field.boundary_coordinates.map(c => [c[1], c[0]]);
    const map = L.map('field-map', { zoomControl: true, attributionControl: false });
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: 'OpenStreetMap'
    }).addTo(map);

    const polygon = L.polygon(latlngs, {
        color: '#00c896',
        weight: 2,
        fillOpacity: 0.15,
        fillColor: '#00c896'
    }).addTo(map);

    map.fitBounds(polygon.getBounds(), { padding: [30, 30] });
}

// -- Seasonal Risk Alerts --
function renderSeasonalAlerts(data) {
    const el = document.getElementById('seasonal-alerts-content');
    if (!data || !data.alerts || data.alerts.length === 0) {
        el.innerHTML = '<div class="campo-placeholder">Sin alertas estacionales</div>';
        return;
    }

    const typeLabels = {
        preparacion: 'Preparacion',
        siembra: 'Siembra',
        cosecha: 'Cosecha',
        mantenimiento: 'Mantenimiento',
    };

    const typeColors = {
        preparacion: 'seasonal-prep',
        siembra: 'seasonal-siembra',
        cosecha: 'seasonal-cosecha',
        mantenimiento: 'seasonal-maint',
    };

    let html = `<div class="seasonal-alerts-header">
        <span class="seasonal-season-badge">${esc(data.season)}</span>
        <span class="seasonal-date">${esc(data.reference_date)}</span>
    </div>`;

    html += '<div class="seasonal-alerts-list">';
    data.alerts.forEach(a => {
        const cls = typeColors[a.alert_type] || 'seasonal-prep';
        const label = typeLabels[a.alert_type] || a.alert_type;
        html += `<div class="seasonal-alert-card ${cls}">
            <div class="seasonal-alert-top">
                <span class="seasonal-alert-crop">${esc(a.crop)}</span>
                <span class="seasonal-alert-type">${esc(label)}</span>
                <span class="seasonal-alert-months">${esc(a.month_range)}</span>
            </div>
            <div class="seasonal-alert-message">${esc(a.message)}</div>
        </div>`;
    });
    html += '</div>';

    el.innerHTML = html;
}

// -- Init --
loadFieldDetail();
