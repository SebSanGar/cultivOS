/* Farmer dollar-savings view — /impacto-agricultor (English-first, currency-neutral).
   Binds to GET /api/farms/{id}/farmer-impact. Honest: ranges read as "about $X",
   never a $0 headline, estimate badge travels with the number. */

(async function () {
    "use strict";
    var farmSelect = document.getElementById("farmSelect");
    var fieldCards = document.getElementById("field-cards");

    async function fetchJSON(url) {
        try {
            var token = localStorage.getItem("cultivOS_token");
            var headers = {};
            if (token) headers["Authorization"] = "Bearer " + token;
            var r = await fetch(url, { headers: headers });
            if (!r.ok) return null;
            return await r.json();
        } catch (e) { return null; }
    }

    function esc(s) { var d = document.createElement("div"); d.textContent = s == null ? "" : s; return d.innerHTML; }

    // Neutral money: "$" + thousands separators, no currency code, no decimals.
    function money(n) { return "$" + Math.round(n).toLocaleString("en-US"); }

    function countUp(el, target) {
        var start = 0, dur = 900, t0 = null;
        function step(ts) {
            if (!t0) t0 = ts;
            var p = Math.min((ts - t0) / dur, 1);
            var eased = 1 - Math.pow(1 - p, 3);
            el.textContent = money(Math.round(target * eased));
            if (p < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    }

    // Load farms, auto-select the first so the page shows real data immediately.
    var farms = await fetchJSON("/api/farms?page_size=100");
    var items = (farms && (farms.items || farms)) || [];
    farmSelect.innerHTML = "";
    if (!items.length) {
        farmSelect.innerHTML = '<option value="">No farms yet</option>';
        showEmptyHero("Add a farm and we'll start showing what you save.");
        return;
    }
    items.forEach(function (f) {
        var opt = document.createElement("option");
        opt.value = f.id; opt.textContent = f.name;
        farmSelect.appendChild(opt);
    });

    farmSelect.addEventListener("change", function () {
        if (farmSelect.value) loadImpact(farmSelect.value);
    });

    await loadImpact(items[0].id);

    async function loadImpact(farmId) {
        var data = await fetchJSON("/api/farms/" + farmId + "/farmer-impact");
        if (!data) { showEmptyHero("We couldn't load this farm just now."); return; }

        var savings = Number(data.estimated_savings_mxn || 0);
        var treatments = Number(data.treatments_applied || 0);

        // Honesty: no $0 headline. Without enough data, show a forward-looking line.
        if (savings <= 0 || treatments <= 0) {
            showEmptyHero("Here you'll see how much you save as we look after your farm.");
        } else {
            document.getElementById("impact-hero").classList.remove("is-empty");
            var amountEl = document.getElementById("hero-amount");
            amountEl.classList.remove("impact-hero-amount--soft");
            document.querySelector(".impact-hero-label").textContent = "You've saved about";
            document.getElementById("hero-subline").textContent = "since we started looking after your farm";
            document.getElementById("hero-badge").hidden = false;
            countUp(amountEl, savings);
        }

        // Supporting strip
        setText("sup-days", data.days_since_onboard != null ? data.days_since_onboard : "—");
        setText("sup-fields", data.total_fields != null ? data.total_fields : "—");
        setText("sup-treatments", treatments);
        var imp = data.avg_health_improvement_pct;
        setText("sup-health", imp != null ? (imp > 0 ? "+" : "") + imp + " pts" : "—");

        renderFieldCards(data.fields || []);
    }

    function showEmptyHero(msg) {
        document.getElementById("impact-hero").classList.add("is-empty");
        document.querySelector(".impact-hero-label").textContent = msg;
        var amountEl = document.getElementById("hero-amount");
        amountEl.textContent = "";
        amountEl.classList.add("impact-hero-amount--soft");
        document.getElementById("hero-subline").textContent = "";
        document.getElementById("hero-badge").hidden = true;
        ["sup-days", "sup-fields", "sup-treatments", "sup-health"].forEach(function (id) { setText(id, "—"); });
        renderFieldCards([]);
    }

    function setText(id, v) { var el = document.getElementById(id); if (el) el.textContent = v; }

    // green ≥70, yellow 40–70, red <40
    function band(score) {
        if (score == null) return { cls: "muted", word: "No reading yet" };
        if (score >= 70) return { cls: "green", word: "Doing well" };
        if (score >= 40) return { cls: "yellow", word: "Needs attention" };
        return { cls: "red", word: "Needs help now" };
    }

    function renderFieldCards(fields) {
        fieldCards.innerHTML = "";
        if (!fields || !fields.length) {
            fieldCards.innerHTML = '<p class="impact-muted">No fields yet — add one to see how it changes.</p>';
            return;
        }
        fields.forEach(function (f) {
            var b = band(f.latest_score);
            var delta = f.health_delta;
            var deltaPill = delta != null
                ? '<span class="delta-pill ' + (delta > 0 ? "up" : delta < 0 ? "down" : "flat") + '">' + (delta > 0 ? "+" : "") + delta + '</span>'
                : "";
            var card = document.createElement("div");
            card.className = "field-impact-card";
            card.innerHTML = [
                '<div class="field-impact-head">',
                '  <span class="semaforo-dot ' + b.cls + '"></span>',
                '  <div class="field-impact-name">' + esc(f.field_name) + '</div>',
                f.crop_type ? '  <span class="field-impact-crop">' + esc(f.crop_type) + '</span>' : '',
                '</div>',
                '<div class="field-impact-status">' + b.word + '</div>',
                '<div class="before-after">',
                '  <span class="ba-swatch ' + band(f.first_score).cls + '" title="before"></span>',
                '  <span class="ba-arrow">→</span>',
                '  <span class="ba-swatch ' + band(f.latest_score).cls + '" title="now"></span>',
                '  ' + deltaPill,
                '</div>',
            ].join("\n");
            fieldCards.appendChild(card);
        });
    }
})();
