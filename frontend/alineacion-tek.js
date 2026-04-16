/* /alineacion-tek — TEK sensor alignment page JS (#240) */

(async function () {
    const farmSel = document.getElementById("tek-farm-select");
    const fieldSel = document.getElementById("tek-field-select");
    const monthSel = document.getElementById("tek-month-select");
    const scoreEl = document.getElementById("tek-score");
    const ring = document.getElementById("tek-score-ring");
    const practicesEl = document.getElementById("tek-practices");

    // Set default month to current
    monthSel.value = String(new Date().getMonth() + 1);

    async function fetchJSON(url) {
        const r = await fetch(url);
        if (!r.ok) return null;
        return r.json();
    }

    // Load farms
    const farms = await fetchJSON("/api/farms");
    if (!farms || !farms.length) {
        farmSel.innerHTML = '<option value="">Sin datos</option>';
        return;
    }
    farmSel.innerHTML = '<option value="">Seleccione finca</option>' +
        farms.map(f => `<option value="${f.id}">${f.name}</option>`).join("");

    farmSel.addEventListener("change", async () => {
        const fid = farmSel.value;
        fieldSel.innerHTML = '<option value="">Cargando...</option>';
        practicesEl.innerHTML = "";
        scoreEl.textContent = "--";
        ring.style.borderColor = "";
        if (!fid) { fieldSel.innerHTML = '<option value="">Seleccione finca</option>'; return; }
        const fields = await fetchJSON(`/api/farms/${fid}/fields`);
        if (!fields || !fields.length) {
            fieldSel.innerHTML = '<option value="">Sin campos</option>';
            return;
        }
        fieldSel.innerHTML = '<option value="">Seleccione campo</option>' +
            fields.map(f => `<option value="${f.id}">${f.name || "Campo " + f.id}</option>`).join("");
    });

    async function loadAlignment() {
        const fid = farmSel.value;
        const flid = fieldSel.value;
        const month = monthSel.value;
        if (!fid || !flid) return;

        const data = await fetchJSON(`/api/farms/${fid}/fields/${flid}/tek-alignment?month=${month}`);
        if (!data) {
            scoreEl.textContent = "--";
            ring.style.borderColor = "";
            practicesEl.innerHTML = '<div class="no-data-msg">Sin datos de alineación TEK para este campo y mes.</div>';
            return;
        }

        const pct = data.alignment_score_pct;
        scoreEl.textContent = Math.round(pct) + "%";
        ring.style.borderColor = pct >= 70 ? "#22c55e" : pct >= 40 ? "#f59e0b" : "#ef4444";

        if (!data.practices || !data.practices.length) {
            practicesEl.innerHTML = '<div class="no-data-msg">Sin prácticas ancestrales para este mes.</div>';
            return;
        }

        practicesEl.innerHTML = data.practices.map(p => {
            const supported = p.sensor_support;
            const pillClass = supported ? "support-confirmed" : "support-nodata";
            const pillText = supported ? "Confirmado" : "Sin datos";
            return `<div class="practice-card">
                <h3>${esc(p.name)}</h3>
                <span class="support-pill ${pillClass}">${pillText}</span>
                ${p.timing_rationale ? `<div style="margin-top:0.5rem;font-size:0.85rem;">${esc(p.timing_rationale)}</div>` : ""}
                <div class="evidence">${esc(p.evidence_es)}</div>
            </div>`;
        }).join("");
    }

    fieldSel.addEventListener("change", loadAlignment);
    monthSel.addEventListener("change", loadAlignment);

    function esc(s) {
        if (!s) return "";
        const d = document.createElement("div");
        d.textContent = s;
        return d.innerHTML;
    }
})();
