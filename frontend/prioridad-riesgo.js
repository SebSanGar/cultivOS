(async function () {
    const farmSelect = document.getElementById("risk-farm-select");
    const content = document.getElementById("risk-content");
    const emptyMsg = document.getElementById("risk-empty");
    const heroCard = document.getElementById("risk-hero-card");
    const heroName = document.getElementById("risk-hero-name");
    const heroScore = document.getElementById("risk-hero-score");
    const fieldCards = document.getElementById("risk-field-cards");

    async function fetchJSON(url) {
        const r = await fetch(url);
        if (!r.ok) return null;
        return r.json();
    }

    function urgencyClass(score) {
        if (score > 60) return "urgency-red";
        if (score >= 30) return "urgency-amber";
        return "urgency-green";
    }

    function renderCards(items) {
        fieldCards.innerHTML = "";
        if (!items || items.length === 0) {
            content.style.display = "none";
            heroCard.style.display = "none";
            emptyMsg.textContent = "No hay datos de riesgo para esta finca.";
            emptyMsg.style.display = "block";
            return;
        }
        content.style.display = "block";
        emptyMsg.style.display = "none";

        const top = items[0];
        heroCard.style.display = "block";
        heroName.textContent = "Campo #" + top.field_id + " — " + top.crop_type;
        heroScore.textContent = top.priority_score.toFixed(1);

        items.forEach(function (item) {
            const cls = urgencyClass(item.priority_score);
            const card = document.createElement("div");
            card.className = "risk-card " + cls;
            card.innerHTML =
                '<div class="risk-card-name">Campo #' + item.field_id + '</div>' +
                '<div class="risk-card-crop">' + item.crop_type + '</div>' +
                '<div class="risk-card-stats">' +
                '  <div><div class="risk-stat-label">Puntuación</div><div class="risk-stat-value risk-score-big">' + item.priority_score.toFixed(1) + '</div></div>' +
                '  <div><div class="risk-stat-label">Estrés</div><div class="risk-stat-value">' + item.stress_score.toFixed(1) + '</div></div>' +
                '  <div><div class="risk-stat-label">Días sin tratar</div><div class="risk-stat-value">' + item.days_since_treatment + '</div></div>' +
                '</div>' +
                '<div class="risk-recommendation">' + item.recommendation_es + '</div>';
            fieldCards.appendChild(card);
        });
    }

    const farms = await fetchJSON("/api/farms");
    if (farms) {
        farms.forEach(function (f) {
            const opt = document.createElement("option");
            opt.value = f.id;
            opt.textContent = f.name;
            farmSelect.appendChild(opt);
        });
    }

    farmSelect.addEventListener("change", async function () {
        const farmId = farmSelect.value;
        if (!farmId) {
            content.style.display = "none";
            heroCard.style.display = "none";
            emptyMsg.textContent = "Seleccione una finca para ver la prioridad de riesgo por campo.";
            emptyMsg.style.display = "block";
            return;
        }
        const data = await fetchJSON("/api/farms/" + farmId + "/risk-priority");
        renderCards(data);
    });
})();
