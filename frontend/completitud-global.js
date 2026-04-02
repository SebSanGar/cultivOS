/* Global data completeness dashboard — /completitud-global */
(function () {
    "use strict";

    var allData = [];

    function fetchJSON(url) {
        return fetch(url).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
    }
    function esc(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

    function scoreColor(pct) {
        if (pct >= 80) return "#22c55e";
        if (pct >= 50) return "#eab308";
        return "#ef4444";
    }

    function cellIcon(has) {
        return has
            ? '<span style="color:#22c55e;font-weight:700;">Si</span>'
            : '<span style="color:#ef4444;font-weight:700;">No</span>';
    }

    async function loadData() {
        var data = await fetchJSON("/api/intel/data-completeness-global");
        if (!data || !data.farms) {
            document.getElementById("cg-empty").style.display = "";
            document.getElementById("cg-table-container").style.display = "none";
            updateStats(0, 0, 0, 0);
            return;
        }

        allData = data.farms;
        populateStateFilter(allData);
        renderAll(allData);
    }

    function populateStateFilter(farms) {
        var sel = document.getElementById("cg-state-filter");
        var states = [];
        farms.forEach(function (f) {
            if (f.state && states.indexOf(f.state) === -1) states.push(f.state);
        });
        states.sort();
        states.forEach(function (s) {
            var opt = document.createElement("option");
            opt.value = s;
            opt.textContent = s;
            sel.appendChild(opt);
        });
    }

    window.filterByState = function () {
        var state = document.getElementById("cg-state-filter").value;
        var filtered = state ? allData.filter(function (f) { return f.state === state; }) : allData;
        renderAll(filtered);
    };

    function renderAll(farms) {
        var emptyEl = document.getElementById("cg-empty");
        var tableEl = document.getElementById("cg-table-container");

        if (!farms || farms.length === 0) {
            emptyEl.style.display = "";
            tableEl.style.display = "none";
            updateStats(0, 0, 0, 0);
            return;
        }

        emptyEl.style.display = "none";
        tableEl.style.display = "";

        var avg = Math.round(farms.reduce(function (s, f) { return s + f.farm_score; }, 0) / farms.length);
        var complete = farms.filter(function (f) { return f.farm_score >= 100; }).length;
        var gaps = farms.filter(function (f) { return f.farm_score < 100; }).length;
        updateStats(farms.length, avg, complete, gaps);

        var tbody = document.getElementById("cg-table-body");
        tbody.innerHTML = farms.map(function (f) {
            var color = scoreColor(f.farm_score);
            return '<tr style="border-bottom:1px solid #222;">' +
                '<td style="padding:8px 12px;color:#eee;font-weight:600;">' + esc(f.farm_name) + '</td>' +
                '<td style="padding:8px 12px;color:#999;">' + esc(f.state || "") + '</td>' +
                '<td style="padding:8px 12px;text-align:center;">' + cellIcon(f.has_soil) + '</td>' +
                '<td style="padding:8px 12px;text-align:center;">' + cellIcon(f.has_ndvi) + '</td>' +
                '<td style="padding:8px 12px;text-align:center;">' + cellIcon(f.has_thermal) + '</td>' +
                '<td style="padding:8px 12px;text-align:center;">' + cellIcon(f.has_treatments) + '</td>' +
                '<td style="padding:8px 12px;text-align:center;">' + cellIcon(f.has_weather) + '</td>' +
                '<td style="padding:8px 12px;text-align:right;font-weight:800;color:' + color + ';">' + Math.round(f.farm_score) + '%</td>' +
                '</tr>';
        }).join("");
    }

    function updateStats(farms, avg, complete, gaps) {
        document.getElementById("cg-stat-farms").textContent = farms;
        var avgEl = document.getElementById("cg-stat-avg");
        avgEl.textContent = avg + "%";
        avgEl.style.color = scoreColor(avg);
        document.getElementById("cg-stat-complete").textContent = complete;
        document.getElementById("cg-stat-gaps").textContent = gaps;
    }

    loadData();
})();
