/* resiliencia.js — field crop resilience score (#234) */

(function () {
    const farmSel = document.getElementById("res-farm-select");
    const fieldSel = document.getElementById("res-field-select");
    const content = document.getElementById("res-content");
    const noData = document.getElementById("res-no-data");
    const scoreEl = document.getElementById("res-score");
    const scoreRing = document.getElementById("res-score-ring");
    const gradePill = document.getElementById("res-grade-pill");
    const interpEl = document.getElementById("res-interpretation");

    const barHealth = document.getElementById("res-bar-health");
    const barSoilPh = document.getElementById("res-bar-soil-ph");
    const barWaterStress = document.getElementById("res-bar-water-stress");
    const barDiseaseRisk = document.getElementById("res-bar-disease-risk");
    const valHealth = document.getElementById("res-val-health");
    const valSoilPh = document.getElementById("res-val-soil-ph");
    const valWaterStress = document.getElementById("res-val-water-stress");
    const valDiseaseRisk = document.getElementById("res-val-disease-risk");

    async function fetchJSON(url) {
        try {
            const r = await fetch(url);
            if (!r.ok) return null;
            return await r.json();
        } catch { return null; }
    }

    function gradeInfo(score) {
        if (score >= 80) return { text: "Excelente", cls: "grade-excelente", ring: "#22c55e" };
        if (score >= 60) return { text: "Buena", cls: "grade-buena", ring: "#10b981" };
        if (score >= 40) return { text: "Regular", cls: "grade-regular", ring: "#f59e0b" };
        return { text: "Vulnerable", cls: "grade-vulnerable", ring: "#ef4444" };
    }

    function setBar(barEl, valEl, value) {
        if (value === null || value === undefined) {
            barEl.style.width = "0%";
            valEl.textContent = "Sin datos";
            return;
        }
        const pct = Math.max(0, Math.min(100, value));
        barEl.style.width = pct + "%";
        valEl.textContent = pct.toFixed(1);
    }

    async function loadFarms() {
        const farms = await fetchJSON("/api/farms/");
        if (!farms) return;
        farms.forEach(function (f) {
            const opt = document.createElement("option");
            opt.value = f.id;
            opt.textContent = f.name;
            farmSel.appendChild(opt);
        });
    }

    async function loadFields(farmId) {
        fieldSel.innerHTML = '<option value="">Seleccione un campo</option>';
        fieldSel.disabled = true;
        if (!farmId) return;
        const fields = await fetchJSON("/api/farms/" + farmId + "/fields");
        if (!fields) return;
        fields.forEach(function (f) {
            const opt = document.createElement("option");
            opt.value = f.id;
            opt.textContent = f.name;
            fieldSel.appendChild(opt);
        });
        fieldSel.disabled = false;
    }

    async function loadResilience(farmId, fieldId) {
        content.style.display = "none";
        noData.style.display = "none";
        if (!farmId || !fieldId) return;

        const data = await fetchJSON("/api/farms/" + farmId + "/fields/" + fieldId + "/resilience-score");
        if (!data || data.resilience_score === null || data.resilience_score === undefined) {
            noData.style.display = "block";
            return;
        }

        const score = data.resilience_score;
        const g = gradeInfo(score);

        scoreEl.textContent = score.toFixed(1);
        scoreRing.style.borderColor = g.ring;

        gradePill.textContent = g.text;
        gradePill.className = "grade-pill " + g.cls;

        const c = data.components || {};
        setBar(barHealth, valHealth, c.health);
        setBar(barSoilPh, valSoilPh, c.soil_ph);
        setBar(barWaterStress, valWaterStress, c.water_stress);
        setBar(barDiseaseRisk, valDiseaseRisk, c.disease_risk);

        interpEl.textContent = data.interpretation_es || "";

        content.style.display = "block";
    }

    farmSel.addEventListener("change", function () {
        loadFields(farmSel.value);
        content.style.display = "none";
        noData.style.display = "none";
    });

    fieldSel.addEventListener("change", function () {
        loadResilience(farmSel.value, fieldSel.value);
    });

    loadFarms();
})();
