(function () {
    const sel = document.getElementById("coop-evidence-select");
    const content = document.getElementById("coop-evidence-content");
    const empty = document.getElementById("coop-evidence-empty");

    async function fetchJSON(url) {
        try {
            const r = await fetch(url);
            if (!r.ok) return null;
            return await r.json();
        } catch (e) {
            return null;
        }
    }

    function fmt(value, digits) {
        if (value === null || value === undefined) return "--";
        const n = Number(value);
        if (!isFinite(n)) return "--";
        return n.toFixed(digits == null ? 1 : digits);
    }

    function clamp(v, lo, hi) {
        return Math.max(lo, Math.min(hi, v));
    }

    function setPillar(barId, labelId, pctValue) {
        const bar = document.getElementById(barId);
        const label = document.getElementById(labelId);
        if (pctValue === null || pctValue === undefined || !isFinite(pctValue)) {
            if (bar) bar.style.width = "0%";
            if (label) label.textContent = "--";
            return;
        }
        const pct = clamp(Number(pctValue), 0, 100);
        if (bar) bar.style.width = pct.toFixed(0) + "%";
        if (label) label.textContent = pct.toFixed(0) + " / 100";
    }

    function setOutbreakPill(level) {
        const el = document.getElementById("coop-evidence-outbreak");
        if (!el) return;
        const value = (level || "none").toLowerCase();
        el.className = "evid-pill " + (["high", "medium", "low", "none"].includes(value) ? value : "none");
        const labels = { high: "Alto", medium: "Medio", low: "Bajo", none: "Ninguno" };
        el.textContent = "Riesgo de brote: " + (labels[value] || "Desconocido");
    }

    async function loadCoopList() {
        const data = await fetchJSON("/api/cooperatives");
        const rows = Array.isArray(data) ? data : (data && data.cooperatives) || [];
        sel.innerHTML = '<option value="">Seleccione una cooperativa...</option>';
        rows.forEach(function (c) {
            const opt = document.createElement("option");
            opt.value = c.id;
            opt.textContent = c.name || ("Cooperativa " + c.id);
            sel.appendChild(opt);
        });
    }

    async function loadEvidence(coopId) {
        if (!coopId) {
            content.style.display = "none";
            empty.style.display = "block";
            empty.textContent = "Seleccione una cooperativa para ver la evidencia.";
            return;
        }
        const data = await fetchJSON("/api/cooperatives/" + coopId + "/evidence-pack");
        if (!data) {
            content.style.display = "none";
            empty.style.display = "block";
            empty.textContent = "No hay datos de evidencia disponibles para esta cooperativa.";
            return;
        }

        document.getElementById("coop-evidence-readiness").textContent = fmt(data.readiness_score, 0);
        document.getElementById("coop-evidence-health").textContent = fmt(data.portfolio_health_avg, 1);
        document.getElementById("coop-evidence-regen").textContent = fmt(data.regen_adoption_pct, 0);
        document.getElementById("coop-evidence-co2e").textContent = fmt(data.total_co2e_sequestered_t, 1);
        document.getElementById("coop-evidence-diversity").textContent = fmt(data.shannon_diversity_index, 2);

        setPillar("coop-evidence-pillar-readiness", "coop-evidence-pillar-readiness-label", data.readiness_score);
        setPillar("coop-evidence-pillar-health", "coop-evidence-pillar-health-label", data.portfolio_health_avg);
        setPillar("coop-evidence-pillar-regen", "coop-evidence-pillar-regen-label", data.regen_adoption_pct);

        setOutbreakPill(data.outbreak_risk_level);

        document.getElementById("coop-evidence-strength").textContent = data.top_strength_es || "Sin datos.";
        document.getElementById("coop-evidence-weakness").textContent = data.top_weakness_es || "Sin datos.";

        content.style.display = "block";
        empty.style.display = "none";
    }

    sel.addEventListener("change", function () { loadEvidence(sel.value); });
    loadCoopList();
})();
