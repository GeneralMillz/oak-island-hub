window.zoomToFirstSearchMatch = function(query) {
  if (!window.oakData || !window.oakData.locations) return;
  const q = window.normalizeString(query);

  for (const loc of window.oakData.locations) {
    if (window.matchesGlobalSearchLocation(loc, q)) {
      const latlng = window.getLatLngFromLocation(loc);
      if (latlng) {
        window.map.setView(latlng, 18);
      }
      return;
    }
  }
};
