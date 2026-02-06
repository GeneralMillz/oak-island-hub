window.OakMap = window.OakMap || {};

// ------------------------------------------------------------
// HISTORICAL / LIDAR OVERLAYS + CLUSTERS
// ------------------------------------------------------------
window.OakMap.initOverlaysAndClusters = function(m) {

  // Historical + LIDAR overlays
  const histImageUrl = "images/historical_overlay.svg";
  const lidarImageUrl = "images/lidar_overlay.svg";

  // Covers entire island
  const overlayBounds = [
    [44.5210, -64.3040],  // SW
    [44.5265, -64.2960]   // NE
  ];

  const histOverlay = L.imageOverlay(histImageUrl, overlayBounds, { opacity: 0.7 });
  const lidarOverlay = L.imageOverlay(lidarImageUrl, overlayBounds, { opacity: 0.6 });

  // Expose overlays globally
  window.historicalOverlay = histOverlay;
  window.lidarOverlay = lidarOverlay;

  // Marker clusters
  const locCluster = L.markerClusterGroup({
    chunkedLoading: true,
    maxClusterRadius: 50,
    spiderfyOnMaxZoom: true,
    showCoverageOnHover: false,
    zoomToBoundsOnClick: true,
    removeOutsideVisibleBounds: true
  });

  const bhCluster = L.markerClusterGroup({
    chunkedLoading: true,
    maxClusterRadius: 30,
    spiderfyOnMaxZoom: true,
    showCoverageOnHover: false,
    zoomToBoundsOnClick: true,
    removeOutsideVisibleBounds: true
  });

  const artCluster = L.markerClusterGroup({
    chunkedLoading: true,
    maxClusterRadius: 40,
    spiderfyOnMaxZoom: true,
    showCoverageOnHover: false,
    zoomToBoundsOnClick: true,
    removeOutsideVisibleBounds: true
  });

  // Expose clusters globally
  window.locationCluster = locCluster;
  window.boreholeCluster = bhCluster;
  window.artifactCluster = artCluster;

  return {
    histOverlay,
    lidarOverlay,
    locCluster,
    bhCluster,
    artCluster
  };
};

// ------------------------------------------------------------
// OVERLAY + LAYER TOGGLES
// ------------------------------------------------------------
window.initOverlayToggles = function() {

  // Historical / LIDAR toggles
  const histCheckbox = document.getElementById("overlay-nolan");
  const lidarCheckbox = document.getElementById("overlay-1897");

  if (histCheckbox) {
    histCheckbox.addEventListener("change", e => {
      if (!window.map || !window.historicalOverlay) return;
      e.target.checked
        ? window.historicalOverlay.addTo(window.map)
        : window.map.removeLayer(window.historicalOverlay);
    });
  }

  if (lidarCheckbox) {
    lidarCheckbox.addEventListener("change", e => {
      if (!window.map || !window.lidarOverlay) return;
      e.target.checked
        ? window.lidarOverlay.addTo(window.map)
        : window.map.removeLayer(window.lidarOverlay);
    });
  }

  // Location / borehole / artifact toggles
  const locCheckbox = document.getElementById("layer-locations");
  const bhCheckbox = document.getElementById("layer-boreholes");
  const artCheckbox = document.getElementById("layer-artifacts");

  if (locCheckbox) {
    locCheckbox.checked = window.showLocations;
    locCheckbox.addEventListener("change", e => {
      window.setShowLocations(e.target.checked);
      window.applyLayerVisibility();
    });
  }

  if (bhCheckbox) {
    bhCheckbox.checked = window.showBoreholes;
    bhCheckbox.addEventListener("change", e => {
      window.setShowBoreholes(e.target.checked);
      window.applyLayerVisibility();
    });
  }

  if (artCheckbox) {
    artCheckbox.checked = window.showArtifacts;
    artCheckbox.addEventListener("change", e => {
      window.setShowArtifacts(e.target.checked);
      window.applyLayerVisibility();
    });
  }

  // Basemap switcher (OSM vs full-island orthophoto)
  const basemapOsm = document.getElementById("basemap-osm");
  const basemapOrtho = document.getElementById("basemap-orthophoto");

  if (basemapOsm) {
    basemapOsm.addEventListener("change", e => {
      if (e.target.checked) window.setBasemap("osm");
    });
  }

  if (basemapOrtho) {
    basemapOrtho.addEventListener("change", e => {
      if (e.target.checked) window.setBasemap("orthophoto");
    });
  }

  // Opacity sliders
  const orthoOpacity = document.getElementById("opacity-orthophoto");
  const hillOpacity = document.getElementById("opacity-hillshade");

  if (orthoOpacity) {
    orthoOpacity.addEventListener("input", e => {
      const v = Math.max(0, Math.min(100, Number(e.target.value))) / 100;
      if (window.fullIslandOrthophotoTiles) {
        window.fullIslandOrthophotoTiles.setOpacity(v);
      }
    });
  }

  if (hillOpacity) {
    hillOpacity.addEventListener("input", e => {
      const v = Math.max(0, Math.min(100, Number(e.target.value))) / 100;
      if (window.fullIslandHillshadeTiles) window.fullIslandHillshadeTiles.setOpacity(v);
      if (window.fullIslandHillshadeMultiTiles) window.fullIslandHillshadeMultiTiles.setOpacity(v);
    });
  }
};

