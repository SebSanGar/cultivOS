/* Crop rotation planner page — /rotacion */
(function () {
    "use strict";

    var farmSel = document.getElementById("rotation-farm-select");
    var fieldSel = document.getElementById("rotation-field-select");
    var emptyEl = document.getElementById("rotation-empty");
    var contentEl = document.getElementById("rotation-content");
    var cardsEl = document.getElementById("rotation-cards");
    var multiyearSection = document.getElementById("multiyear-section");
    var multiyearCards = document.getElementById("multiyear-cards");

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

    var seasonLabels = {
        secas: "Secas (Nov-May)",
        temporal: "Temporal (Jun-Oct)",
        transicion: "Transicion"
    };

    var seasonColors = {
        secas: "#eab308",
        temporal: "#22c55e",
        transicion: "#4da6ff"
    };

    var purposeIcons = {
        "fijacion de nitrogeno": "N+",
        "cobertura / abono verde": "CV",
        "cultivo principal": "CP",
        "diversificacion": "DIV"
    };

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
    window.loadFieldsForRotation = function () {
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
                opt.textContent = f.name + (f.crop_type ? " (" + f.crop_type + ")" : "");
                fieldSel.appendChild(opt);
            });
        });
    };

    /* Load rotation plan for selected field */
    window.loadRotationPlan = function () {
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

        fetchJSON("/api/farms/" + farmId + "/fields/" + fieldId + "/rotation").then(function (data) {
            if (!data || !data.plan) {
                contentEl.style.display = "none";
                emptyEl.style.display = "";
                emptyEl.textContent = data && data.detail
                    ? data.detail
                    : "No se pudo generar el plan de rotacion. Verifique que el campo tiene un cultivo asignado.";
                resetStats();
                multiyearSection.style.display = "none";
                return;
            }
            renderPlan(data);
        });

        /* Also load multi-year plan */
        fetchJSON("/api/farms/" + farmId + "/fields/" + fieldId + "/rotation/multi-year").then(function (data) {
            if (!data || !data.plan) {
                multiyearSection.style.display = "none";
                return;
            }
            renderMultiYear(data);
        });
    };

    function resetStats() {
        document.getElementById("rotation-last-crop").textContent = "--";
        document.getElementById("rotation-region").textContent = "--";
        document.getElementById("rotation-seasons").textContent = "--";
        cardsEl.innerHTML = "";
        multiyearSection.style.display = "none";
        multiyearCards.innerHTML = "";
    }

    function renderPlan(data) {
        /* Stats strip */
        document.getElementById("rotation-last-crop").textContent = capitalize(data.last_crop);
        document.getElementById("rotation-region").textContent = capitalize(data.region);
        document.getElementById("rotation-seasons").textContent = data.plan.length;

        /* Season cards */
        cardsEl.innerHTML = "";
        data.plan.forEach(function (entry, idx) {
            var color = seasonColors[entry.season] || "#4da6ff";
            var seasonLabel = seasonLabels[entry.season] || capitalize(entry.season);
            var purposeIcon = purposeIcons[entry.purpose] || "";

            var card = document.createElement("div");
            card.className = "intel-card";
            card.style.cssText = "border-left:4px solid " + color + ";";

            card.innerHTML =
                '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;">' +
                    '<span style="color:' + color + ';font-weight:700;font-size:0.85rem;text-transform:uppercase;">' +
                        esc(seasonLabel) +
                    '</span>' +
                    '<span style="background:' + color + '22;color:' + color + ';padding:0.2rem 0.6rem;border-radius:4px;font-size:0.75rem;font-weight:600;">' +
                        'Temporada ' + (idx + 1) +
                    '</span>' +
                '</div>' +
                '<h3 style="color:#eee;font-size:1.3rem;margin:0 0 0.5rem 0;">' + esc(capitalize(entry.crop)) + '</h3>' +
                (purposeIcon
                    ? '<div style="margin-bottom:0.5rem;"><span style="background:#333;color:#ccc;padding:0.15rem 0.5rem;border-radius:3px;font-size:0.75rem;font-weight:500;">' + esc(purposeIcon) + ' ' + esc(capitalize(entry.purpose)) + '</span></div>'
                    : '') +
                '<p style="color:#999;font-size:0.85rem;line-height:1.5;margin:0 0 0.75rem 0;">' + esc(entry.reason) + '</p>' +
                '<div style="color:#666;font-size:0.8rem;">' + esc(entry.months) + '</div>';

            cardsEl.appendChild(card);
        });
    }

    function renderMultiYear(data) {
        multiyearSection.style.display = "";

        /* Milpa badge + info */
        var milpaBadge = document.getElementById("milpa-badge");
        var milpaInfo = document.getElementById("milpa-info");
        var milpaDesc = document.getElementById("milpa-description");
        if (data.milpa_recommended) {
            milpaBadge.style.display = "";
            milpaInfo.style.display = "";
            milpaDesc.textContent = data.milpa_description;
        } else {
            milpaBadge.style.display = "none";
            milpaInfo.style.display = "none";
        }

        /* OM stats */
        document.getElementById("om-start-val").textContent = data.om_start.toFixed(1) + "%";
        document.getElementById("om-end-val").textContent = data.om_end.toFixed(1) + "%";
        var delta = data.om_end - data.om_start;
        var deltaSign = delta >= 0 ? "+" : "";
        document.getElementById("om-delta-val").textContent = deltaSign + delta.toFixed(2) + "%";
        document.getElementById("om-delta-val").style.color = delta >= 0 ? "#22c55e" : "#ef4444";

        /* OM chart — simple bar/line chart with canvas */
        drawOMChart(data);

        /* Year cards — grouped by year */
        multiyearCards.innerHTML = "";
        for (var yr = 1; yr <= 3; yr++) {
            var yearEntries = data.plan.filter(function (e) { return e.year === yr; });
            var yearDiv = document.createElement("div");
            yearDiv.style.cssText = "background:#111a;border-radius:8px;padding:1.25rem;";
            var yearTitle = document.createElement("h3");
            yearTitle.style.cssText = "color:#eee;font-size:1rem;margin:0 0 1rem 0;";
            yearTitle.textContent = "Ano " + yr;
            yearDiv.appendChild(yearTitle);

            var grid = document.createElement("div");
            grid.style.cssText = "display:grid;grid-template-columns:1fr 1fr;gap:1rem;";

            yearEntries.forEach(function (entry) {
                var color = seasonColors[entry.season] || "#4da6ff";
                var seasonLabel = seasonLabels[entry.season] || capitalize(entry.season);
                var card = document.createElement("div");
                card.className = "intel-card";
                card.style.cssText = "border-left:4px solid " + color + ";margin:0;";

                var isMilpa = entry.purpose.indexOf("milpa") !== -1;
                var milpaTag = isMilpa
                    ? '<span style="background:#22c55e22;color:#22c55e;padding:0.15rem 0.5rem;border-radius:3px;font-size:0.7rem;font-weight:600;margin-left:0.5rem;">MILPA</span>'
                    : '';

                card.innerHTML =
                    '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">' +
                        '<span style="color:' + color + ';font-weight:700;font-size:0.8rem;text-transform:uppercase;">' + esc(seasonLabel) + '</span>' +
                        '<span style="color:#666;font-size:0.75rem;">MO: ' + entry.organic_matter_pct.toFixed(1) + '%</span>' +
                    '</div>' +
                    '<h4 style="color:#eee;font-size:1.1rem;margin:0 0 0.4rem 0;">' + esc(capitalize(entry.crop)) + milpaTag + '</h4>' +
                    '<p style="color:#999;font-size:0.8rem;line-height:1.4;margin:0 0 0.5rem 0;">' + esc(entry.reason) + '</p>' +
                    '<div style="display:flex;justify-content:space-between;color:#666;font-size:0.75rem;">' +
                        '<span>' + esc(capitalize(entry.purpose)) + '</span>' +
                        '<span>' + esc(entry.months) + '</span>' +
                    '</div>';

                grid.appendChild(card);
            });

            yearDiv.appendChild(grid);
            multiyearCards.appendChild(yearDiv);
        }
    }

    function drawOMChart(data) {
        var canvas = document.getElementById("om-chart");
        if (!canvas || !canvas.getContext) return;
        var ctx = canvas.getContext("2d");
        var w = canvas.width = canvas.parentElement.clientWidth - 32;
        var h = canvas.height = 120;

        ctx.clearRect(0, 0, w, h);

        var points = [data.om_start];
        data.plan.forEach(function (e) { points.push(e.organic_matter_pct); });

        var minOM = Math.min.apply(null, points) - 0.3;
        var maxOM = Math.max.apply(null, points) + 0.3;
        var range = maxOM - minOM || 1;

        var padding = 40;
        var chartW = w - padding * 2;
        var chartH = h - 30;

        /* Grid lines */
        ctx.strokeStyle = "#333";
        ctx.lineWidth = 0.5;
        for (var g = 0; g < 4; g++) {
            var gy = 10 + (chartH / 3) * g;
            ctx.beginPath();
            ctx.moveTo(padding, gy);
            ctx.lineTo(w - padding, gy);
            ctx.stroke();
        }

        /* Line */
        ctx.beginPath();
        ctx.strokeStyle = "#22c55e";
        ctx.lineWidth = 2;
        for (var i = 0; i < points.length; i++) {
            var x = padding + (chartW / (points.length - 1)) * i;
            var y = 10 + chartH - ((points[i] - minOM) / range) * chartH;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.stroke();

        /* Dots + labels */
        var labels = ["Inicio"];
        data.plan.forEach(function (e) {
            labels.push("A" + e.year + " " + (e.season === "secas" ? "S" : "T"));
        });

        ctx.fillStyle = "#22c55e";
        ctx.font = "11px Inter, sans-serif";
        ctx.textAlign = "center";
        for (var j = 0; j < points.length; j++) {
            var px = padding + (chartW / (points.length - 1)) * j;
            var py = 10 + chartH - ((points[j] - minOM) / range) * chartH;
            ctx.beginPath();
            ctx.arc(px, py, 4, 0, Math.PI * 2);
            ctx.fill();
            /* Value above dot */
            ctx.fillStyle = "#ccc";
            ctx.fillText(points[j].toFixed(1) + "%", px, py - 10);
            /* Label below */
            ctx.fillStyle = "#666";
            ctx.fillText(labels[j], px, h - 2);
            ctx.fillStyle = "#22c55e";
        }
    }

    function capitalize(s) {
        if (!s) return "";
        return s.charAt(0).toUpperCase() + s.slice(1);
    }

    loadFarms();
})();
