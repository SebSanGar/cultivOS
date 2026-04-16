/* Ranking de Miembros — /ranking-miembros (#236)
   Consumes GET /api/cooperatives/{coop_id}/member-ranking */

(async function () {
    var coopSelect = document.getElementById("rank-coop-select");
    var cardsContainer = document.getElementById("rank-cards");
    var noData = document.getElementById("rank-no-data");

    var medals = { 1: "\uD83E\uDD47", 2: "\uD83E\uDD48", 3: "\uD83E\uDD49" };

    // Load cooperatives
    try {
        var res = await fetch("/api/cooperatives");
        if (res.ok) {
            var coops = await res.json();
            coops.forEach(function (c) {
                var o = document.createElement("option");
                o.value = c.id;
                o.textContent = c.name;
                coopSelect.appendChild(o);
            });
        }
    } catch (_) { /* ignore */ }

    coopSelect.addEventListener("change", loadRanking);

    async function loadRanking() {
        var coopId = coopSelect.value;
        cardsContainer.innerHTML = "";
        noData.style.display = "none";

        if (!coopId) return;

        try {
            var res = await fetch("/api/cooperatives/" + coopId + "/member-ranking");
            if (!res.ok) {
                noData.style.display = "block";
                return;
            }
            var d = await res.json();

            if (!d.members || d.members.length === 0) {
                noData.textContent = "No hay miembros en esta cooperativa.";
                noData.style.display = "block";
                return;
            }

            d.members.forEach(function (m) {
                var card = document.createElement("div");
                card.className = "farm-card";
                if (m.rank <= 3) card.classList.add("rank-" + m.rank);

                var rankEl = document.createElement("div");
                if (medals[m.rank]) {
                    rankEl.className = "medal";
                    rankEl.textContent = medals[m.rank];
                } else {
                    rankEl.className = "rank-num";
                    rankEl.textContent = "#" + m.rank;
                }

                var info = document.createElement("div");
                info.className = "farm-info";

                var name = document.createElement("div");
                name.className = "farm-name";
                name.textContent = m.farm_name;

                var stats = document.createElement("div");
                stats.className = "farm-stats";
                stats.innerHTML =
                    '<span class="stat">Salud: <span class="stat-value">' + m.health_avg.toFixed(1) + '</span></span>' +
                    '<span class="stat">Regen: <span class="stat-value">' + m.regen_score.toFixed(1) + '</span></span>' +
                    '<span class="stat">Respuesta: <span class="stat-value">' + (m.alert_response_rate * 100).toFixed(0) + '%</span></span>';

                info.appendChild(name);
                info.appendChild(stats);

                var score = document.createElement("div");
                score.style.textAlign = "right";
                var scoreVal = document.createElement("div");
                scoreVal.className = "composite-score";
                scoreVal.textContent = m.composite_score.toFixed(1);
                var scoreLabel = document.createElement("div");
                scoreLabel.className = "composite-label";
                scoreLabel.textContent = "Puntaje";
                score.appendChild(scoreVal);
                score.appendChild(scoreLabel);

                card.appendChild(rankEl);
                card.appendChild(info);
                card.appendChild(score);
                cardsContainer.appendChild(card);
            });
        } catch (_) {
            noData.style.display = "block";
        }
    }
})();
