window.OakMap = window.OakMap || {};

// ------------------------------------------------------------
// CONTOURS (1m core + full-island)
// ------------------------------------------------------------
window.OakMap.initContours = function() {
  const base = (window.TILE_BASE_URL || "tiles").replace(/\/+$/, "");

  // Core island contours
  let contours1mLayer = null;

  fetch(`${base}/contours_1m/contours_1m.json`)
    .then(r => {
      if (!r.ok) throw new Error("Failed to load contours_1m.json");
      return r.json();
    })
    .then(data => {
      contours1mLayer = L.geoJSON(data, {
        style: { color: "#ff8800", weight: 1 }
      });
      window.contours1mLayer = contours1mLayer;

      // Update overlay control once contours are ready
      if (window._overlayControl) {
        window._overlayControl.addOverlay(contours1mLayer, "Contours 1m");
      }
    })
    .catch(err => {
      console.warn("Contours 1m not loaded:", err);
    });

  // Full-Island contours (optional)
  let fullContours1mLayer = null;

  fetch(`${base}/full_island_contours_1m/contours_1m.json`)
    .then(r => {
      if (!r.ok) throw new Error("Failed to load full-island contours_1m.json");
      return r.json();
    })
    .then(data => {
      fullContours1mLayer = L.geoJSON(data, {
        style: { color: "#ffaa00", weight: 1 }
      });
      window.fullContours1mLayer = fullContours1mLayer;

      if (window._overlayControl) {
        window._overlayControl.addOverlay(fullContours1mLayer, "Full-Island Contours 1m");
      }
    })
    .catch(err => {
      console.warn("Full-Island Contours 1m not loaded (optional):", err);
    });
};

// ------------------------------------------------------------
// PERFORMANCE OPTIMIZATION (moveend throttling + invalidateSize)
// ------------------------------------------------------------
window.OakMap.initPerformance = function(m) {
  m.on("moveend", () => {
    clearTimeout(m._markerRenderTimeout);
    m._markerRenderTimeout = setTimeout(() => {
      if (typeof window.renderMarkers === "function") {
        window.renderMarkers(true);
      }
    }, 200);
  });

  // Fix tile math after layout settles
  setTimeout(() => {
    m.invalidateSize(true);
  }, 200);
};

// ------------------------------------------------------------
// CLICK-TO-UPDATE COORDINATE TOOL (unchanged, just moved)
// ------------------------------------------------------------
window.enableCoordinateCapture = function() {
  if (!window._leafletMap) return;

  // Prevent duplicate handlers
  window._leafletMap.off("click");

  window._leafletMap.on("click", function(e) {
    const lat = e.latlng.lat.toFixed(6);
    const lng = e.latlng.lng.toFixed(6);

    L.popup()
      .setLatLng(e.latlng)
      .setContent(`
        <div style="font-size:14px;">
          <b>Clicked:</b><br>
          Lat: ${lat}<br>
          Lng: ${lng}<br><br>
          <input id="coord-loc-id" placeholder="location_id" style="width:120px;" />
          <button onclick="window.saveCoord('${lat}', '${lng}')">Save</button>
        </div>
      `)
      .openOn(window._leafletMap);
  });
};

window.saveCoord = async function(lat, lng) {
  const locId = document.getElementById("coord-loc-id").value.trim();
  if (!locId) {
    alert("Enter a location_id");
    return;
  }

  const payload = {
    location_id: locId,
    lat: parseFloat(lat),
    lng: parseFloat(lng),
    updated_at: new Date().toISOString()
  };

  console.log("Saving coordinate patch:", payload);

  await fetch("/coord_patch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  alert(`Saved patch for ${locId}`);
};
