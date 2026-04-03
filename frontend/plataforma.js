/* cultivOS — Plataforma Overview (/plataforma)
   Categorized grid of all platform pages with search and category filtering.
*/

(function () {
    "use strict";

    var searchInput = document.getElementById("search-input");
    var categoryFilter = document.getElementById("category-filter");

    function filterPages() {
        var query = (searchInput ? searchInput.value : "").toLowerCase();
        var category = categoryFilter ? categoryFilter.value : "all";
        var sections = document.querySelectorAll(".category-section");

        sections.forEach(function (section) {
            var sectionCategory = section.getAttribute("data-category");
            var categoryMatch = category === "all" || sectionCategory === category;

            if (!categoryMatch) {
                section.style.display = "none";
                return;
            }

            var cards = section.querySelectorAll(".page-card");
            var visibleCount = 0;

            cards.forEach(function (card) {
                var title = (card.querySelector(".page-card-title") || {}).textContent || "";
                var desc = (card.querySelector(".page-card-desc") || {}).textContent || "";
                var text = (title + " " + desc).toLowerCase();

                if (!query || text.indexOf(query) !== -1) {
                    card.style.display = "";
                    visibleCount++;
                } else {
                    card.style.display = "none";
                }
            });

            section.style.display = visibleCount > 0 ? "" : "none";
        });
    }

    // Bind events
    if (searchInput) {
        searchInput.addEventListener("input", filterPages);
    }
    if (categoryFilter) {
        categoryFilter.addEventListener("change", filterPages);
    }

    // Expose for inline onchange
    window.filterPages = filterPages;
})();
