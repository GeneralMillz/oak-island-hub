// Oak Island approximate bounds (expanded for validation)
const OAK_ISLAND_BOUNDS = {
  north: 44.6,
  south: 44.4,
  east: -64.2,
  west: -64.4
};

let debugLayer = null;
let boundsLayer = null;

/**
 * Validate if coordinates are within reasonable Oak Island bounds
 */
window.validateCoordinates = function(lat, lng) {
  if (lat == null || lng == null) return { valid: false, reason: "null coordinates" };
  if (typeof lat !== "number" || typeof lng !== "number") return { valid: false, reason: "non-numeric coordinates" };
  if (isNaN(lat) || isNaN(lng)) return { valid: false, reason: "NaN coordinates" };

  if (lat < OAK_ISLAND_BOUNDS.south || lat > OAK_ISLAND_BOUNDS.north) {
    return { valid: false, reason: `latitude ${lat} out of bounds (${OAK_ISLAND_BOUNDS.south}-${OAK_ISLAND_BOUNDS.north})` };
  }

  if (lng < OAK_ISLAND_BOUNDS.west || lng > OAK_ISLAND_BOUNDS.east) {
    return { valid: false, reason: `longitude ${lng} out of bounds (${OAK_ISLAND_BOUNDS.west}-${OAK_ISLAND_BOUNDS.east})` };
  }

  return { valid: true };
};

/**
 * Validate all location coordinates and return results
 */
window.validateAllLocations = function() {
  if (!window.oakData || !window.oakData.locations) {
    console.warn("No data loaded for validation");
    return { total: 0, valid: 0, invalid: 0, results: [] };
  }

  const results = [];
  let valid = 0;
  let invalid = 0;

  window.oakData.locations.forEach(location => {
    const coords = window.getLatLngFromLocation(location);
    const validation = window.validateCoordinates(coords?.[0], coords?.[1]);

    const result = {
      id: location.id || location.name,
      name: location.name,
      coordinates: coords,
      validation: validation
    };

    results.push(result);

    if (validation.valid) {
      valid++;
    } else {
      invalid++;
      console.warn(`Invalid coordinates for ${location.name}:`, validation.reason);
    }
  });

  console.log(`Coordinate validation complete: ${valid} valid, ${invalid} invalid out of ${results.length} locations`);

  return {
    total: results.length,
    valid: valid,
    invalid: invalid,
    results: results
  };
};

/**
 * Add debug layer showing coordinate validation status
 */
window.addDebugLayer = function() {
  if (!window.map) {
    console.warn("Map not initialized");
    return;
  }

  // Remove existing debug layer
  if (debugLayer) {
    window.map.removeLayer(debugLayer);
  }

  debugLayer = L.layerGroup();

  if (!window.oakData || !window.oakData.locations) {
    console.warn("No data loaded for debug layer");
    return;
  }

  window.oakData.locations.forEach(location => {
    const coords = window.getLatLngFromLocation(location);
    if (!coords) return;

    const validation = window.validateCoordinates(coords[0], coords[1]);

    // Create marker with color based on validation
    const color = validation.valid ? "#10b981" : "#ef4444"; // green for valid, red for invalid
    const marker = L.circleMarker(coords, {
      radius: 8,
      color: color,
      fillColor: color,
      fillOpacity: 0.7,
      weight: 2
    });

    marker.bindPopup(`
      <b>${location.name}</b><br>
      Coordinates: ${coords[0].toFixed(6)}, ${coords[1].toFixed(6)}<br>
      Status: <span style="color: ${color}">${validation.valid ? "Valid" : "Invalid"}</span>
      ${!validation.valid ? `<br>Issue: ${validation.reason}` : ""}
    `);

    debugLayer.addLayer(marker);
  });

  debugLayer.addTo(window.map);
  console.log("Debug layer added - green markers = valid coordinates, red markers = invalid coordinates");
};

/**
 * Show Oak Island bounds rectangle for reference
 */
window.showCoordinateBounds = function() {
  if (!window.map) {
    console.warn("Map not initialized");
    return;
  }

  // Remove existing bounds layer
  if (boundsLayer) {
    window.map.removeLayer(boundsLayer);
  }

  boundsLayer = L.rectangle([
    [OAK_ISLAND_BOUNDS.south, OAK_ISLAND_BOUNDS.west],
    [OAK_ISLAND_BOUNDS.north, OAK_ISLAND_BOUNDS.east]
  ], {
    color: "#3b82f6",
    weight: 2,
    fillOpacity: 0.1,
    dashArray: "5, 5"
  });

  boundsLayer.addTo(window.map);
  boundsLayer.bindPopup("Oak Island Validation Bounds<br>(Expected coordinate range)");

  console.log("Validation bounds shown - coordinates should be within this blue rectangle");
};

/**
 * Remove debug and bounds layers
 */
window.clearValidationLayers = function() {
  if (debugLayer && window.map) {
    window.map.removeLayer(debugLayer);
    debugLayer = null;
  }

  if (boundsLayer && window.map) {
    window.map.removeLayer(boundsLayer);
    boundsLayer = null;
  }

  console.log("Validation layers cleared");
};

/**
 * Console command for quick validation (can be called from browser console)
 */
window.validateCoords = function() {
  return window.validateAllLocations();
};

// Make validation functions available globally for console debugging
if (typeof window !== "undefined") {
  window.validateCoords = window.validateCoords;
  window.showDebugLayer = window.addDebugLayer;
  window.showBounds = window.showCoordinateBounds;
  window.clearValidation = window.clearValidationLayers;
}