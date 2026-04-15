(function () {
    var sel = document.getElementById("fodecijal-coop-select");
    var content = document.getElementById("fodecijal-content");
    var empty = document.getElementById("fodecijal-empty");

    function fetchJSON(url) {
        return fetch(url).then(function (r) {
            if (!r.ok) return null;
            return r.json();
        }).catch(function () { return null; });
    }

    function fmt(v) {
        if (v === null || v === undefined) return "--";
        var n = Number(v);
        return isFinite(n) ? n.toFixed(0) : "--";
    }

    function colorClass(score) {
        if (score >= 70) return "green";
        if (score >= 40) return "amber";
        return "red";
    }

    function gradeText(score) {
        if (score >= 80) return { text: "Listo", cls: "listo" };
        if (score >= 60) return { text: "Avanzado", cls: "avanzado" };
        if (score >= 40) return { text: "En progreso", cls: "progreso" };
        return { text: "Inicial", cls: "inicial" };
    }

    function loadCoops() {
        fetchJSON("/api/cooperatives").then(function (data) {
            if (!data) return;
            var list = Array.isArray(data) ? data : data.cooperatives || [];
            list.forEach(function (c) {
                var opt = document.createElement("option");
                opt.value = c.id;
                opt.textContent = c.name || "Cooperativa " + c.id;
                sel.appendChild(opt);
            });
        });
    }

    function loadReadiness(coopId) {
        fetchJSON("/api/cooperatives/" + coopId + "/fodecijal-readiness").then(function (data) {
            if (!data) {
                content.style.display = "none";
                empty.style.display = "";
                empty.textContent = "Sin datos de preparacion FODECIJAL para esta cooperativa.";
                return;
            }

            content.style.display = "";
            empty.style.display = "none";

            var score = data.overall_score || 0;
            document.getElementById("fodecijal-readiness-score").textContent = fmt(score);

            var ring = document.getElementById("fodecijal-ring");
            ring.className = "fod-ring " + colorClass(score);

            var grade = gradeText(score);
            var gradeEl = document.getElementById("fodecijal-grade");
            gradeEl.textContent = grade.text;
            gradeEl.className = "fod-grade " + grade.cls;

            (data.sub_scores || []).forEach(function (s) {
                var pctEl = document.getElementById("pct-" + s.name);
                var barEl = document.getElementById("bar-" + s.name);
                var evEl = document.getElementById("ev-" + s.name);
                if (pctEl) pctEl.textContent = fmt(s.score) + "%";
                if (barEl) {
                    barEl.style.width = Math.min(100, Math.max(0, s.score)) + "%";
                    barEl.className = "fod-bar-fill " + colorClass(s.score);
                }
                if (evEl) evEl.textContent = s.evidence_es || "";
            });
        });
    }

    sel.addEventListener("change", function () {
        if (!sel.value) {
            content.style.display = "none";
            empty.style.display = "";
            empty.textContent = "Seleccione una cooperativa para ver la preparacion FODECIJAL.";
            return;
        }
        loadReadiness(sel.value);
    });

    loadCoops();
})();
