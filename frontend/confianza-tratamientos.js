/* Treatment trust scores dashboard — /confianza-tratamientos */
(function () {
    "use strict";

    var allTreatments = [];

    function fetchJSON(url) {
        return fetch(url).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
    }
    function esc(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

    function trustColor(score) {
        if (score >= 70) return "#22c55e";
        if (score >= 40) return "#eab308";
        return "#ef4444";
    }

    function trustLabel(score) {
        if (score >= 70) return "Alta";
        if (score >= 40) return "Media";
        return "Baja";
    }

    async function loadData() {
        var data = await fetchJSON("/api/intel/treatment-trust");
        allTreatments = (data && data.treatments) ? data.treatments : [];

        populateCropFilter();
        renderAll(allTreatments);
    }

    function populateCropFilter() {
        var select = document.getElementById("trust-crop-filter");
        fetchJSON("/api/farms").then(function (farmsData) {
            var farms = (farmsData && farmsData.data) ? farmsData.data : (Array.isArray(farmsData) ? farmsData : []);
            var crops = [];
            farms.forEach(function (f) {
                if (f.fields) {
                    f.fields.forEach(function (fl) {
                        if (fl.crop_type && crops.indexOf(fl.crop_type) === -1) {
                            crops.push(fl.crop_type);
                        }
                    });
                }
            });
            crops.sort();
            crops.forEach(function (c) {
                var opt = document.createElement("option");
                opt.value = c;
                opt.textContent = c.charAt(0).toUpperCase() + c.slice(1);
                select.appendChild(opt);
            });
        });
    }

    function renderAll(treatments) {
        updateStats(treatments);
        renderCards(treatments);
    }

    function updateStats(treatments) {
        document.getElementById("stat-total").textContent = treatments.length;
        var totalFeedback = treatments.reduce(function (sum, t) { return sum + t.total_feedback; }, 0);
        document.getElementById("stat-feedback").textContent = totalFeedback;
        var avgTrust = treatments.length > 0
            ? (treatments.reduce(function (sum, t) { return sum + t.trust_score; }, 0) / treatments.length).toFixed(1)
            : "--";
        document.getElementById("stat-avg-trust").textContent = avgTrust;
        var best = treatments.length > 0 ? treatments[0].treatment_name : "--";
        document.getElementById("stat-best").textContent = best;
    }

    function renderCards(treatments) {
        var container = document.getElementById("trust-cards");
        if (treatments.length === 0) {
            container.innerHTML = '<p class="intel-empty">No hay retroalimentacion de agricultores registrada.</p>';
            return;
        }

        var html = "";
        treatments.forEach(function (t, i) {
            var color = trustColor(t.trust_score);
            var label = trustLabel(t.trust_score);
            var noteHtml = t.top_farmer_note
                ? '<p class="trust-note">"' + esc(t.top_farmer_note) + '"</p>'
                : '';

            html += '<div class="intel-card trust-card" data-treatment="' + esc(t.treatment_name) + '">'
                + '<div class="trust-card-header">'
                + '<span class="trust-rank">#' + (i + 1) + '</span>'
                + '<h3 class="trust-card-title">' + esc(t.treatment_name) + '</h3>'
                + '<span class="trust-badge" style="background:' + color + ';">' + label + ' ' + t.trust_score.toFixed(1) + '</span>'
                + '</div>'
                + '<div class="trust-card-metrics">'
                + '<div class="trust-metric"><span class="trust-metric-label">Retroalimentaciones</span><span class="trust-metric-value">' + t.total_feedback + '</span></div>'
                + '<div class="trust-metric"><span class="trust-metric-label">Positivas</span><span class="trust-metric-value" style="color:#22c55e;">' + t.positive_count + '</span></div>'
                + '<div class="trust-metric"><span class="trust-metric-label">Negativas</span><span class="trust-metric-value" style="color:#ef4444;">' + t.negative_count + '</span></div>'
                + '<div class="trust-metric"><span class="trust-metric-label">Calificacion promedio</span><span class="trust-metric-value">' + t.average_rating.toFixed(1) + '/5</span></div>'
                + '</div>'
                + '<div class="trust-bar-container">'
                + '<div class="trust-bar" style="width:' + t.trust_score + '%;background:' + color + ';"></div>'
                + '</div>'
                + noteHtml
                + '</div>';
        });
        container.innerHTML = html;
    }

    window.filterTrust = function () {
        var crop = document.getElementById("trust-crop-filter").value;
        if (!crop) {
            renderAll(allTreatments);
            return;
        }
        fetchJSON("/api/intel/treatment-trust?crop_type=" + encodeURIComponent(crop)).then(function (data) {
            var filtered = (data && data.treatments) ? data.treatments : [];
            renderAll(filtered);
        });
    };

    loadData();
})();
