(async function () {
    var farmSelect = document.getElementById("stress-farm-select");
    var fieldSelect = document.getElementById("stress-field-select");
    var content = document.getElementById("stress-content");
    var emptyMsg = document.getElementById("stress-empty");
    var bigNumber = document.getElementById("stress-big-number");
    var ringArc = document.getElementById("stress-ring-arc");
    var levelPill = document.getElementById("stress-level-pill");
    var recBox = document.getElementById("stress-recommendation");
    var waterFill = document.getElementById("gauge-water-fill");
    var waterVal = document.getElementById("gauge-water-value");
    var diseaseFill = document.getElementById("gauge-disease-fill");
    var diseaseVal = document.getElementById("gauge-disease-value");
    var thermalFill = document.getElementById("gauge-thermal-fill");
    var thermalVal = document.getElementById("gauge-thermal-value");

    var CIRC = 408.4;

    async function fetchJSON(url) {
        var r = await fetch(url);
        if (!r.ok) return null;
        return r.json();
    }

    function stressColor(val) {
        if (val >= 60) return "#ef4444";
        if (val >= 30) return "#f59e0b";
        return "#22c55e";
    }

    function pillClass(level) {
        var map = { none: "pill-none", low: "pill-low", moderate: "pill-moderate", high: "pill-high", critical: "pill-critical" };
        return map[level] || "pill-moderate";
    }

    function levelEs(level) {
        var map = { none: "Sin estrés", low: "Bajo", moderate: "Moderado", high: "Alto", critical: "Crítico" };
        return map[level] || level;
    }

    function renderStress(data) {
        if (!data) {
            content.style.display = "none";
            emptyMsg.textContent = "No hay datos de estrés para este campo.";
            emptyMsg.style.display = "block";
            return;
        }
        content.style.display = "block";
        emptyMsg.style.display = "none";

        var idx = data.stress_index;
        bigNumber.textContent = idx.toFixed(1);
        var color = stressColor(idx);
        ringArc.style.stroke = color;
        ringArc.style.strokeDashoffset = CIRC - (CIRC * idx / 100);

        levelPill.textContent = levelEs(data.stress_level);
        levelPill.className = "stress-pill " + pillClass(data.stress_level);

        var c = data.components;
        setGauge(waterFill, waterVal, c.water);
        setGauge(diseaseFill, diseaseVal, c.disease);
        setGauge(thermalFill, thermalVal, c.thermal);

        if (data.recommendation_es) {
            recBox.textContent = data.recommendation_es;
            recBox.style.display = "block";
        } else {
            recBox.style.display = "none";
        }
    }

    function setGauge(fill, valEl, val) {
        fill.style.width = Math.min(val, 100) + "%";
        fill.style.backgroundColor = stressColor(val);
        valEl.textContent = val.toFixed(1);
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
        var farmId = farmSelect.value;
        fieldSelect.innerHTML = '<option value="">Seleccione un campo...</option>';
        content.style.display = "none";
        if (!farmId) {
            fieldSelect.disabled = true;
            emptyMsg.textContent = "Seleccione una finca y un campo para ver el índice de estrés.";
            emptyMsg.style.display = "block";
            return;
        }
        var fields = await fetchJSON("/api/farms/" + farmId + "/fields");
        if (fields && fields.length) {
            fields.forEach(function (fl) {
                var opt = document.createElement("option");
                opt.value = fl.id;
                opt.textContent = fl.name || ("Campo #" + fl.id);
                fieldSelect.appendChild(opt);
            });
            fieldSelect.disabled = false;
        } else {
            fieldSelect.disabled = true;
        }
        emptyMsg.textContent = "Seleccione un campo para ver el índice de estrés.";
        emptyMsg.style.display = "block";
    });

    fieldSelect.addEventListener("change", async function () {
        var farmId = farmSelect.value;
        var fieldId = fieldSelect.value;
        if (!farmId || !fieldId) {
            content.style.display = "none";
            emptyMsg.textContent = "Seleccione un campo para ver el índice de estrés.";
            emptyMsg.style.display = "block";
            return;
        }
        var data = await fetchJSON("/api/farms/" + farmId + "/fields/" + fieldId + "/stress-index");
        renderStress(data);
    });
})();
