/* Fotos de Campo — crop photo upload + analysis gallery */

(async function () {
    const farmSelect = document.getElementById("farmSelect");
    const fieldSelect = document.getElementById("fieldSelect");
    const uploadZone = document.getElementById("uploadZone");
    const fileInput = document.getElementById("fileInput");
    const photoGrid = document.getElementById("photoGrid");
    const statsStrip = document.getElementById("statsStrip");
    const emptyState = document.getElementById("emptyState");

    let currentFarmId = null;
    let currentFieldId = null;

    async function fetchJSON(url) {
        const r = await fetch(url);
        if (!r.ok) return null;
        return r.json();
    }

    // Load farms
    const farmsResp = await fetchJSON("/api/farms");
    const farms = farmsResp ? (farmsResp.data || farmsResp) : [];
    farms.forEach(function (f) {
        const opt = document.createElement("option");
        opt.value = f.id;
        opt.textContent = f.name;
        farmSelect.appendChild(opt);
    });
    if (farms.length === 0) {
        emptyState.style.display = "block";
        emptyState.textContent = "No hay granjas registradas.";
    }

    farmSelect.addEventListener("change", async function () {
        currentFarmId = this.value;
        currentFieldId = null;
        fieldSelect.innerHTML = '<option value="">-- Seleccionar parcela --</option>';
        fieldSelect.disabled = true;
        uploadZone.style.display = "none";
        statsStrip.style.display = "none";
        photoGrid.innerHTML = "";
        if (!currentFarmId) return;

        const fields = await fetchJSON("/api/farms/" + currentFarmId + "/fields");
        if (fields && fields.length > 0) {
            fieldSelect.disabled = false;
            fields.forEach(function (f) {
                const opt = document.createElement("option");
                opt.value = f.id;
                opt.textContent = f.name + (f.crop_type ? " (" + f.crop_type + ")" : "");
                fieldSelect.appendChild(opt);
            });
        }
    });

    fieldSelect.addEventListener("change", function () {
        currentFieldId = this.value;
        if (currentFieldId) {
            uploadZone.style.display = "block";
            loadPhotos();
        } else {
            uploadZone.style.display = "none";
            statsStrip.style.display = "none";
            photoGrid.innerHTML = "";
        }
    });

    // Upload
    uploadZone.addEventListener("click", function () { fileInput.click(); });
    uploadZone.addEventListener("dragover", function (e) { e.preventDefault(); });
    uploadZone.addEventListener("drop", function (e) {
        e.preventDefault();
        if (e.dataTransfer.files.length > 0) uploadFile(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener("change", function () {
        if (this.files.length > 0) uploadFile(this.files[0]);
    });

    async function uploadFile(file) {
        if (!currentFarmId || !currentFieldId) return;
        var fd = new FormData();
        fd.append("file", file);
        uploadZone.querySelector("div").textContent = "Subiendo...";
        try {
            var resp = await fetch("/api/farms/" + currentFarmId + "/fields/" + currentFieldId + "/photos", {
                method: "POST",
                body: fd,
            });
            if (resp.ok) {
                loadPhotos();
            } else {
                var err = await resp.json().catch(function () { return {}; });
                alert("Error: " + (err.detail || "No se pudo subir la foto"));
            }
        } finally {
            uploadZone.querySelector("div").textContent = "Haz clic o arrastra una foto aqui para analizar";
            fileInput.value = "";
        }
    }

    async function loadPhotos() {
        if (!currentFarmId || !currentFieldId) return;
        var photos = await fetchJSON("/api/farms/" + currentFarmId + "/fields/" + currentFieldId + "/photos");
        if (!photos) photos = [];

        // Stats
        statsStrip.style.display = "flex";
        document.getElementById("totalPhotos").textContent = photos.length;
        var healthy = 0, stressed = 0, greenSum = 0;
        photos.forEach(function (p) {
            if (p.analysis) {
                if (p.analysis.classification === "healthy_vegetation") healthy++;
                if (p.analysis.classification === "stressed_vegetation") stressed++;
                greenSum += p.analysis.green_ratio || 0;
            }
        });
        document.getElementById("healthyCount").textContent = healthy;
        document.getElementById("stressedCount").textContent = stressed;
        document.getElementById("avgGreen").textContent = photos.length > 0 ? (greenSum / photos.length * 100).toFixed(1) + "%" : "--";

        // Render
        photoGrid.innerHTML = "";
        if (photos.length === 0) {
            emptyState.style.display = "block";
            emptyState.textContent = "No hay fotos para esta parcela. Sube una foto para comenzar el analisis.";
            return;
        }
        emptyState.style.display = "none";

        photos.forEach(function (p) {
            var card = document.createElement("div");
            card.className = "photo-card";

            var classLabel = p.analysis ? classificationLabel(p.analysis.classification) : { text: "Sin analisis", cls: "class-mixed" };

            var html = '<div class="photo-header">'
                + "<h4>" + esc(p.filename) + "</h4>"
                + '<span class="date">' + new Date(p.uploaded_at).toLocaleDateString("es-MX") + "</span>"
                + "</div>"
                + '<span class="classification-badge ' + classLabel.cls + '">' + classLabel.text + "</span>";

            if (p.analysis) {
                // Color bar
                html += '<div class="color-bar">';
                (p.analysis.dominant_colors || []).forEach(function (c) {
                    html += '<span style="width:' + c.percentage + "%;background:rgb(" + c.color.join(",") + ')"></span>';
                });
                html += "</div>";
                html += '<div class="analysis-row"><span class="label">Brillo promedio</span><span>' + p.analysis.avg_brightness + "</span></div>";
                html += '<div class="analysis-row"><span class="label">Ratio verde</span><span>' + (p.analysis.green_ratio * 100).toFixed(1) + "%</span></div>";
            }
            html += '<div style="margin-top:0.5rem;text-align:right;">'
                + '<button class="btn-delete" data-id="' + p.id + '">Eliminar</button></div>';
            card.innerHTML = html;
            photoGrid.appendChild(card);
        });

        // Delete handlers
        photoGrid.querySelectorAll(".btn-delete").forEach(function (btn) {
            btn.addEventListener("click", async function () {
                var pid = this.getAttribute("data-id");
                await fetch("/api/farms/" + currentFarmId + "/fields/" + currentFieldId + "/photos/" + pid, { method: "DELETE" });
                loadPhotos();
            });
        });
    }

    function classificationLabel(cls) {
        var map = {
            healthy_vegetation: { text: "Vegetacion Sana", cls: "class-healthy" },
            stressed_vegetation: { text: "Vegetacion Estresada", cls: "class-stressed" },
            bare_soil: { text: "Suelo Desnudo", cls: "class-bare" },
            mixed: { text: "Mixto", cls: "class-mixed" },
        };
        return map[cls] || { text: cls, cls: "class-mixed" };
    }

    function esc(s) {
        var d = document.createElement("div");
        d.textContent = s || "";
        return d.innerHTML;
    }
})();
