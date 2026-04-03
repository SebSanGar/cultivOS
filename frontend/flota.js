/* cultivOS — Flota de Drones (/flota)
   Fleet status dashboard with drone cards, battery levels, and operational stats.
   Data is static (hardware fleet specs from CLAUDE.md) — future: API-driven status updates.
*/

(function () {
    "use strict";

    const FLEET = [
        {
            id: "mavic_multispectral",
            name: "DJI Mavic 3 Multispectral",
            purpose: "Mapeo NDVI",
            battery: 85,
            flightHours: 342,
            coverageHa: 200,
            costMXN: 106000,
            status: "operativo",
            lastMission: "2026-04-01",
            nextMaintenance: "2026-04-15"
        },
        {
            id: "mavic_thermal",
            name: "DJI Mavic 3 Thermal",
            purpose: "Deteccion termica",
            battery: 72,
            flightHours: 198,
            coverageHa: 150,
            costMXN: 130000,
            status: "operativo",
            lastMission: "2026-03-30",
            nextMaintenance: "2026-04-20"
        },
        {
            id: "agras_t100",
            name: "DJI Agras T100",
            purpose: "Aspersion de precision",
            battery: 93,
            flightHours: 87,
            coverageHa: 75,
            costMXN: 556000,
            status: "operativo",
            lastMission: "2026-03-28",
            nextMaintenance: "2026-04-10"
        }
    ];

    function updateStats() {
        var totalDrones = FLEET.length;
        var operational = FLEET.filter(function (d) { return d.status === "operativo"; }).length;
        var totalCoverage = FLEET.reduce(function (sum, d) { return sum + d.coverageHa; }, 0);
        var totalInvestment = FLEET.reduce(function (sum, d) { return sum + d.costMXN; }, 0);

        var el;
        el = document.getElementById("drones-total");
        if (el) el.textContent = totalDrones;
        el = document.getElementById("drones-operativos");
        if (el) el.textContent = operational;
        el = document.getElementById("cobertura-total");
        if (el) el.textContent = totalCoverage + " ha/dia";
        el = document.getElementById("inversion-total");
        if (el) el.textContent = "$" + totalInvestment.toLocaleString("es-MX") + " MXN";
    }

    updateStats();
})();
