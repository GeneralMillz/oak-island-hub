window.OakMap = window.OakMap || {};

// ------------------------------------------------------------
// MAP CREATION ONLY
// ------------------------------------------------------------
window.OakMap.createMap = function() {
  console.log("Creating map...");

  // Correct center for Oak Island (Mahone Bay)
  const OAK_CENTER = [44.52363, -64.30021];

  const m = L.map("map", {
    zoomControl: true,
    preferCanvas: true,
    maxZoom: 21
  }).setView(OAK_CENTER, 17);

  console.log("Map created, adding base layer...");

  // Canonical global references (preserve existing behavior)
  window._leafletMap = m;
  window.map = m;

  return m;
};
