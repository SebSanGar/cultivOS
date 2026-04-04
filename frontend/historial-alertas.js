/**
 * Historial de Alertas — timeline of all alerts per farm.
 * Fetches from GET /api/alerts/history with optional filters.
 */

(async function () {
  const timeline = document.getElementById('alertas-timeline');
  const loading = document.getElementById('alertas-loading');
  const empty = document.getElementById('alertas-empty');
  const farmFilter = document.getElementById('alertas-farm-filter');
  const typeFilter = document.getElementById('alertas-type-filter');
  const severityFilter = document.getElementById('alertas-severity-filter');
  const dateStart = document.getElementById('alertas-date-start');
  const dateEnd = document.getElementById('alertas-date-end');

  let allData = [];

  // ── Helpers ──────────────────────────────────────────

  function esc(s) {
    if (!s) return '';
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  function severityBadge(severity) {
    const colors = {
      critical: '#ef4444',
      warning: '#f59e0b',
      info: '#3b82f6',
    };
    const labels = {
      critical: 'Critica',
      warning: 'Advertencia',
      info: 'Info',
    };
    const color = colors[severity] || '#6b7280';
    const label = labels[severity] || severity;
    return '<span style="background:' + color + ';color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75rem;font-weight:600;">' + esc(label) + '</span>';
  }

  function sourceBadge(source) {
    const label = source === 'sms' ? 'SMS/WhatsApp' : 'Sistema';
    const bg = source === 'sms' ? '#8b5cf6' : '#6366f1';
    return '<span style="background:' + bg + ';color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75rem;font-weight:600;">' + label + '</span>';
  }

  function statusBadge(status) {
    if (!status) return '';
    const colors = { sent: '#22c55e', pending: '#f59e0b', failed: '#ef4444' };
    const labels = { sent: 'Enviado', pending: 'Pendiente', failed: 'Fallido' };
    const color = colors[status] || '#6b7280';
    return '<span style="background:' + color + ';color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75rem;margin-left:0.5rem;">' + esc(labels[status] || status) + '</span>';
  }

  function formatDate(iso) {
    if (!iso) return '--';
    const d = new Date(iso);
    return d.toLocaleDateString('es-MX', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  }

  function typeLabel(t) {
    const map = {
      low_health: 'Salud baja',
      irrigation: 'Riego urgente',
      anomaly_health_drop: 'Anomalia de salud',
      anomaly_ndvi_drop: 'Anomalia NDVI',
      weather: 'Clima',
      health: 'Salud',
      recommendation: 'Recomendacion',
    };
    return map[t] || t;
  }

  // ── Render ──────────────────────────────────────────

  function renderCards(data) {
    if (!data.length) {
      timeline.style.display = 'none';
      empty.style.display = 'block';
      return;
    }
    empty.style.display = 'none';
    timeline.style.display = 'grid';

    timeline.innerHTML = data.map(function (a) {
      return '<div class="intel-card" data-severity="' + esc(a.severity) + '">'
        + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;">'
        + '<span style="font-weight:700;color:#e5e7eb;">' + esc(typeLabel(a.alert_type)) + '</span>'
        + '<div>' + severityBadge(a.severity) + ' ' + sourceBadge(a.source) + statusBadge(a.status) + '</div>'
        + '</div>'
        + '<p style="color:#9ca3af;margin:0 0 0.75rem;">' + esc(a.message) + '</p>'
        + '<div style="display:flex;justify-content:space-between;font-size:0.8rem;color:#6b7280;">'
        + '<span>Granja #' + a.farm_id + (a.field_id ? ' / Campo #' + a.field_id : '') + '</span>'
        + '<span>' + formatDate(a.created_at) + '</span>'
        + '</div>'
        + '</div>';
    }).join('');
  }

  function updateStats(data) {
    document.getElementById('alertas-stat-total').textContent = data.length;
    document.getElementById('alertas-stat-critical').textContent = data.filter(function (a) { return a.severity === 'critical'; }).length;
    document.getElementById('alertas-stat-pending').textContent = data.filter(function (a) { return a.status === 'pending'; }).length;
    var farms = new Set(data.map(function (a) { return a.farm_id; }));
    document.getElementById('alertas-stat-farms').textContent = farms.size;
  }

  // ── Filter ──────────────────────────────────────────

  function applyFilters() {
    var filtered = allData.slice();
    var farmVal = farmFilter.value;
    var typeVal = typeFilter.value;
    var sevVal = severityFilter.value;
    var startVal = dateStart.value;
    var endVal = dateEnd.value;

    if (farmVal) filtered = filtered.filter(function (a) { return String(a.farm_id) === farmVal; });
    if (typeVal) filtered = filtered.filter(function (a) { return a.alert_type === typeVal; });
    if (sevVal) filtered = filtered.filter(function (a) { return a.severity === sevVal; });
    if (startVal) filtered = filtered.filter(function (a) { return a.created_at >= startVal; });
    if (endVal) filtered = filtered.filter(function (a) { return a.created_at <= endVal + 'T23:59:59'; });

    updateStats(filtered);
    renderCards(filtered);
  }

  // ── Load ──────────────────────────────────────────

  async function loadData() {
    try {
      var resp = await fetch('/api/alerts/history');
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      allData = await resp.json();

      // Populate farm filter
      var farmIds = [...new Set(allData.map(function (a) { return a.farm_id; }))];
      farmIds.sort(function (a, b) { return a - b; });
      farmIds.forEach(function (fid) {
        var opt = document.createElement('option');
        opt.value = fid;
        opt.textContent = 'Granja #' + fid;
        farmFilter.appendChild(opt);
      });

      updateStats(allData);
      renderCards(allData);
    } catch (e) {
      timeline.innerHTML = '<p style="color:#ef4444;">Error al cargar alertas: ' + esc(e.message) + '</p>';
      timeline.style.display = 'block';
    }
    loading.style.display = 'none';
  }

  // ── Events ──────────────────────────────────────────

  farmFilter.addEventListener('change', applyFilters);
  typeFilter.addEventListener('change', applyFilters);
  severityFilter.addEventListener('change', applyFilters);
  dateStart.addEventListener('change', applyFilters);
  dateEnd.addEventListener('change', applyFilters);

  // ── Analytics ──────────────────────────────────────────

  async function loadAnalytics() {
    try {
      var resp = await fetch('/api/alerts/analytics');
      if (!resp.ok) return;
      var data = await resp.json();
      document.getElementById('analytics-delivery-rate').textContent = data.delivery_rate + '%';
      document.getElementById('analytics-sms-count').textContent = data.total_sms;
      document.getElementById('analytics-system-count').textContent = data.total_system;
      document.getElementById('analytics-farms-reached').textContent = data.farms_reached;
    } catch (e) {
      // Analytics are non-critical — fail silently
    }
  }

  await loadData();
  await loadAnalytics();
})();
