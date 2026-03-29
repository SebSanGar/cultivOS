/* TEK ancestral knowledge validation page — /tek */
(function () {
    "use strict";

    var emptyEl = document.getElementById("tek-empty");
    var contentEl = document.getElementById("tek-content");
    var methodsEl = document.getElementById("tek-methods");
    var filterEl = document.getElementById("tek-filter");

    var allMethods = [];

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

    window.loadTEKData = function () {
        emptyEl.style.display = "none";
        contentEl.style.display = "";
        methodsEl.innerHTML = '<div style="color:#888;">Cargando...</div>';

        fetchJSON("/api/intel/tek-validation").then(function (data) {
            if (!data || !data.methods || data.methods.length === 0) {
                contentEl.style.display = "none";
                emptyEl.style.display = "";
                emptyEl.textContent = "Sin datos de validacion TEK — no hay retroalimentacion de agricultores registrada.";
                resetStats();
                return;
            }
            allMethods = data.methods;
            updateStats(allMethods);
            renderMethods(allMethods);
        });
    };

    window.filterMethods = function () {
        var value = filterEl.value;
        var filtered;
        if (value === "high") {
            filtered = allMethods.filter(function (m) { return m.trust_score > 70; });
        } else if (value === "medium") {
            filtered = allMethods.filter(function (m) { return m.trust_score >= 40 && m.trust_score <= 70; });
        } else if (value === "low") {
            filtered = allMethods.filter(function (m) { return m.trust_score < 40; });
        } else {
            filtered = allMethods;
        }
        renderMethods(filtered);
    };

    function resetStats() {
        document.getElementById("tek-total-methods").textContent = "--";
        document.getElementById("tek-avg-trust").textContent = "--";
        document.getElementById("tek-total-feedback").textContent = "--";
        document.getElementById("tek-top-method").textContent = "--";
    }

    function updateStats(methods) {
        document.getElementById("tek-total-methods").textContent = methods.length;

        var totalTrust = 0;
        var totalFeedback = 0;
        var topMethod = null;
        var topScore = -1;

        methods.forEach(function (m) {
            totalTrust += m.trust_score;
            totalFeedback += m.total_feedback;
            if (m.trust_score > topScore) {
                topScore = m.trust_score;
                topMethod = m.method_name;
            }
        });

        var avgTrust = methods.length > 0 ? (totalTrust / methods.length).toFixed(1) : "0";
        document.getElementById("tek-avg-trust").textContent = avgTrust;
        document.getElementById("tek-total-feedback").textContent = totalFeedback;
        document.getElementById("tek-top-method").textContent = topMethod || "--";
    }

    function trustColor(score) {
        if (score >= 70) return "#22c55e";
        if (score >= 40) return "#eab308";
        return "#ef4444";
    }

    function trustLabel(score) {
        if (score >= 70) return "Alta";
        if (score >= 40) return "Media";
        return "Baja";
    }

    function renderMethods(methods) {
        methodsEl.innerHTML = "";

        if (methods.length === 0) {
            methodsEl.innerHTML = '<div class="intel-card" style="color:#888;text-align:center;">Sin metodos que coincidan con el filtro seleccionado.</div>';
            return;
        }

        methods.forEach(function (m) {
            var color = trustColor(m.trust_score);
            var label = trustLabel(m.trust_score);
            var barWidth = Math.min(m.trust_score, 100);

            var card = document.createElement("div");
            card.className = "intel-card tek-method-card";
            card.style.borderLeft = "3px solid " + color;

            var starsHtml = "";
            var fullStars = Math.floor(m.average_rating);
            for (var i = 0; i < 5; i++) {
                starsHtml += '<span style="color:' + (i < fullStars ? "#eab308" : "#444") + ';">&#9733;</span>';
            }

            card.innerHTML =
                '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">' +
                    '<span style="color:#eee;font-weight:600;font-size:0.95rem;">' + esc(m.method_name) + '</span>' +
                    '<span style="background:' + color + '22;color:' + color + ';padding:0.15rem 0.5rem;border-radius:4px;font-size:0.75rem;font-weight:600;">' + label + '</span>' +
                '</div>' +

                /* Trust score bar */
                '<div style="margin-bottom:0.75rem;">' +
                    '<div style="display:flex;justify-content:space-between;font-size:0.8rem;color:#888;margin-bottom:0.25rem;">' +
                        '<span>Confianza</span>' +
                        '<span style="color:' + color + ';font-weight:600;">' + m.trust_score.toFixed(1) + '</span>' +
                    '</div>' +
                    '<div style="background:#222;border-radius:4px;height:8px;overflow:hidden;">' +
                        '<div style="background:' + color + ';height:100%;width:' + barWidth + '%;border-radius:4px;transition:width 0.3s;"></div>' +
                    '</div>' +
                '</div>' +

                /* Rating stars */
                '<div style="margin-bottom:0.5rem;font-size:1rem;">' + starsHtml +
                    '<span style="color:#888;font-size:0.8rem;margin-left:0.5rem;">' + m.average_rating.toFixed(1) + '/5</span>' +
                '</div>' +

                /* Feedback counts */
                '<div style="display:flex;gap:1rem;margin-bottom:0.5rem;">' +
                    '<div style="display:flex;align-items:center;gap:0.3rem;">' +
                        '<span style="color:#22c55e;font-weight:600;font-size:0.9rem;">' + m.positive_count + '</span>' +
                        '<span style="color:#888;font-size:0.8rem;">positivas</span>' +
                    '</div>' +
                    '<div style="display:flex;align-items:center;gap:0.3rem;">' +
                        '<span style="color:#ef4444;font-weight:600;font-size:0.9rem;">' + m.negative_count + '</span>' +
                        '<span style="color:#888;font-size:0.8rem;">negativas</span>' +
                    '</div>' +
                    '<div style="display:flex;align-items:center;gap:0.3rem;">' +
                        '<span style="color:#aaa;font-weight:600;font-size:0.9rem;">' + m.total_feedback + '</span>' +
                        '<span style="color:#888;font-size:0.8rem;">total</span>' +
                    '</div>' +
                '</div>' +

                /* Usage ratio bar */
                '<div style="font-size:0.8rem;color:#888;">' +
                    'Efectividad: ' +
                    '<span style="color:#22c55e;">' + m.positive_count + '</span>/' +
                    '<span style="color:#aaa;">' + m.total_feedback + '</span> reportes positivos' +
                '</div>';

            methodsEl.appendChild(card);
        });
    }
})();
