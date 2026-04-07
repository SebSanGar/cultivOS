/* api-status.js — System health dashboard */

async function loadSystemHealth() {
    const btn = document.getElementById('refresh-btn');
    if (btn) btn.disabled = true;

    try {
        const resp = await fetch('/api/system/health-detailed');
        if (!resp.ok) throw new Error('API error');
        const data = await resp.json();

        // Status
        const statusEl = document.getElementById('system-status');
        if (statusEl) {
            statusEl.textContent = data.status === 'operational' ? 'Operativo' : data.status;
            statusEl.style.color = data.status === 'operational' ? '#22c55e' : '#ef4444';
        }

        // Versions
        setText('api-version', data.api_version || '--');
        setText('python-version', data.python_version || '--');
        setText('endpoint-count', data.endpoint_count || '--');
        setText('test-count', data.test_count || '--');

        // Uptime
        if (data.uptime_seconds != null) {
            const h = Math.floor(data.uptime_seconds / 3600);
            const m = Math.floor((data.uptime_seconds % 3600) / 60);
            setText('uptime', h > 0 ? h + 'h ' + m + 'm' : m + 'm');
        }

        // Database counts
        if (data.database) {
            setText('count-farms', data.database.farms);
            setText('count-fields', data.database.fields);
            setText('count-soil', data.database.soil_analyses);
            setText('count-ndvi', data.database.ndvi_results);
            setText('count-thermal', data.database.thermal_results);
            setText('count-treatments', data.database.treatments);
            setText('count-alerts', data.database.alerts);
            setText('count-flights', data.database.flight_logs);
            setText('count-weather', data.database.weather_records);
        }

        // Latest data timestamps
        if (data.latest_data) {
            setTimestamp('latest-soil', data.latest_data.soil);
            setTimestamp('latest-ndvi', data.latest_data.ndvi);
            setTimestamp('latest-thermal', data.latest_data.thermal);
            setTimestamp('latest-weather', data.latest_data.weather);
        }
    } catch (err) {
        console.error('Failed to load system health:', err);
        setText('system-status', 'Error');
    } finally {
        if (btn) btn.disabled = false;
    }
}

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value != null ? value : '--';
}

function setTimestamp(id, isoStr) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!isoStr) { el.textContent = 'Sin datos'; return; }
    try {
        const d = new Date(isoStr);
        el.textContent = d.toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' });
    } catch {
        el.textContent = isoStr;
    }
}

document.addEventListener('DOMContentLoaded', loadSystemHealth);
