window.initCategoryFilters = function() {
  const container = document.getElementById("category-filters");
  if (!container) return;
  container.innerHTML = "";

  if (!window.oakData || !window.oakData.locations) return;

  const types = new Set(window.oakData.locations.map(l => l.type).filter(Boolean));

  types.forEach(cat => {
    const chip = document.createElement("button");
    chip.className = "category-chip";
    chip.textContent = cat;

    chip.addEventListener("click", () => {
      if (window.activeCategories.has(cat)) {
        window.activeCategories.delete(cat);
        chip.classList.remove("active");
      } else {
        window.activeCategories.add(cat);
        chip.classList.add("active");
      }
      window.renderMarkers();
    });

    container.appendChild(chip);
  });
};

window.initSeasonFilter = function() {
  const select = document.getElementById("season-filter");
  if (!select || !window.oakData || !window.oakData.seasons) return;

  select.innerHTML = "";
  const allOption = document.createElement("option");
  allOption.value = "all";
  allOption.textContent = "All seasons";
  select.appendChild(allOption);

  window.oakData.seasons.forEach(s => {
    const option = document.createElement("option");
    option.value = s.season.toString();
    option.textContent = `Season ${s.season}`;
    select.appendChild(option);
  });

  select.addEventListener("change", e => {
    window.setActiveSeason(e.target.value);
    window.renderMarkers();
  });
};

window.initYearSlider = function() {
  const slider = document.getElementById("timeline-slider");
  const label = document.getElementById("timeline-year");
  if (!slider || !label) return;

  slider.min = 1700;
  slider.max = new Date().getFullYear();
  slider.value = slider.max;

  window.setActiveYear("all");
  label.textContent = "All years";

  slider.addEventListener("input", e => {
    const val = e.target.value;
    window.setActiveYear(val);
    label.textContent = `Up to ${val}`;
    window.renderMarkers();
  });
};

window.initSearchInputs = function() {
  const textInput = document.getElementById("search-input");
  if (textInput) {
    textInput.addEventListener("input", e => {
      window.setTextSearchQuery(e.target.value.trim());
      window.renderMarkers();
    });
  }

  const globalInput = document.getElementById("global-search");
  if (globalInput) {
    let searchTimeout;

    globalInput.addEventListener("input", e => {
      const query = e.target.value.trim();
      window.setGlobalSearchQuery(query);
      window.renderMarkers();

      // Clear previous timeout
      clearTimeout(searchTimeout);

      // Hide results if query is too short
      const resultsContainer = document.getElementById("search-results");
      if (query.length < 2) {
        if (resultsContainer) resultsContainer.style.display = "none";
        return;
      }

      // Debounce search results display
      searchTimeout = setTimeout(() => {
        displaySearchResults(query);
        if (query.length > 2) {
          window.zoomToFirstSearchMatch(query);
        }
      }, 300);
    });
  }
};

function displaySearchResults(query) {
  const results = window.searchLocationsWithFuse(query);
  const resultsContainer = document.getElementById("search-results");

  if (!resultsContainer) return;

  if (results.length === 0) {
    resultsContainer.style.display = "none";
    return;
  }

  // Show top 5 results
  const topResults = results.slice(0, 5);
  resultsContainer.innerHTML = topResults.map(result => {
    const location = result.location;
    return `
      <div class="search-result-item" data-location-id="${location.id || location.location_id}">
        <div class="search-result-title">${location.name}</div>
        <div class="search-result-meta">${location.type}</div>
      </div>
    `;
  }).join("");

  resultsContainer.style.display = "block";

  // Add click handlers
  resultsContainer.querySelectorAll('.search-result-item').forEach(item => {
    item.addEventListener('click', () => {
      const locationId = item.dataset.locationId;
      const location = window.oakData.locations.find(loc => (loc.id || loc.location_id) === locationId);
      if (location) {
        // Zoom to location
        window.zoomToFirstSearchMatch(location.name);
        // Hide results
        resultsContainer.style.display = "none";
      }
    });
  });
}
