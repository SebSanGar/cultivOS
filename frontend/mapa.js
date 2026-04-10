/* -- cultivOS Interactive Field Map -- mapa.js -- */

const API = '/api';
let mapInstance = null;
let allFarmData = [];
let mapLayers = [];
let viewMode = 'health'; // 'health' | 'risk'
let riskDataByFarm = {}; // farm_id → [{field_id, risk_score, dominant_factor, lat, lon}]

function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

async function fetchJSON(path) {
    try {
        const resp = await fetch(API + path);
        if (!resp.ok) return null;
        return await resp.json();
    } catch {
        return null;
    }
}

function healthColor(score) {
    if (score == null) return '#666';
    if (score > 70) return '#00c896';
    if (score >= 40) return '#f0b429';
    return '#e63946';
}

function healthLabel(score) {
    if (score == null) return 'Sin datos';
    if (score > 70) return 'Saludable';
    if (score >= 40) return 'Alerta';
    return 'Critico';
}

function riskColor(score) {
    if (score == null) return '#666';
    if (score > 60) return '#e63946';
    if (score >= 30) return '#f0b429';
    return '#00c896';
}

function riskLabel(score) {
    if (score == null) return 'Sin datos';
    if (score > 60) return 'Riesgo Alto';
    if (score >= 30) return 'Riesgo Medio';
    return 'Riesgo Bajo';
}

function dominantLabel(factor) {
    const labels = {health: 'Salud', weather: 'Clima', disease: 'Enfermedad', thermal: 'Termal'};
    return factor ? (labels[factor] || factor) : '--';
}

window.toggleViewMode = function() {
    viewMode = viewMode === 'health' ? 'risk' : 'health';
    var btn = document.getElementById('view-toggle-btn');
    if (btn) btn.textContent = viewMode === 'health' ? 'Ver Riesgo' : 'Ver Salud';
    var lh = document.getElementById('legend-health');
    var lr = document.getElementById('legend-risk');
    if (lh) lh.style.display = viewMode === 'health' ? 'contents' : 'none';
    if (lr) lr.style.display = viewMode === 'risk' ? 'contents' : 'none';
    var val = document.getElementById('map-farm-filter').value;
    if (!val) {
        renderMap(allFarmData);
    } else {
        var filtered = allFarmData.filter(function(entry) { return String(entry.farm.id) === val; });
        renderMap(filtered);
    }
};

// -- Initialize map --
function initMap() {
    mapInstance = L.map('map-container', {
        zoomControl: true,
        attributionControl: false
    }).setView([20.66, -103.35], 10); // Center on Jalisco

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: 'OpenStreetMap'
    }).addTo(mapInstance);
}

// -- Load all data --
async function loadMapData() {
    const farms = await fetchJSON('/farms');
    if (!farms || farms.length === 0) {
        document.getElementById('map-empty').style.display = 'block';
        document.getElementById('map-stat-farms').textContent = '0';
        document.getElementById('map-stat-fields').textContent = '0';
        document.getElementById('map-stat-hectares').textContent = '0';
        return;
    }

    // Populate farm filter
    const filter = document.getElementById('map-farm-filter');
    farms.forEach(function(farm) {
        const opt = document.createElement('option');
        opt.value = farm.id;
        opt.textContent = farm.name;
        filter.appendChild(opt);
    });

    // Fetch fields and health for each farm in parallel
    const farmFieldPromises = farms.map(async function(farm) {
        const fields = await fetchJSON('/farms/' + farm.id + '/fields');
        if (!fields) return { farm: farm, fields: [], healthScores: {} };

        // Fetch latest health score for each field
        const healthPromises = fields.map(async function(field) {
            const health = await fetchJSON('/farms/' + farm.id + '/fields/' + field.id + '/health');
            const latest = health && health.length > 0 ? health[health.length - 1] : null;
            return { fieldId: field.id, score: latest ? latest.score : null };
        });
        const healthResults = await Promise.all(healthPromises);
        const healthMap = {};
        healthResults.forEach(function(h) { healthMap[h.fieldId] = h.score; });

        return { farm: farm, fields: fields, healthScores: healthMap };
    });

    allFarmData = await Promise.all(farmFieldPromises);

    // Fetch risk map for each farm in parallel
    await Promise.all(farms.map(async function(farm) {
        const risk = await fetchJSON('/farms/' + farm.id + '/fields/risk-map');
        if (risk) {
            riskDataByFarm[farm.id] = risk;
        }
    }));

    renderMap(allFarmData);
}

