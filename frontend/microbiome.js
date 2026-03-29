/* Microbiome health page — /microbioma */
(function () {
    "use strict";

    var farmSel = document.getElementById("micro-farm-select");
    var fieldSel = document.getElementById("micro-field-select");
    var emptyEl = document.getElementById("micro-empty");
    var noneEl = document.getElementById("micro-none");
    var contentEl = document.getElementById("micro-content");

    var respirationChart = null;
    var ratioChart = null;
    var biomassChart = null;

    function fetchJSON(url) {
        return fetch(url).then(function (r) {
            if (!r.ok) return null;
            return r.json();
        }).catch(function () { return null; });
    }

    function esc(s) {
        var d = document.createElement("div");
        d.textContent = s;
        return d.innerHTML;
    }

    function classLabel(c) {
        if (c === "healthy") return "Saludable";
        if (c === "moderate") return "Moderado";
        return "Degradado";
    }

    function classColor(c) {
        if (c === "healthy") return "#00c896";
        if (c === "moderate") return "#f0b429";
        return "#ef4444";
    }

    /* Load farms on init */
    function loadFarms() {
        fetchJSON("/api/farms").then(function (farms) {
            if (!farms) return;
            farms.forEach(function (f) {
                var opt = document.createElement("option");
                opt.value = f.id;
                opt.textContent = f.name;
                farmSel.appendChild(opt);
            });
        });
        emptyEl.style.display = "";
    }

    /* Load fields for selected farm */
    window.loadFieldsForMicro = function () {
        fieldSel.innerHTML = '<option value="">Seleccione un campo...</option>';
        contentEl.style.display = "none";
        noneEl.style.display = "none";
        emptyEl.style.display = "";
        resetStats();
        var farmId = farmSel.value;
        if (!farmId) return;
        fetchJSON("/api/farms/" + farmId + "/fields").then(function (fields) {
            if (!fields) return;
            fields.forEach(function (f) {
                var opt = document.createElement("option");
                opt.value = f.id;
                opt.textContent = f.name;
                fieldSel.appendChild(opt);
            });
        });
    };

    /* Load microbiome records for selected field */
    window.loadMicrobiome = function () {
        var farmId = farmSel.value;
        var fieldId = fieldSel.value;
        if (!farmId || !fieldId) {
            contentEl.style.display = "none";
            noneEl.style.display = "none";
            emptyEl.style.display = "";
            resetStats();
            return;
        }
        emptyEl.style.display = "none";
        noneEl.style.display = "none";

        fetchJSON("/api/farms/" + farmId + "/fields/" + fieldId + "/microbiome").then(function (data) {
            if (!data || data.length === 0) {
                contentEl.style.display = "none";
                noneEl.style.display = "";
                resetStats();
                return;
            }
            renderMicrobiome(data);
        });
    };

    function resetStats() {
        document.getElementById("micro-avg-respiration").textContent = "--";
        document.getElementById("micro-avg-ratio").textContent = "--";
        document.getElementById("micro-record-count").textContent = "--";
    }

    function renderMicrobiome(records) {
        /* Sort chronologically (oldest first) for charts */
        var sorted = records.slice().sort(function (a, b) {
            return new Date(a.sampled_at) - new Date(b.sampled_at);
        });

        /* Stats strip */
        var avgResp = sorted.reduce(function (s, r) { return s + r.respiration_rate; }, 0) / sorted.length;
        var avgRatio = sorted.reduce(function (s, r) { return s + r.fungi_bacteria_ratio; }, 0) / sorted.length;
        document.getElementById("micro-avg-respiration").textContent = avgResp.toFixed(1);
        document.getElementById("micro-avg-ratio").textContent = avgRatio.toFixed(2);
        document.getElementById("micro-record-count").textContent = sorted.length;

        contentEl.style.display = "";
        noneEl.style.display = "none";

        var labels = sorted.map(function (r) {
            return new Date(r.sampled_at).toLocaleDateString("es-MX", { month: "short", year: "numeric" });
        });

        /* Respiration chart */
        var respCtx = document.getElementById("micro-respiration-chart").getContext("2d");
        if (respirationChart) respirationChart.destroy();
        respirationChart = new Chart(respCtx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [{
                    label: "Respiracion (mg CO2/kg/dia)",
                    data: sorted.map(function (r) { return r.respiration_rate; }),
                    borderColor: "#00c896",
                    backgroundColor: "rgba(0,200,150,0.1)",
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { labels: { color: "#ccc" } } },
                scales: {
                    x: { ticks: { color: "#999" }, grid: { color: "#222" } },
                    y: { ticks: { color: "#999" }, grid: { color: "#222" }, beginAtZero: true }
                }
            }
        });

        /* Fungi/Bacteria ratio chart */
        var ratioCtx = document.getElementById("micro-ratio-chart").getContext("2d");
        if (ratioChart) ratioChart.destroy();
        ratioChart = new Chart(ratioCtx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Hongos/Bacterias",
                    data: sorted.map(function (r) { return r.fungi_bacteria_ratio; }),
                    backgroundColor: sorted.map(function (r) { return classColor(r.classification); }),
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { labels: { color: "#ccc" } } },
                scales: {
                    x: { ticks: { color: "#999" }, grid: { color: "#222" } },
                    y: { ticks: { color: "#999" }, grid: { color: "#222" }, beginAtZero: true }
                }
            }
        });

        /* Biomass chart */
        var bioCtx = document.getElementById("micro-biomass-chart").getContext("2d");
        if (biomassChart) biomassChart.destroy();
        biomassChart = new Chart(bioCtx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [{
                    label: "Carbono Biomasa (mg C/kg)",
                    data: sorted.map(function (r) { return r.microbial_biomass_carbon; }),
                    borderColor: "#4da6ff",
                    backgroundColor: "rgba(77,166,255,0.1)",
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { labels: { color: "#ccc" } } },
                scales: {
                    x: { ticks: { color: "#999" }, grid: { color: "#222" } },
                    y: { ticks: { color: "#999" }, grid: { color: "#222" }, beginAtZero: true }
                }
            }
        });

        /* Data table */
        var tbody = document.getElementById("micro-table-body");
        tbody.innerHTML = "";
        sorted.forEach(function (r) {
            var tr = document.createElement("tr");
            var dateStr = new Date(r.sampled_at).toLocaleDateString("es-MX");
            var clsLabel = classLabel(r.classification);
            var clsCol = classColor(r.classification);
            tr.innerHTML =
                "<td>" + esc(dateStr) + "</td>" +
                "<td>" + r.respiration_rate.toFixed(1) + " mg CO2/kg/dia</td>" +
                "<td>" + r.microbial_biomass_carbon.toFixed(0) + " mg C/kg</td>" +
                "<td>" + r.fungi_bacteria_ratio.toFixed(2) + "</td>" +
                '<td><span style="color:' + clsCol + ';font-weight:600;">' + esc(clsLabel) + "</span></td>";
            tbody.appendChild(tr);
        });
    }

    loadFarms();
})();
