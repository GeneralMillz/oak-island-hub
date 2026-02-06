// data.js
// Centralized loader for all dashboard data.
// This version preserves all existing behavior and adds a semantic data loader
// for events, measurements, people, theories, and location mentions.

function isPiMode() {
  return typeof window.PI_MODE === "boolean" ? window.PI_MODE : false;
}

window.initMapDataLayers = function() {
  if (!window.map || !window.locationCluster || !window.boreholeCluster || !window.artifactCluster) {
    return;
  }

  if (typeof window.renderMarkers === "function") {
    window.renderMarkers();
  }

  if (typeof window.renderBoreholes === "function") {
    const boreholes = Array.isArray(window.oakData?.boreholes) ? window.oakData.boreholes : [];
    window.renderBoreholes(boreholes);
  }

  if (typeof window.createArtifactMarkers === "function") {
    window.createArtifactMarkers();
  }
};

async function loadSemanticData() {
  console.log("[loadData] Loading semantic data...");

  if (isPiMode()) {
    console.log("[loadData] PI_MODE detected, skipping semantic data.");
    window.semanticData = {
      events: [],
      measurements: [],
      people: [],
      theories: [],
      locationMentions: []
    };
    window.semanticReady = true;
    window.dispatchEvent(new CustomEvent("semantic:ready"));
    return;
  }

  const files = [
    { key: "events", path: "data/events.json" },
    { key: "measurements", path: "data/measurements.json" },
    { key: "people", path: "data/people.json" },
    { key: "theories", path: "data/theories.json" },
    { key: "locationMentions", path: "data/location_mentions.json" }
  ];

  const result = {};

  for (const file of files) {
    try {
      const resp = await fetch(file.path);
      if (!resp.ok) {
        console.warn(
          "[loadData] Semantic file missing or failed:",
          file.path,
          "status:",
          resp.status
        );
        result[file.key] = [];
        continue;
      }
      const data = await resp.json();
      result[file.key] = Array.isArray(data) ? data : [];
      console.log(
        "[loadData] Loaded semantic",
        file.key,
        "records:",
        result[file.key].length
      );
    } catch (err) {
      console.warn(
        "[loadData] Error loading semantic file:",
        file.path,
        err
      );
      result[file.key] = [];
    }
  }

  // Expose globally for any module that wants semantic layers
  window.semanticData = result;
  window.semanticReady = true;
  window.dispatchEvent(new CustomEvent("semantic:ready"));
  console.log("[loadData] Semantic data load complete.");
}

window.loadData = async function () {
  console.log("[loadData] Starting data load...");

  try {
    // ------------------------------------------------------------
    // Fetch primary dataset (oak_island_data.json)
    // ------------------------------------------------------------
    const response = await fetch("data/oak_island_data.json");
    console.log("[loadData] Fetch response status:", response.status);

    if (!response.ok) {
      throw new Error("Failed to load oak_island_data.json: " + response.status);
    }

    const data = await response.json();
    const locationCount = Array.isArray(data.locations)
      ? data.locations.length
      : 0;

    console.log(
      "[loadData] Data loaded successfully:",
      locationCount,
      "locations"
    );

    // ------------------------------------------------------------
    // Global exposure (legacy + modern)
    // ------------------------------------------------------------
    window.oakIslandData = data; // legacy global
    window.oakData = data;       // newer naming convention

    if (typeof window.setOakData === "function") {
      window.setOakData(data);
    }

    // ------------------------------------------------------------
    // Initialize UI components that depend on data
    // ------------------------------------------------------------
    if (typeof window.initCategoryFilters === "function") {
      window.initCategoryFilters();
    }

    if (typeof window.initSeasonFilter === "function") {
      window.initSeasonFilter();
    }

    if (typeof window.initYearSlider === "function") {
      window.initYearSlider();
    }

    if (typeof window.initEpisodeList === "function") {
      window.initEpisodeList();
    }

    // ------------------------------------------------------------
    // Render map layers that depend on data
    // ------------------------------------------------------------
    window.oakDataReady = true;
    if (window.mapReady && typeof window.initMapDataLayers === "function") {
      window.initMapDataLayers();
    } else {
      window.pendingMapDataInit = true;
    }

    // ------------------------------------------------------------
    // Load semantic layers (non-blocking for core UI)
    // ------------------------------------------------------------
    await loadSemanticData();

    console.log("[loadData] All initialization complete.");

  } catch (err) {
    console.error("[loadData] Data loading error:", err);
    alert("Failed to load Oak Island data. Check console for details.");
  }
};