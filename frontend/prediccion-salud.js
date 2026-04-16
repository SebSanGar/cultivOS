(async function () {
    var farmSelect = document.getElementById("pred-farm-select");
    var fieldSelect = document.getElementById("pred-field-select");
    var content = document.getElementById("pred-content");
    var emptyMsg = document.getElementById("pred-empty");
    var currentScore = document.getElementById("pred-current-score");
    var predictedScore = document.getElementById("pred-predicted-score");
    var trendArrow = document.getElementById("pred-trend-arrow");
    var deltaBadge = document.getElementById("pred-delta-badge");
    var confidencePill = document.getElementById("pred-confidence-pill");
    var riskFlag = document.getElementById("pred-risk-flag");

    async function fetchJSON(url) {
        var r = await fetch(url);
        if (!r.ok) return null;
        return r.json();
    }

    function trendSymbol(dir) {
        if (dir === "improving") return { symbol: "\u2191", cls: "up" };
        if (dir === "declining") return { symbol: "\u2193", cls: "down" };
        return { symbol: "\u2192", cls: "flat" };
    }

    function confidenceEs(c) {
        var map = { high: "Alta", medium: "Media", low: "Baja" };
        return map[c] || c;
    }

    function confidenceCls(c) {
        var map = { high: "alta", medium: "media", low: "baja" };
        return map[c] || "media";
    }

    function render(data) {
        if (!data) {
            content.style.display = "none";
            emptyMsg.textContent = "No hay datos de prediccion para este campo.";
            emptyMsg.style.display = "block";
            return;
        }
        content.style.display = "block";
        emptyMsg.style.display = "none";

        currentScore.textContent = data.current_avg_health.toFixed(1);
        predictedScore.textContent = data.predicted_health_30d.toFixed(1);

        var t = trendSymbol(data.trend_direction);
        trendArrow.textContent = t.symbol;
        trendArrow.className = "pred-trend-arrow " + t.cls;

        var delta = data.predicted_health_30d - data.current_avg_health;
        var sign = delta >= 0 ? "+" : "";
        deltaBadge.textContent = sign + delta.toFixed(1);
        if (delta > 0) deltaBadge.className = "pred-delta positive";
        else if (delta < 0) deltaBadge.className = "pred-delta negative";
        else deltaBadge.className = "pred-delta neutral";

        confidencePill.textContent = confidenceEs(data.confidence);
        confidencePill.className = "pred-pill " + confidenceCls(data.confidence);

        if (data.risk_flag) {
            riskFlag.style.display = "block";
        } else {
            riskFlag.style.display = "none";
        }
    }

    var farms = await fetchJSON("/api/farms");
    if (farms) {
        farms.forEach(function (f) {
            var opt = document.createElement("option");
            opt.value = f.id;
            opt.textContent = f.name;
            farmSelect.appendChild(opt);
        });
    }

    farmSelect.addEventListener("change", async function () {
        fieldSelect.innerHTML = '<option value="">Seleccione un campo...</option>';
        fieldSelect.disabled = true;
        content.style.display = "none";
        emptyMsg.style.display = "none";
        var farmId = farmSelect.value;
        if (!farmId) return;
        var fields = await fetchJSON("/api/farms/" + farmId + "/fields");
        if (fields && fields.length) {
            fields.forEach(function (fl) {
                var opt = document.createElement("option");
                opt.value = fl.id;
                opt.textContent = fl.name;
                fieldSelect.appendChild(opt);
            });
            fieldSelect.disabled = false;
        }
    });

    fieldSelect.addEventListener("change", async function () {
        content.style.display = "none";
        emptyMsg.style.display = "none";
        var farmId = farmSelect.value;
        var fieldId = fieldSelect.value;
        if (!farmId || !fieldId) return;
        var data = await fetchJSON("/api/farms/" + farmId + "/fields/" + fieldId + "/health-prediction");
        render(data);
    });
})();
