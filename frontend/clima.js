/* ── cultivOS Weather Dashboard — clima.js ── */

let tempChart = null;
let rainChart = null;

// ── Helpers ──
function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

async function fetchJSON(path) {
    try {
        const token = localStorage.getItem('cultivOS_token');
        const headers = {};
        if (token) headers['Authorization'] = 'Bearer ' + token;
        const resp = await fetch(path, { headers });
        if (!resp.ok) return null;
        return await resp.json();
    } catch {
        return null;
    }
}

// ── Load farms dropdown ──
async function loadFarms() {
    const data = await fetchJSON('/api/farms?page_size=100');
    if (!data || !data.farms) return;
    const sel = document.getElementById('clima-farm-select');
    data.farms.forEach(f => {
        const opt = document.createElement('option');
        opt.value = f.id;
        opt.textContent = f.name;
        sel.appendChild(opt);
    });
    if (data.farms.length > 0) {
        sel.value = data.farms[0].id;
        loadWeather();
    }
}

// ── Load weather data ──
async function loadWeather() {
    const farmId = document.getElementById('clima-farm-select').value;
    if (!farmId) return;

    const records = await fetchJSON(`/api/farms/${farmId}/weather`);

    if (!records || records.length === 0) {
        showEmpty();
        return;
    }

    // Latest record = current conditions
    const latest = records[0];
    document.getElementById('clima-temp').textContent = latest.temp_c.toFixed(1);
    document.getElementById('clima-humidity').textContent = latest.humidity_pct.toFixed(0);
    document.getElementById('clima-wind').textContent = latest.wind_kmh.toFixed(1);
    document.getElementById('clima-rain').textContent = latest.rainfall_mm.toFixed(1);

    // Build 7-day forecast from forecast_3day arrays across records
    buildForecast(records);
    buildTempChart(records);
    buildRainChart(records);
    buildHistory(records);
    checkDrought(records);
    loadWeatherAlerts(farmId);
}

function showEmpty() {
    document.getElementById('clima-temp').textContent = '--';
    document.getElementById('clima-humidity').textContent = '--';
    document.getElementById('clima-wind').textContent = '--';
    document.getElementById('clima-rain').textContent = '--';
    document.getElementById('clima-forecast').innerHTML =
        '<div class="intel-empty">Sin datos climaticos para esta granja</div>';
    document.getElementById('clima-history').innerHTML =
        '<div class="intel-empty">Sin registros</div>';
    document.getElementById('clima-drought-alert').style.display = 'none';
    if (tempChart) { tempChart.destroy(); tempChart = null; }
    if (rainChart) { rainChart.destroy(); rainChart = null; }
}

// ── 7-day forecast cards ──
function buildForecast(records) {
    const container = document.getElementById('clima-forecast');
    // Collect up to 7 days from the latest record's forecast + historical records
    const days = [];
    const latest = records[0];

    // Add current day
    const now = new Date(latest.recorded_at);
    days.push({
        label: 'Hoy',
        temp: latest.temp_c,
        rain: latest.rainfall_mm,
        desc: latest.description,
        humidity: latest.humidity_pct,
    });

    // Add forecast days from latest record
    if (latest.forecast_3day && latest.forecast_3day.length > 0) {
        latest.forecast_3day.forEach((fc, i) => {
            const d = new Date(now);
            d.setDate(d.getDate() + i + 1);
            days.push({
                label: d.toLocaleDateString('es-MX', { weekday: 'short', day: 'numeric' }),
                temp: fc.temp_c ?? fc.temp ?? '--',
                rain: fc.rainfall_mm ?? fc.rain ?? 0,
                desc: fc.description ?? fc.desc ?? '',
                humidity: fc.humidity_pct ?? fc.humidity ?? '--',
            });
        });
    }

    // Fill remaining days from older records
    for (let i = 1; i < records.length && days.length < 7; i++) {
        const r = records[i];
        const d = new Date(r.recorded_at);
        days.push({
            label: d.toLocaleDateString('es-MX', { weekday: 'short', day: 'numeric' }),
            temp: r.temp_c,
            rain: r.rainfall_mm,
            desc: r.description,
            humidity: r.humidity_pct,
        });
    }

    container.innerHTML = days.slice(0, 7).map(d => `
        <div style="min-width:130px; background:rgba(255,255,255,0.05); border-radius:12px; padding:1rem; text-align:center; flex-shrink:0;">
            <div style="font-weight:700; color:#60a5fa; margin-bottom:0.5rem;">${esc(d.label)}</div>
            <div style="font-size:1.5rem; font-weight:800; color:#f0f0f0;">${typeof d.temp === 'number' ? d.temp.toFixed(1) : d.temp}&deg;C</div>
            <div style="color:#94a3b8; font-size:0.85rem; margin:0.25rem 0;">${esc(d.desc)}</div>
            <div style="color:#38bdf8; font-size:0.85rem;">${typeof d.rain === 'number' ? d.rain.toFixed(1) : d.rain} mm</div>
            <div style="color:#94a3b8; font-size:0.8rem;">${typeof d.humidity === 'number' ? d.humidity.toFixed(0) : d.humidity}% hum</div>
        </div>
    `).join('');
}

