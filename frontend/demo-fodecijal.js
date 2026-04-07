/* demo-fodecijal.js — Step completion tracking for FODECIJAL guided demo */

(function () {
    'use strict';

    var TOTAL_STEPS = 8;
    var STORAGE_KEY = 'cultivOS_demo_fodecijal_completed';

    function getCompleted() {
        try {
            var stored = localStorage.getItem(STORAGE_KEY);
            return stored ? JSON.parse(stored) : [];
        } catch (e) {
            return [];
        }
    }

    function saveCompleted(completed) {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(completed));
        } catch (e) {
            // localStorage not available — state is ephemeral
        }
    }

    function updateProgress(completed) {
        var count = completed.length;
        var pct = Math.round((count / TOTAL_STEPS) * 100);

        var bar = document.getElementById('progress-bar');
        var text = document.getElementById('progress-text');
        var completedEl = document.getElementById('completed-count');
        var remainingEl = document.getElementById('remaining-count');

        if (bar) bar.style.width = pct + '%';
        if (text) text.textContent = count + ' de ' + TOTAL_STEPS + ' pasos completados';
        if (completedEl) completedEl.textContent = count;
        if (remainingEl) remainingEl.textContent = (TOTAL_STEPS - count);

        // Mark completed cards
        for (var i = 1; i <= TOTAL_STEPS; i++) {
            var card = document.getElementById('step-' + i);
            if (!card) continue;
            if (completed.indexOf(i) >= 0) {
                card.classList.add('completed');
                var check = card.querySelector('.step-check');
                if (check) check.innerHTML = '&#10003;';
            } else {
                card.classList.remove('completed');
                var check2 = card.querySelector('.step-check');
                if (check2) check2.textContent = i;
            }
        }
    }

    window.toggleStep = function (stepNum) {
        var completed = getCompleted();
        var idx = completed.indexOf(stepNum);
        if (idx >= 0) {
            completed.splice(idx, 1);
        } else {
            completed.push(stepNum);
        }
        saveCompleted(completed);
        updateProgress(completed);
    };

    // Initialize on page load
    document.addEventListener('DOMContentLoaded', function () {
        var completed = getCompleted();
        updateProgress(completed);
    });
})();
