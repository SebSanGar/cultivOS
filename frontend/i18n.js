/* cultivOS — Lightweight client i18n (ES/EN) */

(function () {
    'use strict';

    var LS_KEY = 'cultivOS_lang';
    var DEFAULT_LANG = 'es';

    var dict = {
        es: {
            'nav.farms': 'Mis Parcelas',
            'nav.alerts': 'Alertas',
            'nav.knowledge': 'Conocimiento',
            'nav.whatsapp': 'WhatsApp',
            'nav.intel': 'Inteligencia',
            'nav.map': 'Mapa',
            'nav.flights': 'Vuelos',
            'nav.platform': 'Plataforma',
            'nav.status': 'Estado',
            'dash.title': 'Granjas',
            'dash.subtitle': 'Vista general de todas las granjas y su salud',
            'stat.farms': 'Granjas',
            'stat.fields': 'Campos',
            'stat.avgHealth': 'Salud Promedio',
            'stat.hectares': 'Hectareas Total',
            'dash.seedDemo': 'Cargar datos de ejemplo',
            'dash.guidedTour': 'Asistente guiado',
            'dash.portfolioReport': 'Descargar Reporte de Portafolio',
            'dash.newFarm': '+ Nueva Granja',
            'dash.loading': 'Cargando granjas...',
            'form.name': 'Nombre *',
            'form.owner': 'Propietario',
            'form.hectares': 'Hectareas',
            'form.municipality': 'Municipio',
            'form.state': 'Estado',
            'form.cancel': 'Cancelar',
            'form.createFarm': 'Crear Granja',
            'notif.title': 'Notificaciones',
            'notif.healthFloor': 'Salud minima (0-100)',
            'notif.ndviMin': 'NDVI minimo (0-1)',
            'notif.tempMax': 'Temperatura maxima (C)',
            'notif.save': 'Guardar',
            'alert.historyTitle': 'Historial de Alertas',
            'alert.loading': 'Cargando alertas...',
            'weather.title': 'Clima',
            'weather.humidity': 'Humedad',
            'weather.wind': 'Viento',
            'login.pageTitle': 'cultivOS — Iniciar Sesion',
            'login.subtitle': 'Inteligencia agricola de precision',
            'login.title': 'Iniciar Sesion',
            'login.username': 'Usuario',
            'login.password': 'Contrasena',
            'login.confirmPassword': 'Confirmar Contrasena',
            'login.role': 'Rol',
            'login.farm': 'Granja',
            'login.noFarm': 'Sin granja',
            'login.submit': 'Entrar',
            'login.noAccount': 'No tienes cuenta?',
            'login.register': 'Registrarse',
            'login.hasAccount': 'Ya tienes cuenta?',
            'login.signIn': 'Iniciar Sesion',
            'login.registerTitle': 'Registrarse',
            'login.registerSubmit': 'Crear Cuenta',
            'role.farmer': 'Agricultor',
            'role.researcher': 'Investigador',
            'user.logout': 'Salir',
            'toggle.agronomo': 'Vista agronomo',
            'toggle.farmer': 'Vista productor',
            'notif.historyTitle': 'Historial de Notificaciones',
            'notif.historySubtitle': 'Alertas y recomendaciones de todas las granjas',
            'notif.refresh': 'Actualizar',
            'field.cta': 'Que hago?',
            'knowledge.title': 'Base de Conocimiento'
        },
        en: {
            'nav.farms': 'My Plots',
            'nav.alerts': 'Alerts',
            'nav.knowledge': 'Knowledge',
            'nav.whatsapp': 'WhatsApp',
            'nav.intel': 'Intelligence',
            'nav.map': 'Map',
            'nav.flights': 'Flights',
            'nav.platform': 'Platform',
            'nav.status': 'Status',
            'dash.title': 'Farms',
            'dash.subtitle': 'Overview of all farms and their health',
            'stat.farms': 'Farms',
            'stat.fields': 'Fields',
            'stat.avgHealth': 'Avg Health',
            'stat.hectares': 'Total Hectares',
            'dash.seedDemo': 'Load demo data',
            'dash.guidedTour': 'Guided tour',
            'dash.portfolioReport': 'Download Portfolio Report',
            'dash.newFarm': '+ New Farm',
            'dash.loading': 'Loading farms...',
            'form.name': 'Name *',
            'form.owner': 'Owner',
            'form.hectares': 'Hectares',
            'form.municipality': 'Municipality',
            'form.state': 'State',
            'form.cancel': 'Cancel',
            'form.createFarm': 'Create Farm',
            'notif.title': 'Notifications',
            'notif.healthFloor': 'Min health (0-100)',
            'notif.ndviMin': 'Min NDVI (0-1)',
            'notif.tempMax': 'Max temperature (C)',
            'notif.save': 'Save',
            'alert.historyTitle': 'Alert History',
            'alert.loading': 'Loading alerts...',
            'weather.title': 'Weather',
            'weather.humidity': 'Humidity',
            'weather.wind': 'Wind',
            'login.pageTitle': 'cultivOS — Sign In',
            'login.subtitle': 'Precision agricultural intelligence',
            'login.title': 'Sign In',
            'login.username': 'Username',
            'login.password': 'Password',
            'login.confirmPassword': 'Confirm Password',
            'login.role': 'Role',
            'login.farm': 'Farm',
            'login.noFarm': 'No farm',
            'login.submit': 'Sign In',
            'login.noAccount': "Don't have an account?",
            'login.register': 'Register',
            'login.hasAccount': 'Already have an account?',
            'login.signIn': 'Sign In',
            'login.registerTitle': 'Register',
            'login.registerSubmit': 'Create Account',
            'role.farmer': 'Farmer',
            'role.researcher': 'Researcher',
            'user.logout': 'Log out',
            'toggle.agronomo': 'Agronomist view',
            'toggle.farmer': 'Farmer view',
            'notif.historyTitle': 'Notification History',
            'notif.historySubtitle': 'Alerts and recommendations from all farms',
            'notif.refresh': 'Refresh',
            'field.cta': 'What do I do?',
            'knowledge.title': 'Knowledge Base'
        }
    };

    function getLang() {
        return localStorage.getItem(LS_KEY) || DEFAULT_LANG;
    }

    function setLang(lang) {
        localStorage.setItem(LS_KEY, lang);
    }

    function t(key) {
        var lang = getLang();
        return (dict[lang] && dict[lang][key]) || (dict[DEFAULT_LANG] && dict[DEFAULT_LANG][key]) || key;
    }

    function applyAll() {
        var lang = getLang();
        var els = document.querySelectorAll('[data-i18n]');
        for (var i = 0; i < els.length; i++) {
            var key = els[i].getAttribute('data-i18n');
            var val = t(key);
            if (els[i].tagName === 'INPUT' || els[i].tagName === 'TEXTAREA') {
                els[i].setAttribute('placeholder', val);
            } else {
                els[i].textContent = val;
            }
        }
        var placeholders = document.querySelectorAll('[data-i18n-placeholder]');
        for (var j = 0; j < placeholders.length; j++) {
            var pk = placeholders[j].getAttribute('data-i18n-placeholder');
            placeholders[j].setAttribute('placeholder', t(pk));
        }
        updateToggleBtn();
    }

    function updateToggleBtn() {
        var lang = getLang();
        var toggleBtns = document.querySelectorAll('.nav-lang-toggle');
        for (var i = 0; i < toggleBtns.length; i++) {
            var esSpan = toggleBtns[i].querySelector('[data-lang="es"]');
            var enSpan = toggleBtns[i].querySelector('[data-lang="en"]');
            if (esSpan) esSpan.classList.toggle('active', lang === 'es');
            if (enSpan) enSpan.classList.toggle('active', lang === 'en');
        }
    }

    function switchLang(lang) {
        setLang(lang);
        applyAll();
    }

    function initToggle() {
        var toggleBtns = document.querySelectorAll('.nav-lang-toggle');
        for (var i = 0; i < toggleBtns.length; i++) {
            toggleBtns[i].addEventListener('click', function (e) {
                var target = e.target.closest('[data-lang]');
                if (target) {
                    switchLang(target.getAttribute('data-lang'));
                }
            });
        }
    }

    function init() {
        applyAll();
        initToggle();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    window.cultivOS_i18n = { t: t, switchLang: switchLang, getLang: getLang, applyAll: applyAll };
})();
