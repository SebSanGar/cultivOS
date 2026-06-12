/* timeline.js — Field health history timeline */

(function () {
    'use strict';

    const farmSelect = document.getElementById('tl-farm-select');
    const fieldSelect = document.getElementById('tl-field-select');
    const timelineEl = document.getElementById('tl-timeline');
    const emptyEl = document.getElementById('tl-empty');
    const scoreCountEl = document.getElementById('tl-score-count');
    const trendEl = document.getElementById('tl-trend');
    const treatmentCountEl = document.getElementById('tl-treatment-count');
    const latestScoreEl = document.getElementById('tl-latest-score');

    function _t(key, fallback) { return (window.cultivOS_i18n && window.cultivOS_i18n.t) ? window.cultivOS_i18n.t(key) : fallback; }

    function getTrendLabels() {
        return {
            improving: _t('tl.trend.improving', 'Improving'),
            stable: _t('tl.trend.stable', 'Stable'),
            declining: _t('tl.trend.declining', 'Declining'),
            insufficient_data: _t('tl.trend.insufficient', 'Insufficient data')
        };
    }

    async function fetchJSON(url) {
        try {
            const resp = await fetch(url);
            if (!resp.ok) return null;
            return await resp.json();
        } catch {
            return null;
        }
    }

    function esc(str) {
        const d = document.createElement('div');
        d.textContent = str || '';
        return d.innerHTML;
    }

    function formatDate(iso) {
        if (!iso) return '--';
        const d = new Date(iso);
        return d.toLocaleDateString('es-MX', { year: 'numeric', month: 'short', day: 'numeric' });
    }

    function scoreColor(score) {
        if (score >= 70) return '#00c896';
        if (score >= 40) return '#f0b429';
        return '#e74c3c';
    }

    function urgenciaClass(urgencia) {
        if (urgencia === 'alta') return 'tl-urgencia-alta';
        if (urgencia === 'media') return 'tl-urgencia-media';
        return 'tl-urgencia-baja';
    }

    // Load farms on startup
    async function loadFarms() {
        const data = await fetchJSON('/api/farms?page_size=100');
        if (!data) return;
        const farms = (data.data || data.items) || [];
        farms.forEach(function (f) {
            const opt = document.createElement('option');
            opt.value = f.id;
            opt.textContent = f.name;
            farmSelect.appendChild(opt);
        });
        if (farms.length === 1) {
            farmSelect.value = farms[0].id;
            loadFieldsForTimeline();
        }
    }

    // Load fields when farm is selected
    window.loadFieldsForTimeline = async function () {
        const farmId = farmSelect.value;
        fieldSelect.innerHTML = '<option value="">' + _t('nav.selectField', 'Select a field...') + '</option>';
        timelineEl.innerHTML = '';
        emptyEl.style.display = 'block';
        resetStats();
        if (!farmId) return;

        const data = await fetchJSON('/api/farms/' + farmId + '/fields');
        if (!data) return;
        const fields = Array.isArray(data) ? data : (data.fields || []);
        fields.forEach(function (f) {
            const opt = document.createElement('option');
            opt.value = f.id;
            opt.textContent = f.name + ' (' + (f.crop_type || '--') + ')';
            fieldSelect.appendChild(opt);
        });
        if (fields.length === 1) {
            fieldSelect.value = fields[0].id;
            loadTimeline();
        }
    };

    function resetStats() {
        scoreCountEl.textContent = '--';
        trendEl.textContent = '--';
        treatmentCountEl.textContent = '--';
        latestScoreEl.textContent = '--';
    }

    // Load and merge timeline
    window.loadTimeline = async function () {
        const farmId = farmSelect.value;
        const fieldId = fieldSelect.value;
        if (!farmId || !fieldId) {
            timelineEl.innerHTML = '';
            emptyEl.style.display = 'block';
            resetStats();
            return;
        }

        emptyEl.style.display = 'none';

        const [healthData, treatments] = await Promise.all([
            fetchJSON('/api/farms/' + farmId + '/fields/' + fieldId + '/health/history'),
            fetchJSON('/api/farms/' + farmId + '/fields/' + fieldId + '/treatments/treatment-history')
        ]);

        const events = [];

        // Health score events
        if (healthData && healthData.scores) {
            healthData.scores.forEach(function (s) {
                events.push({
                    type: 'health',
                    date: s.scored_at,
                    score: s.score,
                    trend: s.trend,
                    sources: s.sources || [],
                    breakdown: s.breakdown || {}
                });
            });
            scoreCountEl.textContent = healthData.count || 0;
            trendEl.textContent = getTrendLabels()[healthData.trend] || healthData.trend || '--';
            if (healthData.scores.length > 0) {
                const latest = healthData.scores[healthData.scores.length - 1];
                latestScoreEl.textContent = latest.score.toFixed(1);
            }
        } else {
            scoreCountEl.textContent = '0';
            trendEl.textContent = '--';
            latestScoreEl.textContent = '--';
        }

        // Treatment events
        const treatmentList = Array.isArray(treatments) ? treatments : [];
        treatmentList.forEach(function (t) {
            events.push({
                type: 'treatment',
                date: t.applied_at || t.created_at,
                problema: t.problema,
                problema_en: t.problema_en,
                problema_es: t.problema_es,
                tratamiento: t.tratamiento,
                tratamiento_en: t.tratamiento_en,
                tratamiento_es: t.tratamiento_es,
                urgencia: t.urgencia,
                urgencia_en: t.urgencia_en,
                urgencia_es: t.urgencia_es,
                organic: t.organic,
                applied_notes: t.applied_notes,
                health_score_used: t.health_score_used
            });
        });
        treatmentCountEl.textContent = treatmentList.length;

        // Sort by date ascending
        events.sort(function (a, b) {
            return new Date(a.date) - new Date(b.date);
        });

        if (events.length === 0) {
            timelineEl.innerHTML = '<p class="tl-no-data">' + _t('tl.noData', 'No health or treatment data for this field.') + '</p>';
            return;
        }

        renderTimeline(events);
    };

    function renderTimeline(events) {
        var html = '';
        events.forEach(function (ev, idx) {
            if (ev.type === 'health') {
                html += renderHealthEvent(ev, idx);
            } else {
                html += renderTreatmentEvent(ev, idx);
            }
        });
        timelineEl.innerHTML = html;
    }

    function renderHealthEvent(ev, idx) {
        var color = scoreColor(ev.score);
        var sourcesStr = (ev.sources || []).join(', ') || 'N/A';
        var breakdownHtml = '';
        if (ev.breakdown && Object.keys(ev.breakdown).length > 0) {
            breakdownHtml = '<div class="tl-breakdown">';
            Object.keys(ev.breakdown).forEach(function (k) {
                breakdownHtml += '<span class="tl-breakdown-item">' + esc(k) + ': ' + ev.breakdown[k].toFixed(1) + '</span>';
            });
            breakdownHtml += '</div>';
        }
        return '<div class="tl-event tl-event-health" data-idx="' + idx + '">' +
            '<div class="tl-event-marker" style="background:' + color + '"></div>' +
            '<div class="tl-event-content">' +
                '<div class="tl-event-date">' + formatDate(ev.date) + '</div>' +
                '<div class="tl-event-title">' + _t('tl.healthScore', 'Health Score: ') + '<strong style="color:' + color + '">' + ev.score.toFixed(1) + '</strong></div>' +
                '<div class="tl-event-detail">' + _t('tl.sources', 'Sources: ') + esc(sourcesStr) + '</div>' +
                breakdownHtml +
            '</div>' +
        '</div>';
    }

    function renderTreatmentEvent(ev, idx) {
        var urgClass = urgenciaClass(ev.urgencia);
        var organicBadge = ev.organic ? '<span class="tl-badge tl-badge-organic">' + _t('tl.badge.organic', 'Organic') + '</span>' : '';
        var notesHtml = ev.applied_notes ? '<div class="tl-event-detail">' + _t('tl.notes', 'Notes: ') + esc(ev.applied_notes) + '</div>' : '';
        return '<div class="tl-event tl-event-treatment" data-idx="' + idx + '">' +
            '<div class="tl-event-marker tl-marker-treatment"></div>' +
            '<div class="tl-event-content">' +
                '<div class="tl-event-date">' + formatDate(ev.date) + '</div>' +
                '<div class="tl-event-title">' + _t('tl.treatment', 'Treatment: ') + '<strong>' + esc(window.cultivOS_i18n ? window.cultivOS_i18n.localized(ev, 'tratamiento') : (ev.tratamiento_es || ev.tratamiento || '')) + '</strong></div>' +
                '<div class="tl-event-detail">' + _t('tl.problem', 'Problem: ') + esc(window.cultivOS_i18n ? window.cultivOS_i18n.localized(ev, 'problema') : (ev.problema_es || ev.problema || '')) + '</div>' +
                '<div class="tl-event-badges">' +
                    '<span class="tl-badge ' + urgClass + '">' + esc(window.cultivOS_i18n ? window.cultivOS_i18n.localized(ev, 'urgencia') : (ev.urgencia_es || ev.urgencia || '')) + '</span>' +
                    organicBadge +
                '</div>' +
                '<div class="tl-event-detail">' + _t('tl.healthAt', 'Health at time: ') + (ev.health_score_used != null ? ev.health_score_used.toFixed(1) : '--') + '</div>' +
                notesHtml +
            '</div>' +
        '</div>';
    }

    // Init
    loadFarms();
    emptyEl.style.display = 'block';
})();
