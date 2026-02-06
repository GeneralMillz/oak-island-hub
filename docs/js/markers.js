// Performance optimization: check if location is in current map bounds
function isLocationInBounds(location, mapBounds) {
  const latlng = window.getLatLngFromLocation(location);
  if (!latlng) return false;
  return mapBounds.contains(latlng);
}

// LOCATION MARKERS
window.createLocationMarker = function(location) {
  const latlng = window.getLatLngFromLocation(location);
  if (!latlng) return null;

  const marker = L.marker(latlng);

  const episodes = window.getEpisodesForLocation(location);
  const episodesHtml = episodes.length
    ? `<p><strong>Episodes:</strong> ${episodes.map(ep => `S${ep.season}E${ep.episode}`).join(", ")}</p>`
    : "";

  const artifactsHtml =
    location.artifacts?.length
      ? `<p><strong>Artifacts:</strong> ${location.artifacts.length}</p>`
      : "";

  const popupHtml = `
    <div>
      <h3>${location.name}</h3>
      <p><strong>Type:</strong> ${location.type}</p>
      ${location.firstDocumentedYear ? `<p><strong>First documented:</strong> ${location.firstDocumentedYear}</p>` : ""}
      <p>${location.description || ""}</p>
      ${artifactsHtml}
      ${episodesHtml}
      ${episodes.length > 0 ? '<button class="episode-timeline-btn" style="margin-top:8px;padding:4px 8px;font-size:0.8rem;">View Episode Timeline</button>' : ''}
      <p style="font-size:0.8rem;color:#6b7280;">Click for full details and cross-section.</p>
    </div>
  `;

  marker.bindPopup(popupHtml);

  marker.on("click", () => {
    window.updateDetailsPanelForLocation(location, window.getEpisodesForLocation);
    window.renderCrossSectionForLocation(location);
    window.highlightEpisodeListForLocation(location);
  });

  marker.on("popupopen", () => {
    const btn = document.querySelector('.episode-timeline-btn');
    if (btn) {
      btn.addEventListener('click', () => {
        window.highlightEpisodeListForLocation(location);
        // Scroll to episode list
        const episodeList = document.getElementById('episode-list');
        if (episodeList) {
          episodeList.scrollIntoView({ behavior: 'smooth' });
        }
      });
    }
  });

  marker._oakType = "location";
  marker._oakLocationId = location.id || location.location_id;
  return marker;
};

// BOREHOLE MARKERS
window.createBoreholeMarker = function(bh) {
  if (!window.oakData || !window.oakData.locations) return null;

  const loc = window.oakData.locations.find(
    l => (l.id || l.location_id) === bh.location_id
  );
  if (!loc) return null;

  const latlng = window.getLatLngFromLocation(loc);
  if (!latlng) return null;

  const marker = L.circleMarker(latlng, {
    radius: 6,
    color: "#0077ff",
    fillColor: "#66aaff",
    fillOpacity: 0.8
  });

  marker.bindPopup(`
    <b>${bh.name}</b><br>
    Intervals: ${bh.intervals.length}
  `);

  marker.on("click", () => {
    window.updateDetailsPanelForBorehole(bh, loc);
    window.renderCrossSectionForBorehole(bh);
  });

  marker._oakType = "borehole";
  marker._oakBoreholeId = bh.borehole_id;
  return marker;
};

// ARTIFACT MARKERS
window.createArtifactMarkers = function() {
  // Clear existing markers from cluster
  window.artifactCluster.clearLayers();
  window.artifactMarkers.length = 0;

  if (!window.oakData?.locations) return;

  window.oakData.locations.forEach(loc => {
    const latlng = window.getLatLngFromLocation(loc);
    if (!latlng || !loc.artifacts?.length) return;

    loc.artifacts.forEach(art => {
      const marker = L.circleMarker(latlng, {
        radius: 4,
        color: "#f59e0b",
        fillColor: "#fbbf24",
        fillOpacity: 0.9
      });

      const epText =
        art.episode_season && art.episode_number
          ? `S${art.episode_season}E${art.episode_number} – ${art.episode_title || ""}`
          : "Episode unknown";

      marker.bindPopup(`
        <div>
          <b>${art.name}</b><br>
          <span>${art.description || ""}</span><br>
          ${art.depth_m ? `<span>Depth: ${art.depth_m} m</span><br>` : ""}
          <span>${epText}</span>
        </div>
      `);

      marker.on("click", () => {
        window.updateDetailsPanelForArtifact(art, loc);
      });

      marker._oakType = "artifact";
      marker._oakLocationId = loc.id || loc.location_id;
      window.artifactMarkers.push(marker);
      window.artifactCluster.addLayer(marker);
    });
  });

  window.applyLayerVisibility();
};

// RENDER FUNCTIONS
// Performance optimization: check if location is in current map bounds
function isLocationInBounds(location, mapBounds) {
  const latlng = window.getLatLngFromLocation(location);
  if (!latlng) return false;
  return mapBounds.contains(latlng);
}

window.renderMarkers = function(useViewportOptimization = false) {
  window.locationCluster.clearLayers();
  window.locationMarkers.length = 0;

  if (!window.oakData?.locations) return;

  window.oakData.locations.forEach(location => {
    const marker = window.createLocationMarker(location);
    if (marker) {
      window.locationMarkers.push(marker);
      window.locationCluster.addLayer(marker);
    }
  });

  window.applyLayerVisibility();
};

// CLEAN-SLATE: Disable boreholes for now, but keep function intact
window.renderBoreholes = function(boreholes) {
  // Intentionally disabled during rebuild
  window.boreholeCluster.clearLayers();
  window.boreholeMarkers.length = 0;
  return;
};