// ------------------------------------------------------------
// BASEMAP CONTROL (OSM vs full-island orthophoto)
// ------------------------------------------------------------
window.setBasemap = function(mode) {
  if (!window.map || !window.baseLayers || !window.rasterLayers) return;

  const m = window.map;
  const { osm } = window.baseLayers;
  const { full_island_orthophoto, full_island_hillshade } = window.rasterLayers;

  if (mode === "osm") {
    if (!m.hasLayer(osm)) osm.addTo(m);
    if (full_island_orthophoto && m.hasLayer(full_island_orthophoto)) {
      m.removeLayer(full_island_orthophoto);
    }
    if (full_island_hillshade && m.hasLayer(full_island_hillshade)) {
      m.removeLayer(full_island_hillshade);
    }
    window.currentBasemap = "osm";
  }

  if (mode === "orthophoto") {
    if (m.hasLayer(osm)) m.removeLayer(osm);
    if (full_island_orthophoto && !m.hasLayer(full_island_orthophoto)) {
      full_island_orthophoto.addTo(m);
    }
    if (full_island_hillshade && !m.hasLayer(full_island_hillshade)) {
      full_island_hillshade.addTo(m);
    }
    window.currentBasemap = "orthophoto";
  }
};

// ------------------------------------------------------------
// CLUSTER VISIBILITY
// ------------------------------------------------------------
window.applyLayerVisibility = function() {
  if (!window.map) return;

  // Locations
  if (window.showLocations) {
    if (window.locationCluster && !window.map.hasLayer(window.locationCluster)) {
      window.map.addLayer(window.locationCluster);
    }
  } else {
    if (window.locationCluster && window.map.hasLayer(window.locationCluster)) {
      window.map.removeLayer(window.locationCluster);
    }
  }

  // Boreholes
  if (window.showBoreholes) {
    if (window.boreholeCluster && !window.map.hasLayer(window.boreholeCluster)) {
      window.map.addLayer(window.boreholeCluster);
    }
  } else {
    if (window.boreholeCluster && window.map.hasLayer(window.boreholeCluster)) {
      window.map.removeLayer(window.boreholeCluster);
    }
  }

  // Artifacts
  if (window.showArtifacts) {
    if (window.artifactCluster && !window.map.hasLayer(window.artifactCluster)) {
      window.map.addLayer(window.artifactCluster);
    }
  } else {
    if (window.artifactCluster && window.map.hasLayer(window.artifactCluster)) {
      window.map.removeLayer(window.artifactCluster);
    }
  }
};