(function () {
    function initSearchableMultiSelect(root) {
        const searchInput = root.querySelector("[data-searchable-multi-select-input]");
        const dropdown = root.querySelector("[data-searchable-multi-select-dropdown]");
        const noResults = root.querySelector("[data-searchable-multi-select-no-results]");
        const options = Array.from(root.querySelectorAll("[data-searchable-multi-select-option]"));
        const optionRows = Array.from(root.querySelectorAll("[data-searchable-multi-select-option-row]"));
        const selectedDisplay = root.querySelector("[data-searchable-multi-select-selected]");

        if (!searchInput || !dropdown) return;

        function openDropdown() {
            dropdown.classList.add("show");
        }

        function closeDropdown() {
            dropdown.classList.remove("show");
        }

        function filterDropdownOptions() {
            const query = searchInput.value.trim().toLowerCase();
            let visibleCount = 0;

            optionRows.forEach(row => {
                const isVisible = row.dataset.searchText.toLowerCase().includes(query);
                row.classList.toggle("d-none", !isVisible);
                if (isVisible) visibleCount += 1;
            });

            if (noResults) {
                noResults.classList.toggle("d-none", visibleCount !== 0 || optionRows.length === 0);
            }
        }

        function showAllDropdownOptions() {
            optionRows.forEach(row => {
                row.classList.remove("d-none");
            });
            if (noResults) {
                noResults.classList.add("d-none");
            }
        }

        function updateSelectedOptions() {
            const selectedOptions = options.filter(option => option.checked);
            searchInput.value = selectedOptions.map(option => option.dataset.selectedLabel).join(", ");
            showAllDropdownOptions();

            if (!selectedDisplay) return;

            if (selectedOptions.length === 0) {
                selectedDisplay.classList.add("text-secondary");
                selectedDisplay.textContent = selectedDisplay.dataset.emptyText;
                return;
            }

            selectedDisplay.classList.remove("text-secondary");
            selectedDisplay.replaceChildren();
            selectedOptions.forEach(option => {
                const badge = document.createElement("span");
                badge.className = "badge bg-light text-dark border me-1 mb-1";
                badge.textContent = option.dataset.selectedLabel;
                selectedDisplay.appendChild(badge);
            });
        }

        searchInput.addEventListener("focus", openDropdown);
        searchInput.addEventListener("input", function () {
            openDropdown();
            filterDropdownOptions();
        });
        root.addEventListener("click", openDropdown);
        document.addEventListener("click", function (event) {
            if (!root.contains(event.target)) {
                closeDropdown();
            }
        });
        options.forEach(option => {
            option.addEventListener("change", updateSelectedOptions);
        });

        filterDropdownOptions();
        updateSelectedOptions();
    }

    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll("[data-searchable-multi-select]").forEach(initSearchableMultiSelect);
    });
}());
