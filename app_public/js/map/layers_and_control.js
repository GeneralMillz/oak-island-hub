window.OakMap = window.OakMap || {};

// ------------------------------------------------------------
// TILE LAYERS + LAYER CONTROL (CLEANED + FIXED)
// ------------------------------------------------------------
window.OakMap.initLayersAndControl = function(m) {

  function tileUrl(path) {
    const base = (window.TILE_BASE_URL || "tiles").replace(/\/+$/, "");
    const suffix = path.replace(/^\/+/, "");
    return `${base}/${suffix}`;
  }

  // Base OSM layer
  const osmTiles = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 21,
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(m);

  // ------------------------------------------------------------
  // FULL-ISLAND STACK (WORKING LAYERS)
  // ------------------------------------------------------------

  // Full-Island Orthophoto (still troubleshooting)
  const fullIslandOrthophotoTiles = L.tileLayer(tileUrl("full_island_orthophoto/{z}/{x}/{y}.png"), {
    maxZoom: 21,
    opacity: 1.0,
    tms: true
  });

  const fullIslandHillshadeTiles = L.tileLayer(tileUrl("full_island_hillshade/{z}/{x}/{y}.png"), {
    maxZoom: 21,
    opacity: 0.7,
    tms: true
  });

  const fullIslandHillshadeMultiTiles = L.tileLayer(tileUrl("full_island_hillshade_multi/{z}/{x}/{y}.png"), {
    maxZoom: 21,
    opacity: 0.7,
    tms: true
  });

  const fullIslandSlopeTiles = L.tileLayer(tileUrl("full_island_slope/{z}/{x}/{y}.png"), {
    maxZoom: 21,
    opacity: 0.7,
    tms: true
  });

  const fullIslandAspectTiles = L.tileLayer(tileUrl("full_island_aspect/{z}/{x}/{y}.png"), {
    maxZoom: 21,
    opacity: 0.7,
    tms: true
  });

  const fullIslandRoughnessTiles = L.tileLayer(tileUrl("full_island_roughness/{z}/{x}/{y}.png"), {
    maxZoom: 21,
    opacity: 0.7,
    tms: true
  });

  const fullIslandTpiTiles = L.tileLayer(tileUrl("full_island_tpi/{z}/{x}/{y}.png"), {
    maxZoom: 21,
    opacity: 0.7,
    tms: true
  });

  const fullIslandTriTiles = L.tileLayer(tileUrl("full_island_tri/{z}/{x}/{y}.png"), {
    maxZoom: 21,
    opacity: 0.7,
    tms: true
  });

  // ------------------------------------------------------------
  // DEFAULT VISIBLE LAYERS
  // ------------------------------------------------------------
  fullIslandHillshadeMultiTiles.addTo(m);
  fullIslandOrthophotoTiles.addTo(m);

  // ------------------------------------------------------------
  // GLOBAL REFERENCES (KEEP FOR API COMPATIBILITY)
  // ------------------------------------------------------------
  window.fullIslandOrthophotoTiles = fullIslandOrthophotoTiles;
  window.fullIslandHillshadeTiles = fullIslandHillshadeTiles;
  window.fullIslandHillshadeMultiTiles = fullIslandHillshadeMultiTiles;
  window.fullIslandSlopeTiles = fullIslandSlopeTiles;
  window.fullIslandAspectTiles = fullIslandAspectTiles;
  window.fullIslandRoughnessTiles = fullIslandRoughnessTiles;
  window.fullIslandTpiTiles = fullIslandTpiTiles;
  window.fullIslandTriTiles = fullIslandTriTiles;

  window.baseLayers = { osm: osmTiles };

  window.rasterLayers = {
    full_island_orthophoto: fullIslandOrthophotoTiles,
    full_island_hillshade: fullIslandHillshadeTiles,
    full_island_hillshade_multi: fullIslandHillshadeMultiTiles,
    full_island_slope: fullIslandSlopeTiles,
    full_island_aspect: fullIslandAspectTiles,
    full_island_roughness: fullIslandRoughnessTiles,
    full_island_tpi: fullIslandTpiTiles,
    full_island_tri: fullIslandTriTiles
  };

  window.currentBasemap = "full_island_orthophoto";

  // ------------------------------------------------------------
  // LAYER CONTROL (ONLY WORKING LAYERS)
  // ------------------------------------------------------------
  const baseMaps = {
    "OSM": osmTiles
  };

  const overlayMaps = {
    "Full-Island Orthophoto": fullIslandOrthophotoTiles,
    "Full-Island Hillshade": fullIslandHillshadeTiles,
    "Full-Island Multi-Hillshade": fullIslandHillshadeMultiTiles,
    "Full-Island Slope": fullIslandSlopeTiles,
    "Full-Island Aspect": fullIslandAspectTiles,
    "Full-Island Roughness": fullIslandRoughnessTiles,
    "Full-Island TPI": fullIslandTpiTiles,
    "Full-Island TRI": fullIslandTriTiles
  };

  const overlayControl = L.control.layers(baseMaps, overlayMaps, {
    collapsed: true
  }).addTo(m);

  window._overlayControl = overlayControl;

  return {
    osmTiles,
    fullIslandOrthophotoTiles,
    fullIslandHillshadeTiles,
    fullIslandHillshadeMultiTiles,
    fullIslandSlopeTiles,
    fullIslandAspectTiles,
    fullIslandRoughnessTiles,
    fullIslandTpiTiles,
    fullIslandTriTiles,
    overlayControl
  };
};