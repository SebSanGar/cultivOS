/* ── cultivOS Guided Tour — tour.js ── */
/* Lightweight tooltip-based tour for FODECIJAL reviewers.
   Cross-page state via sessionStorage. No dependencies. */

const TOUR_KEY = 'cultivosTour';

const TOUR_PAGES = {
    dashboard: {
        path: '/',
        steps: [
            {
                target: '.stats-strip',
                title: 'Metricas Generales',
                body: 'Vista rapida de granjas, campos, salud promedio y hectareas totales bajo monitoreo.',
                position: 'bottom'
            },
            {
                target: '#farm-grid',
                title: 'Granjas Registradas',
                body: 'Cada tarjeta muestra una granja con su municipio, cultivos y puntaje de salud. Haga clic en una granja para ver sus campos.',
                position: 'top'
            },
            {
                target: 'nav',
                title: 'Navegacion',
                body: 'Desde aqui puede acceder a granjas y fertilizantes. Ahora iremos a ver el detalle de un campo.',
                position: 'bottom'
            }
        ]
    },
    campo: {
        path: '/campo',
        steps: [
            {
                target: '.field-header',
                fallback: 'h1',
                title: 'Detalle del Campo',
                body: 'Aqui se muestra el nombre, cultivo, y estado de salud actual del campo seleccionado.',
                position: 'bottom'
            },
            {
                target: '.sensor-section',
                fallback: '.field-content',
                title: 'Datos de Sensores',
                body: 'NDVI, termico, suelo y clima — cada sensor tiene su historial con graficas de tendencia. Los datos vienen de vuelos de dron y estaciones meteorologicas.',
                position: 'top'
            },
            {
                target: '.treatment-timeline',
                fallback: '.field-content',
                title: 'Historial de Tratamientos',
                body: 'Registro de tratamientos organicos aplicados: composta, micorriza, bocashi. Cerebro mide el impacto real en salud antes y despues.',
                position: 'top'
            }
        ]
    },
    intel: {
        path: '/intel',
        steps: [
            {
                target: '.intel-header',
                fallback: 'h1',
                title: 'Panel de Inteligencia',
                body: 'Cerebro agrega datos de todas las granjas para generar analisis cruzados: efectividad de tratamientos, puntajes regenerativos, comparaciones entre granjas.',
                position: 'bottom'
            },
            {
                target: '.intel-section',
                fallback: 'main',
                title: 'Analisis Regenerativo',
                body: 'Aqui se muestra la efectividad de tratamientos organicos, carbono en suelo, y el puntaje regenerativo por campo. Todo basado en datos reales de sensor.',
                position: 'top'
            }
        ]
    },
    conocimiento: {
        path: '/conocimiento',
        steps: [
            {
                target: '.knowledge-header',
                fallback: 'h1',
                title: 'Base de Conocimiento',
                body: 'Fertilizantes organicos, metodos ancestrales, tipos de cultivo y enfermedades — todo documentado y ligado al motor de recomendaciones de Cerebro.',
                position: 'bottom'
            },
            {
                target: '.knowledge-cards',
                fallback: 'main',
                title: 'Conocimiento Ancestral + Cientifico',
                body: '21+ metodos regenerativos documentados. Cada metodo incluye preparacion, dosis, cultivos compatibles y beneficios para el suelo. Cerebro usa esta base para recomendar tratamientos.',
                position: 'top'
            }
        ]
    }
};

const PAGE_ORDER = ['dashboard', 'campo', 'intel', 'conocimiento'];

/* ── State management ── */

function getTourState() {
    try {
        const raw = sessionStorage.getItem(TOUR_KEY);
        return raw ? JSON.parse(raw) : null;
    } catch { return null; }
}

function saveTourState(state) {
    sessionStorage.setItem(TOUR_KEY, JSON.stringify(state));
}

function clearTourState() {
    sessionStorage.removeItem(TOUR_KEY);
}

/* ── Detect current page ── */

function detectCurrentPage() {
    const path = window.location.pathname;
    if (path === '/' || path === '/index.html') return 'dashboard';
    if (path === '/campo' || path === '/field.html') return 'campo';
    if (path === '/intel' || path === '/intel.html') return 'intel';
    if (path === '/conocimiento' || path === '/knowledge.html') return 'conocimiento';
    return null;
}

/* ── DOM helpers ── */

function findTarget(step) {
    let el = document.querySelector(step.target);
    if (!el && step.fallback) el = document.querySelector(step.fallback);
    return el;
}

function createOverlay() {
    // Remove existing
    removeOverlay();

    const overlay = document.createElement('div');
    overlay.id = 'tour-overlay';
    overlay.className = 'tour-overlay';
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) exitTour();
    });
    document.body.appendChild(overlay);
    return overlay;
}

function removeOverlay() {
    const existing = document.getElementById('tour-overlay');
    if (existing) existing.remove();
    const tip = document.getElementById('tour-tooltip');
    if (tip) tip.remove();
    const hl = document.querySelector('.tour-highlight');
    if (hl) hl.classList.remove('tour-highlight');
}

