// map.js
// Orchestrator that wires all map modules together in a clean, predictable sequence.

window.initMap = function () {
  console.log("[initMap] Initializing Leaflet map...");

  // ------------------------------------------------------------
  // 1. Create the map instance
  // ------------------------------------------------------------
  const m = window.OakMap.createMap();
  if (!m) {
    console.error("[initMap] Failed to create map instance.");
    return;
  }

  // ------------------------------------------------------------
  // 2. Base tile layers + layer control
  // ------------------------------------------------------------
  try {
    window.OakMap.initLayersAndControl(m);
  } catch (err) {
    console.error("[initMap] Error initializing layers and control:", err);
  }

  // ------------------------------------------------------------
  // 3. Historical overlays, LIDAR overlays, and marker clusters
  // ------------------------------------------------------------
  try {
    window.OakMap.initOverlaysAndClusters(m);
  } catch (err) {
    console.error("[initMap] Error initializing overlays/clusters:", err);
  }

  // ------------------------------------------------------------
  // 4. Contours (core + full-island)
  // ------------------------------------------------------------
  try {
    window.OakMap.initContours();
  } catch (err) {
    console.error("[initMap] Error initializing contours:", err);
  }

  // ------------------------------------------------------------
  // 5. Performance tweaks (moveend throttling, invalidateSize)
  // ------------------------------------------------------------
  try {
    window.OakMap.initPerformance(m);
  } catch (err) {
    console.error("[initMap] Error applying performance tweaks:", err);
  }

  // ------------------------------------------------------------
  // 6. Overlay toggles, basemap switches, opacity sliders, visibility toggles
  // ------------------------------------------------------------
  try {
    if (typeof window.initOverlayToggles === "function") {
      window.initOverlayToggles();
    }
  } catch (err) {
    console.error("[initMap] Error initializing overlay toggles:", err);
  }

  // ------------------------------------------------------------
  // 7. Coordinate capture tool
  // ------------------------------------------------------------
  try {
    if (typeof window.enableCoordinateCapture === "function") {
      window.enableCoordinateCapture();
    }
  } catch (err) {
    console.error("[initMap] Error enabling coordinate capture:", err);
  }

  window.mapReady = true;
  if (window.pendingMapDataInit && typeof window.initMapDataLayers === "function") {
    window.initMapDataLayers();
    window.pendingMapDataInit = false;
  }

  console.log("[initMap] Map initialization complete.");
};