// ── Temperature chart ──
function buildTempChart(records) {
    const ctx = document.getElementById('clima-temp-chart').getContext('2d');
    if (tempChart) tempChart.destroy();

    const recent = records.slice(0, 7).reverse();
    const labels = recent.map(r => {
        const d = new Date(r.recorded_at);
        return d.toLocaleDateString('es-MX', { day: 'numeric', month: 'short' });
    });
    const temps = recent.map(r => r.temp_c);

    tempChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Temperatura (C)',
                data: temps,
                borderColor: '#f59e0b',
                backgroundColor: 'rgba(245,158,11,0.15)',
                fill: true,
                tension: 0.3,
                pointRadius: 5,
                pointBackgroundColor: '#f59e0b',
            }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: '#94a3b8' } },
            },
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
            },
        },
    });
}

// ── Rainfall chart ──
function buildRainChart(records) {
    const ctx = document.getElementById('clima-rain-chart').getContext('2d');
    if (rainChart) rainChart.destroy();

    const recent = records.slice(0, 7).reverse();
    const labels = recent.map(r => {
        const d = new Date(r.recorded_at);
        return d.toLocaleDateString('es-MX', { day: 'numeric', month: 'short' });
    });
    const rain = recent.map(r => r.rainfall_mm);

    rainChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Precipitacion (mm)',
                data: rain,
                backgroundColor: '#3b82f6',
                borderRadius: 6,
            }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: '#94a3b8' } },
            },
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, beginAtZero: true },
            },
        },
    });
}

// ── History table ──
function buildHistory(records) {
    const container = document.getElementById('clima-history');
    if (records.length === 0) {
        container.innerHTML = '<div class="intel-empty">Sin registros</div>';
        return;
    }

    let html = `<table class="intel-table" style="width:100%;">
        <thead><tr>
            <th>Fecha</th><th>Temp (C)</th><th>Humedad (%)</th><th>Viento (km/h)</th><th>Lluvia (mm)</th><th>Condicion</th>
        </tr></thead><tbody>`;

    records.slice(0, 15).forEach(r => {
        const d = new Date(r.recorded_at);
        html += `<tr>
            <td>${d.toLocaleDateString('es-MX', { year: 'numeric', month: 'short', day: 'numeric' })}</td>
            <td>${r.temp_c.toFixed(1)}</td>
            <td>${r.humidity_pct.toFixed(0)}</td>
            <td>${r.wind_kmh.toFixed(1)}</td>
            <td>${r.rainfall_mm.toFixed(1)}</td>
            <td>${esc(r.description)}</td>
        </tr>`;
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

// ── Drought detection ──
function checkDrought(records) {
    const alert = document.getElementById('clima-drought-alert');
    const msg = document.getElementById('clima-drought-msg');

    // Check last 7 records for consecutive zero rainfall
    const recent = records.slice(0, 7);
    const dryDays = recent.filter(r => r.rainfall_mm < 1).length;
    const highTemp = recent.some(r => r.temp_c > 35);

    if (dryDays >= 5) {
        alert.style.display = 'block';
        const severity = dryDays >= 7 ? 'CRITICA' : 'MODERADA';
        msg.textContent = `Alerta de sequia ${severity}: ${dryDays} de los ultimos 7 registros sin lluvia significativa.` +
            (highTemp ? ' Se detectaron temperaturas superiores a 35C — riesgo de estres termico.' : '') +
            ' Se recomienda revisar el plan de riego y priorizar campos con cultivos sensibles.';
    } else {
        alert.style.display = 'none';
    }
}

// ── Weather alerts ──
async function loadWeatherAlerts(farmId) {
    const container = document.getElementById('clima-weather-alerts');
    const body = document.getElementById('clima-alerts-body');
    const data = await fetchJSON(`/api/farms/${farmId}/weather/alerts`);

    if (!data || !data.alerts || data.alerts.length === 0) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'block';

    const severityColors = {
        critica: { border: '#ef4444', bg: 'rgba(239,68,68,0.1)', text: '#fca5a5', badge: '#ef4444' },
        moderada: { border: '#f59e0b', bg: 'rgba(245,158,11,0.1)', text: '#fcd34d', badge: '#f59e0b' },
    };

    body.innerHTML = data.alerts.map(alert => {
        const colors = severityColors[alert.severity] || severityColors.moderada;
        const sourceLabel = alert.source === 'current' ? 'Ahora' : alert.source.replace('forecast_day_', 'Dia ');
        return `
            <div style="border-left:4px solid ${colors.border}; background:${colors.bg}; border-radius:8px; padding:1rem; margin-bottom:0.75rem;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                    <strong style="color:${colors.text}; font-size:1.1rem;">${esc(alert.title)}</strong>
                    <div>
                        <span style="background:${colors.badge}; color:#000; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:700; text-transform:uppercase;">${esc(alert.severity)}</span>
                        <span style="color:#94a3b8; font-size:0.8rem; margin-left:0.5rem;">${esc(sourceLabel)}</span>
                    </div>
                </div>
                <p style="color:#cbd5e1; margin:0.25rem 0 0.75rem;">${esc(alert.message)}</p>
                <div style="color:#94a3b8; font-size:0.85rem;">
                    <strong style="color:#60a5fa;">Acciones recomendadas:</strong>
                    <ul style="margin:0.25rem 0 0; padding-left:1.25rem;">
                        ${alert.actions.map(a => `<li>${esc(a)}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    }).join('');
}

// ── Init ──
document.addEventListener('DOMContentLoaded', loadFarms);
