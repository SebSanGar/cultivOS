/* Soil carbon sequestration report page — /carbono */
(function () {
    "use strict";

    var farmSel = document.getElementById("carbon-farm-select");
    var fieldSel = document.getElementById("carbon-field-select");
    var emptyEl = document.getElementById("carbon-empty");
    var contentEl = document.getElementById("carbon-content");
    var chartInstance = null;

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
    window.loadFieldsForCarbon = function () {
        fieldSel.innerHTML = '<option value="">Seleccione un campo...</option>';
        contentEl.style.display = "none";
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

    /* Load carbon report for selected field + farm aggregate */
    window.loadCarbonReport = function () {
        var farmId = farmSel.value;
        var fieldId = fieldSel.value;
        if (!farmId || !fieldId) {
            contentEl.style.display = "none";
            emptyEl.style.display = "";
            resetStats();
            return;
        }
        emptyEl.style.display = "none";
        contentEl.style.display = "";

        Promise.all([
            fetchJSON("/api/farms/" + farmId + "/fields/" + fieldId + "/carbon"),
            fetchJSON("/api/farms/" + farmId + "/carbon")
        ]).then(function (results) {
            var fieldData = results[0];
            var farmData = results[1];
            if (!fieldData) {
                contentEl.style.display = "none";
                emptyEl.style.display = "";
                resetStats();
                return;
            }
            renderFieldCarbon(fieldData);
            if (farmData) {
                renderFarmBreakdown(farmData);
            }
        });
    };

    function resetStats() {
        document.getElementById("carbon-soc-value").textContent = "--";
        document.getElementById("carbon-co2e-value").textContent = "--";
        document.getElementById("carbon-trend-value").textContent = "--";
        document.getElementById("carbon-records-value").textContent = "--";
        document.getElementById("carbon-summary-text").textContent = "";
        document.getElementById("carbon-recommendations").innerHTML = "";
        document.getElementById("carbon-fields-tbody").innerHTML = "";
        if (chartInstance) {
            chartInstance.destroy();
            chartInstance = null;
        }
    }

    var tendenciaLabels = {
        ganando: "Ganando",
        estable: "Estable",
        perdiendo: "Perdiendo",
        datos_insuficientes: "Sin datos"
    };

    var tendenciaColors = {
        ganando: "#22c55e",
        estable: "#eab308",
        perdiendo: "#ef4444",
        datos_insuficientes: "#666"
    };

    var clasificacionLabels = {
        bajo: "Bajo",
        adecuado: "Adecuado",
        alto: "Alto"
    };

    function renderFieldCarbon(data) {
        /* Stats strip */
        var soc = data.soc_actual;
        if (soc) {
            document.getElementById("carbon-soc-value").textContent = soc.soc_tonnes_per_ha.toFixed(1);
            // Compute CO2e: SOC * 3.67 (molecular weight ratio CO2/C)
            var co2e = soc.soc_tonnes_per_ha * 3.67;
            document.getElementById("carbon-co2e-value").textContent = co2e.toFixed(1);
        } else {
            document.getElementById("carbon-soc-value").textContent = "--";
            document.getElementById("carbon-co2e-value").textContent = "--";
        }

        document.getElementById("carbon-trend-value").textContent =
            tendenciaLabels[data.tendencia] || data.tendencia;
        document.getElementById("carbon-trend-value").style.color =
            tendenciaColors[data.tendencia] || "#ccc";
        document.getElementById("carbon-records-value").textContent = data.registros;

        /* Summary */
        document.getElementById("carbon-summary-text").textContent = data.resumen;

        /* Recommendations */
        var recsContainer = document.getElementById("carbon-recommendations");
        recsContainer.innerHTML = "";
        if (data.recomendaciones && data.recomendaciones.length > 0) {
            var title = document.createElement("h3");
            title.style.cssText = "color:#eab308;font-size:0.9rem;margin-bottom:0.5rem;";
            title.textContent = "Recomendaciones:";
            recsContainer.appendChild(title);
            data.recomendaciones.forEach(function (rec) {
                var p = document.createElement("p");
                p.style.cssText = "color:#ccc;margin:0.3rem 0;padding-left:1rem;";
                p.textContent = "— " + rec;
                recsContainer.appendChild(p);
            });
        }

        /* Chart — show SOC change if we have data points */
        renderChart(data);
    }

    function renderChart(data) {
        if (chartInstance) {
            chartInstance.destroy();
            chartInstance = null;
        }

        var canvas = document.getElementById("carbon-chart");
        if (!canvas) return;

        // If insufficient data, show placeholder
        if (data.registros < 2 || !data.soc_actual) {
            var ctx = canvas.getContext("2d");
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = "#666";
            ctx.font = "14px Inter, sans-serif";
            ctx.textAlign = "center";
            ctx.fillText("Se necesitan al menos 2 registros para graficar tendencia", canvas.width / 2, canvas.height / 2);
            return;
        }

        // Build data points from cambio_soc (start + current)
        var socCurrent = data.soc_actual.soc_tonnes_per_ha;
        var socStart = socCurrent - data.cambio_soc_tonnes_per_ha;
        var labels = ["Primer analisis", "Actual"];
        var values = [parseFloat(socStart.toFixed(2)), parseFloat(socCurrent.toFixed(2))];
        var co2eValues = [parseFloat((socStart * 3.67).toFixed(2)), parseFloat((socCurrent * 3.67).toFixed(2))];

        var trendColor = tendenciaColors[data.tendencia] || "#4da6ff";

        chartInstance = new Chart(canvas.getContext("2d"), {
            type: "line",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "SOC (t/ha)",
                        data: values,
                        borderColor: trendColor,
                        backgroundColor: trendColor + "33",
                        fill: true,
                        tension: 0.3,
                        pointRadius: 6,
                        pointBackgroundColor: trendColor
                    },
                    {
                        label: "CO2e (t/ha)",
                        data: co2eValues,
                        borderColor: "#4da6ff",
                        backgroundColor: "#4da6ff22",
                        fill: false,
                        tension: 0.3,
                        pointRadius: 4,
                        pointBackgroundColor: "#4da6ff",
                        borderDash: [5, 5]
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: "#ccc" } }
                },
                scales: {
                    x: { ticks: { color: "#999" }, grid: { color: "#222" } },
                    y: {
                        ticks: { color: "#999" },
                        grid: { color: "#222" },
                        title: { display: true, text: "Toneladas por hectarea", color: "#999" }
                    }
                }
            }
        });
    }

    function renderFarmBreakdown(farmData) {
        var tbody = document.getElementById("carbon-fields-tbody");
        tbody.innerHTML = "";

        if (!farmData.fields || farmData.fields.length === 0) return;

        // Update CO2e stat with farm-level total
        document.getElementById("carbon-co2e-value").textContent =
            farmData.total_co2e_tonnes.toFixed(1);

        farmData.fields.forEach(function (f) {
            var tr = document.createElement("tr");
            var trendLabel = tendenciaLabels[f.tendencia] || f.tendencia;
            var trendColor = tendenciaColors[f.tendencia] || "#ccc";
            var nivelLabel = clasificacionLabels[f.clasificacion] || f.clasificacion;

            tr.innerHTML =
                '<td style="padding:0.75rem;border-bottom:1px solid #222;color:#eee;">' + esc(f.field_name) + '</td>' +
                '<td style="padding:0.75rem;border-bottom:1px solid #222;color:#ccc;text-align:right;">' + f.hectares.toFixed(1) + '</td>' +
                '<td style="padding:0.75rem;border-bottom:1px solid #222;color:#ccc;text-align:right;">' + f.soc_tonnes_per_ha.toFixed(1) + '</td>' +
                '<td style="padding:0.75rem;border-bottom:1px solid #222;color:#ccc;text-align:right;">' + f.co2e_tonnes.toFixed(1) + '</td>' +
                '<td style="padding:0.75rem;border-bottom:1px solid #222;text-align:center;"><span style="color:' + trendColor + ';">' + esc(nivelLabel) + '</span></td>' +
                '<td style="padding:0.75rem;border-bottom:1px solid #222;text-align:center;"><span style="color:' + trendColor + ';">' + esc(trendLabel) + '</span></td>';
            tbody.appendChild(tr);
        });
    }

    loadFarms();
})();
