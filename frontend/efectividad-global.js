/* Global treatment effectiveness dashboard — /efectividad-global */
(function () {
    "use strict";

    var allTreatments = [];
    var allFarms = [];
    var barChart = null;

    function fetchJSON(url) {
        return fetch(url).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
    }
    function esc(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

    function deltaColor(delta) {
        if (delta >= 10) return "#22c55e";
        if (delta >= 0) return "#eab308";
        return "#ef4444";
    }

    async function loadData() {
        var results = await Promise.all([
            fetchJSON("/api/intel/treatment-effectiveness-report"),
            fetchJSON("/api/farms")
        ]);
        var effData = results[0];
        var farmsData = results[1];

        allTreatments = (effData && effData.treatments) ? effData.treatments : [];
        allFarms = Array.isArray(farmsData) ? farmsData : [];

        populateFilters();
        renderAll(allTreatments);
    }

    function populateFilters() {
        var cropSelect = document.getElementById("effg-crop-filter");
        var regionSelect = document.getElementById("effg-region-filter");

        // Crop types from farms' fields (approximate from treatment data)
        var crops = [];
        allFarms.forEach(function (f) {
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
            cropSelect.appendChild(opt);
        });

        // Regions from farms
        var regions = [];
        allFarms.forEach(function (f) {
            if (f.state && regions.indexOf(f.state) === -1) {
                regions.push(f.state);
            }
        });
        regions.sort();
        regions.forEach(function (r) {
            var opt = document.createElement("option");
            opt.value = r;
            opt.textContent = r;
            regionSelect.appendChild(opt);
        });
    }

    window.filterEffectiveness = function () {
        var crop = document.getElementById("effg-crop-filter").value;
        if (crop) {
            // Re-fetch with crop_type filter
            fetchJSON("/api/intel/treatment-effectiveness-report?crop_type=" + encodeURIComponent(crop)).then(function (data) {
                var treatments = (data && data.treatments) ? data.treatments : [];
                renderAll(treatments);
            });
        } else {
            renderAll(allTreatments);
        }
    };

    function renderAll(treatments) {
        var emptyEl = document.getElementById("effg-empty");
        var chartContainer = document.getElementById("effg-chart-container");
        var cardsEl = document.getElementById("effg-cards");

        if (!treatments || treatments.length === 0) {
            emptyEl.style.display = "";
            chartContainer.style.display = "none";
            cardsEl.style.display = "none";
            updateStats(0, 0, 0, "--");
            return;
        }

        emptyEl.style.display = "none";
        chartContainer.style.display = "";
        cardsEl.style.display = "";

        // Stats
        var totalApps = treatments.reduce(function (s, t) { return s + (t.total_applications || 0); }, 0);
        var avgDelta = Math.round(treatments.reduce(function (s, t) { return s + (t.avg_health_delta || 0); }, 0) / treatments.length);
        var best = treatments[0].tratamiento || "--";
        updateStats(treatments.length, totalApps, avgDelta, best);

        // Chart
        renderChart(treatments);

        // Cards
        renderCards(treatments);
    }

    function updateStats(count, apps, avgDelta, best) {
        document.getElementById("effg-stat-treatments").textContent = count;
        document.getElementById("effg-stat-applications").textContent = apps;
        var deltaEl = document.getElementById("effg-stat-avg-delta");
        deltaEl.textContent = typeof avgDelta === "number" ? (avgDelta >= 0 ? "+" : "") + avgDelta : "--";
        deltaEl.style.color = typeof avgDelta === "number" ? deltaColor(avgDelta) : "";
        document.getElementById("effg-stat-best").textContent = best;
        document.getElementById("effg-stat-best").style.fontSize = "0.75rem";
    }

    function renderChart(treatments) {
        var canvas = document.getElementById("effg-bar-chart");
        var ctx = canvas.getContext("2d");

        if (barChart) barChart.destroy();

        var labels = treatments.map(function (t) { return t.tratamiento || ""; });
        var deltas = treatments.map(function (t) { return t.avg_health_delta || 0; });
        var colors = deltas.map(function (d) { return deltaColor(d); });

        barChart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Delta de Salud",
                    data: deltas,
                    backgroundColor: colors,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: "#ccc" } }
                },
                scales: {
                    x: {
                        ticks: { color: "#999", maxRotation: 45 },
                        grid: { color: "#222" }
                    },
                    y: {
                        ticks: { color: "#999" },
                        grid: { color: "#222" },
                        beginAtZero: true,
                        title: { display: true, text: "Delta de Salud", color: "#999" }
                    }
                }
            }
        });
    }

    function renderCards(treatments) {
        var cardsEl = document.getElementById("effg-cards");
        cardsEl.innerHTML = treatments.map(function (t) {
            var delta = t.avg_health_delta || 0;
            var dColor = deltaColor(delta);
            var deltaStr = (delta >= 0 ? "+" : "") + Math.round(delta);
            var apps = t.total_applications || 0;
            var successRate = t.feedback_success_rate;
            var rating = t.avg_rating;

            return '<div class="intel-card">' +
                '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">' +
                '<div class="intel-card-title">' + esc(t.tratamiento || "") + '</div>' +
                '<div style="font-size:1.4rem;font-weight:800;color:' + dColor + ';">' + deltaStr + '</div>' +
                '</div>' +
                '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px;">' +
                '<span class="severity-badge" style="background:rgba(99,102,241,0.15);color:#6366f1;">' + apps + ' aplicaciones</span>' +
                (successRate !== null && successRate !== undefined
                    ? '<span class="severity-badge" style="background:rgba(34,197,94,0.15);color:#22c55e;">' + successRate + '% exito</span>'
                    : '') +
                (rating !== null && rating !== undefined
                    ? '<span class="severity-badge" style="background:rgba(250,204,21,0.15);color:#facc15;">' + rating.toFixed(1) + ' estrellas</span>'
                    : '') +
                '</div>' +
                '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">' +
                '<span style="color:#999;font-size:0.8rem;">Antes:</span>' +
                '<div style="flex:1;height:8px;background:rgba(255,255,255,0.08);border-radius:4px;overflow:hidden;">' +
                '<div style="width:' + Math.min(100, Math.max(5, 50)) + '%;height:100%;background:#666;border-radius:4px;"></div>' +
                '</div>' +
                '<span style="color:#999;font-size:0.8rem;">Despues:</span>' +
                '<div style="flex:1;height:8px;background:rgba(255,255,255,0.08);border-radius:4px;overflow:hidden;">' +
                '<div style="width:' + Math.min(100, Math.max(5, 50 + delta)) + '%;height:100%;background:' + dColor + ';border-radius:4px;"></div>' +
                '</div>' +
                '</div>' +
                '<div style="color:#666;font-size:0.75rem;">Puntaje compuesto: ' + (t.composite_score || 0).toFixed(1) + '</div>' +
                '</div>';
        }).join("");
    }

    // Load on page ready
    loadData();
})();
