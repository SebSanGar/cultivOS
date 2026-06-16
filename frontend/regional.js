/* Regional intelligence page — /regional */

(function () {
    'use strict';

    let allRegions = [];

    function cropLabel(value) {
        return (window.cultivOS_i18n && window.cultivOS_i18n.cropName)
            ? window.cultivOS_i18n.cropName(value)
            : (value || '');
    }

    function _t(key, fallback) { return (window.cultivOS_i18n && window.cultivOS_i18n.t) ? window.cultivOS_i18n.t(key) : fallback; }

    async function fetchJSON(url) {
        try {
            const resp = await fetch(url);
            if (!resp.ok) return null;
            return await resp.json();
        } catch { return null; }
    }

    async function loadRegionalData() {
        const data = await fetchJSON('/api/intel/regional-summary');
        if (!data || !data.regions || data.regions.length === 0) {
            document.getElementById('regional-empty').style.display = '';
            document.getElementById('regional-regions').style.display = 'none';
            return;
        }

        allRegions = data.regions;
        populateStateFilter(allRegions);
        renderRegions(allRegions);
    }

    function populateStateFilter(regions) {
        const select = document.getElementById('regional-state-filter');
        const states = [...new Set(regions.map(r => r.state))].sort();
        states.forEach(st => {
            const opt = document.createElement('option');
            opt.value = st;
            opt.textContent = st;
            select.appendChild(opt);
        });
    }

    window.filterByState = function () {
        const state = document.getElementById('regional-state-filter').value;
        if (!state) {
            renderRegions(allRegions);
        } else {
            renderRegions(allRegions.filter(r => r.state === state));
        }
    };

    function renderRegions(regions) {
        const container = document.getElementById('regional-regions');
        const emptyEl = document.getElementById('regional-empty');

        if (regions.length === 0) {
            container.style.display = 'none';
            emptyEl.style.display = '';
            updateStats(0, 0, 0, 0);
            return;
        }

        emptyEl.style.display = 'none';
        container.style.display = '';

        // Stats
        const totalFarms = regions.reduce((s, r) => s + r.farm_count, 0);
        const totalFields = regions.reduce((s, r) => s + r.field_count, 0);
        const totalHectares = regions.reduce((s, r) => s + r.total_hectares, 0);
        updateStats(regions.length, totalFarms, totalFields, totalHectares);

        // Render cards
        container.innerHTML = regions.map(r => renderRegionCard(r)).join('');
    }

    function updateStats(regionCount, farmCount, fieldCount, hectares) {
        document.getElementById('regional-stat-regions').textContent = regionCount;
        document.getElementById('regional-stat-farms').textContent = farmCount;
        document.getElementById('regional-stat-fields').textContent = fieldCount;
        document.getElementById('regional-stat-hectares').textContent = hectares.toFixed(1);
    }

    function renderRegionCard(region) {
        const healthText = region.avg_health !== null
            ? region.avg_health.toFixed(1)
            : 'Sin datos';

        const cropsHtml = region.crop_distribution.length > 0
            ? region.crop_distribution.map(c =>
                '<span class="intel-badge">' + escapeHtml(cropLabel(c.crop_type)) + ' (' + c.field_count + ' campos, ' + c.total_hectares.toFixed(1) + ' ha)</span>'
            ).join(' ')
            : '<span class="intel-muted">' + _t('regional.noCrops', 'No crops registered') + '</span>';

        const treatmentsHtml = region.top_treatments.length > 0
            ? '<table class="intel-table"><thead><tr><th>' + _t('regional.thTreatment', 'Treatment') + '</th><th>' + _t('regional.thApplications', 'Applications') + '</th><th>' + _t('regional.thOrganic', 'Organic') + '</th></tr></thead><tbody>' +
              region.top_treatments.map(t =>
                  '<tr><td>' + escapeHtml(t.tratamiento) + '</td><td>' + t.application_count + '</td><td>' + (t.organic ? _t('common.yes', 'Yes') : _t('common.no', 'No')) + '</td></tr>'
              ).join('') +
              '</tbody></table>'
            : '<p class="intel-muted">' + _t('regional.noTreatments', 'No treatments registered') + '</p>';

        const alertsHtml = region.seasonal_alerts.length > 0
            ? '<ul class="intel-list">' +
              region.seasonal_alerts.map(a =>
                  '<li><strong>' + escapeHtml(a.crop) + '</strong>: ' + escapeHtml(a.message) + ' <span class="intel-badge">' + escapeHtml(a.season) + '</span></li>'
              ).join('') +
              '</ul>'
            : '<p class="intel-muted">' + _t('regional.noAlerts', 'No seasonal alerts') + '</p>';

        return '<div class="intel-panel">' +
            '<div class="intel-panel-header">' +
                '<h2 class="intel-panel-title">' + escapeHtml(region.state) + ', ' + escapeHtml(region.country) + '</h2>' +
                '<span class="intel-badge">' + region.farm_count + ' ' + _t('regional.farmsWord', 'farms') + '</span>' +
            '</div>' +
            '<div class="intel-panel-body">' +
                '<div class="intel-stats-strip" style="margin-bottom:1rem;">' +
                    '<div class="intel-stat"><div class="intel-stat-value">' + healthText + '</div><div class="intel-stat-label">' + _t('regional.avgHealth', 'Avg Health') + '</div></div>' +
                    '<div class="intel-stat"><div class="intel-stat-value">' + region.field_count + '</div><div class="intel-stat-label">' + _t('regional.statFields', 'Fields') + '</div></div>' +
                    '<div class="intel-stat"><div class="intel-stat-value">' + region.total_hectares.toFixed(1) + '</div><div class="intel-stat-label">' + _t('regional.statHectares', 'Hectares') + '</div></div>' +
                    '<div class="intel-stat"><div class="intel-stat-value">' + region.treatment_count + '</div><div class="intel-stat-label">' + _t('regional.statTreatments', 'Treatments') + '</div></div>' +
                    '<div class="intel-stat"><div class="intel-stat-value">' + region.ancestral_methods_count + '</div><div class="intel-stat-label">' + _t('regional.statAncestral', 'Ancestral Methods') + '</div></div>' +
                '</div>' +
                '<h3 style="margin:0.5rem 0;">' + _t('regional.distribCrops', 'Crop Distribution') + '</h3>' +
                '<div id="crop-distribution">' + cropsHtml + '</div>' +
                '<h3 style="margin:0.5rem 0;">' + _t('regional.topTreatments', 'Top Treatments') + '</h3>' +
                treatmentsHtml +
                '<h3 style="margin:0.5rem 0;">' + _t('regional.seasonalAlerts', 'Seasonal Alerts') + '</h3>' +
                alertsHtml +
            '</div>' +
        '</div>';
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    // Load on page ready
    loadRegionalData();
})();