function positionTooltip(tooltip, targetEl, position) {
    const rect = targetEl.getBoundingClientRect();
    const scrollY = window.scrollY || window.pageYOffset;
    const scrollX = window.scrollX || window.pageXOffset;

    // Default to below target
    let top, left;
    if (position === 'bottom') {
        top = rect.bottom + scrollY + 12;
        left = rect.left + scrollX + rect.width / 2;
    } else {
        top = rect.top + scrollY - 12;
        left = rect.left + scrollX + rect.width / 2;
    }

    tooltip.style.position = 'absolute';
    tooltip.style.top = top + 'px';
    tooltip.style.left = left + 'px';
    tooltip.style.transform = position === 'bottom' ? 'translateX(-50%)' : 'translateX(-50%) translateY(-100%)';

    // Ensure tooltip stays on screen
    requestAnimationFrame(function() {
        const tipRect = tooltip.getBoundingClientRect();
        if (tipRect.left < 8) tooltip.style.left = (8 + tipRect.width / 2) + 'px';
        if (tipRect.right > window.innerWidth - 8) tooltip.style.left = (window.innerWidth - 8 - tipRect.width / 2) + 'px';
    });
}

/* ── Render step ── */

function renderTourStep(pageKey, stepIndex) {
    const page = TOUR_PAGES[pageKey];
    if (!page) return;
    const step = page.steps[stepIndex];
    if (!step) return;

    removeOverlay();
    createOverlay();

    const targetEl = findTarget(step);
    if (targetEl) {
        targetEl.classList.add('tour-highlight');
        targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    // Calculate total steps across all pages
    const pageIdx = PAGE_ORDER.indexOf(pageKey);
    let totalSteps = 0;
    let currentGlobal = 0;
    for (let i = 0; i < PAGE_ORDER.length; i++) {
        const p = TOUR_PAGES[PAGE_ORDER[i]];
        if (i < pageIdx) currentGlobal += p.steps.length;
        totalSteps += p.steps.length;
    }
    currentGlobal += stepIndex + 1;

    const isFirst = pageIdx === 0 && stepIndex === 0;
    const isLastOnPage = stepIndex === page.steps.length - 1;
    const isLastPage = pageIdx === PAGE_ORDER.length - 1;
    const isLast = isLastOnPage && isLastPage;

    const tooltip = document.createElement('div');
    tooltip.id = 'tour-tooltip';
    tooltip.className = 'tour-tooltip';
    tooltip.innerHTML = `
        <div class="tour-tooltip-header">
            <span class="tour-tooltip-counter">Paso ${currentGlobal} de ${totalSteps}</span>
            <button class="tour-tooltip-close" onclick="exitTour()" title="Salir del tour">&times;</button>
        </div>
        <div class="tour-tooltip-title">${step.title}</div>
        <div class="tour-tooltip-body">${step.body}</div>
        <div class="tour-tooltip-nav">
            <button class="tour-tooltip-btn tour-btn-prev" onclick="prevTourStep()" ${isFirst ? 'disabled' : ''}>Anterior</button>
            <button class="tour-tooltip-btn tour-btn-next" onclick="${isLast ? 'exitTour()' : 'nextTourStep()'}">
                ${isLast ? 'Finalizar' : isLastOnPage ? 'Siguiente pagina' : 'Siguiente'}
            </button>
        </div>
    `;
    document.body.appendChild(tooltip);

    if (targetEl) {
        // Small delay for scroll to finish
        setTimeout(function() { positionTooltip(tooltip, targetEl, step.position); }, 300);
    } else {
        // No target found — center tooltip
        tooltip.style.position = 'fixed';
        tooltip.style.top = '50%';
        tooltip.style.left = '50%';
        tooltip.style.transform = 'translate(-50%, -50%)';
    }
}

/* ── Navigation ── */

function startTour() {
    const state = { page: 'dashboard', step: 0, active: true };
    saveTourState(state);
    const currentPage = detectCurrentPage();
    if (currentPage === 'dashboard') {
        renderTourStep('dashboard', 0);
    } else {
        window.location.href = '/';
    }
}

function nextTourStep() {
    const state = getTourState();
    if (!state || !state.active) return;

    const page = TOUR_PAGES[state.page];
    if (!page) return;

    if (state.step < page.steps.length - 1) {
        // Next step on same page
        state.step++;
        saveTourState(state);
        renderTourStep(state.page, state.step);
    } else {
        // Move to next page
        const pageIdx = PAGE_ORDER.indexOf(state.page);
        if (pageIdx < PAGE_ORDER.length - 1) {
            const nextPage = PAGE_ORDER[pageIdx + 1];
            state.page = nextPage;
            state.step = 0;
            saveTourState(state);
            window.location.href = TOUR_PAGES[nextPage].path;
        } else {
            exitTour();
        }
    }
}

function prevTourStep() {
    const state = getTourState();
    if (!state || !state.active) return;

    if (state.step > 0) {
        state.step--;
        saveTourState(state);
        renderTourStep(state.page, state.step);
    } else {
        // Move to previous page
        const pageIdx = PAGE_ORDER.indexOf(state.page);
        if (pageIdx > 0) {
            const prevPage = PAGE_ORDER[pageIdx - 1];
            const prevSteps = TOUR_PAGES[prevPage].steps.length;
            state.page = prevPage;
            state.step = prevSteps - 1;
            saveTourState(state);
            window.location.href = TOUR_PAGES[prevPage].path;
        }
    }
}

function exitTour() {
    removeOverlay();
    clearTourState();
}

/* ── Auto-resume on page load ── */

function resumeTourOnLoad() {
    const state = getTourState();
    if (!state || !state.active) return;

    const currentPage = detectCurrentPage();
    if (currentPage === state.page) {
        // Small delay to let the page render its content
        setTimeout(function() {
            renderTourStep(state.page, state.step);
        }, 500);
    }
}

// Resume tour when page loads (if tour is active)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', resumeTourOnLoad);
} else {
    // DOMContentLoaded already fired — use a delay for dynamic content
    setTimeout(resumeTourOnLoad, 600);
}