// -- Render map markers and polygons --
function renderMap(farmData) {
    // Clear existing layers
    mapLayers.forEach(function(layer) { mapInstance.removeLayer(layer); });
    mapLayers = [];

    let totalFarms = 0;
    let totalFields = 0;
    let totalHectares = 0;
    let healthSum = 0;
    let healthCount = 0;
    const bounds = [];

    farmData.forEach(function(entry) {
        const farm = entry.farm;
        const fields = entry.fields;
        const healthScores = entry.healthScores;

        // Farm marker (if coordinates exist)
        if (farm.location_lat && farm.location_lon) {
            totalFarms++;
            const pos = [farm.location_lat, farm.location_lon];
            bounds.push(pos);

            const marker = L.circleMarker(pos, {
                radius: 10,
                color: '#4da6ff',
                fillColor: '#4da6ff',
                fillOpacity: 0.7,
                weight: 2
            }).addTo(mapInstance);

            marker.bindPopup(
                '<strong>' + esc(farm.name) + '</strong><br>' +
                esc(farm.municipality || '') + ', ' + esc(farm.state || 'Jalisco') + '<br>' +
                (farm.total_hectares || 0) + ' ha<br>' +
                '<a href="/?farm=' + farm.id + '">Ver granja</a>'
            );

            marker.on('click', function() {
                updateInfoPanel(farm, fields, healthScores);
            });

            mapLayers.push(marker);
        }

        // Build risk lookup for this farm
        var farmRisk = riskDataByFarm[farm.id] || [];
        var riskByField = {};
        farmRisk.forEach(function(r) { riskByField[r.field_id] = r; });

        // Field polygons / risk markers
        fields.forEach(function(field) {
            totalFields++;
            totalHectares += field.hectares || 0;
            const score = healthScores[field.id];
            if (score != null) {
                healthSum += score;
                healthCount++;
            }

            var riskItem = riskByField[field.id];

            if (viewMode === 'risk') {
                // Risk mode: draw a circle marker at field lat/lon with risk color
                var rLat = riskItem && riskItem.lat != null ? riskItem.lat : (farm.location_lat || null);
                var rLon = riskItem && riskItem.lon != null ? riskItem.lon : (farm.location_lon || null);
                if (rLat != null && rLon != null) {
                    var rScore = riskItem ? riskItem.risk_score : null;
                    var color = riskColor(rScore);
                    var marker = L.circleMarker([rLat, rLon], {
                        radius: 9,
                        color: color,
                        fillColor: color,
                        fillOpacity: 0.85,
                        weight: 2
                    }).addTo(mapInstance);

                    marker.bindPopup(
                        '<strong>' + esc(field.name) + '</strong><br>' +
                        'Cultivo: ' + esc(field.crop_type || '--') + '<br>' +
                        'Area: ' + (field.hectares || 0) + ' ha<br>' +
                        'Riesgo: ' + (rScore != null ? rScore.toFixed(0) + ' — ' + riskLabel(rScore) : 'Sin datos') + '<br>' +
                        (riskItem && riskItem.dominant_factor ? 'Factor: ' + dominantLabel(riskItem.dominant_factor) + '<br>' : '') +
                        '<a href="/campo?farm=' + farm.id + '&field=' + field.id + '">Ver campo</a>'
                    );

                    bounds.push([rLat, rLon]);
                    mapLayers.push(marker);
                }
            } else if (field.boundary_coordinates && field.boundary_coordinates.length >= 3) {
                // Health mode: draw polygon colored by health
                var latlngs = field.boundary_coordinates.map(function(coord) {
                    return [coord[1], coord[0]];
                });

                var hColor = healthColor(score);
                var polygon = L.polygon(latlngs, {
                    color: hColor,
                    weight: 2,
                    fillOpacity: 0.25,
                    fillColor: hColor
                }).addTo(mapInstance);

                polygon.bindPopup(
                    '<strong>' + esc(field.name) + '</strong><br>' +
                    'Cultivo: ' + esc(field.crop_type || '--') + '<br>' +
                    'Area: ' + (field.hectares || 0) + ' ha<br>' +
                    'Salud: ' + (score != null ? Math.round(score) + ' (' + healthLabel(score) + ')' : 'Sin datos') + '<br>' +
                    '<a href="/campo?farm=' + farm.id + '&field=' + field.id + '">Ver campo</a>'
                );

                latlngs.forEach(function(ll) { bounds.push(ll); });
                mapLayers.push(polygon);
            }
        });
    });

    // Update stats
    document.getElementById('map-stat-farms').textContent = totalFarms;
    document.getElementById('map-stat-fields').textContent = totalFields;
    document.getElementById('map-stat-hectares').textContent = totalHectares.toFixed(0);
    document.getElementById('map-stat-avg-health').textContent =
        healthCount > 0 ? Math.round(healthSum / healthCount) : '--';

    // Fit map to bounds
    if (bounds.length > 0) {
        mapInstance.fitBounds(bounds, { padding: [30, 30] });
    }

    // Show empty state if no farms have coordinates
    if (totalFarms === 0 && totalFields === 0) {
        document.getElementById('map-empty').style.display = 'block';
    }
}

// -- Update info panel --
function updateInfoPanel(farm, fields, healthScores) {
    var panel = document.getElementById('map-info-panel');
    var fieldRows = fields.map(function(f) {
        var score = healthScores[f.id];
        var color = healthColor(score);
        return '<tr>' +
            '<td>' + esc(f.name) + '</td>' +
            '<td>' + esc(f.crop_type || '--') + '</td>' +
            '<td>' + (f.hectares || 0) + ' ha</td>' +
            '<td style="color:' + color + '">' + (score != null ? Math.round(score) : '--') + '</td>' +
            '</tr>';
    }).join('');

    panel.innerHTML =
        '<strong>' + esc(farm.name) + '</strong> — ' +
        esc(farm.municipality || '') + ', ' + esc(farm.state || 'Jalisco') +
        '<table style="width:100%;margin-top:0.5rem;border-collapse:collapse;">' +
        '<thead><tr style="border-bottom:1px solid rgba(255,255,255,0.1);text-align:left;">' +
        '<th>Parcela</th><th>Cultivo</th><th>Area</th><th>Salud</th></tr></thead>' +
        '<tbody>' + fieldRows + '</tbody></table>';
}

// -- Farm filter --
window.filterByFarm = function() {
    var val = document.getElementById('map-farm-filter').value;
    if (!val) {
        renderMap(allFarmData);
    } else {
        var filtered = allFarmData.filter(function(entry) {
            return String(entry.farm.id) === val;
        });
        renderMap(filtered);
    }
};

// -- Init --
(async function() {
    initMap();
    await loadMapData();
})();
