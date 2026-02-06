// episodes.js
// Handles episode list rendering, episode selection, and semantic panel updates.

// ------------------------------------------------------------
// Build Episode List
// ------------------------------------------------------------
window.initEpisodeList = function () {
  const container = document.getElementById("episode-list");
  if (!container || !window.oakData || !window.oakData.seasons) return;

  container.innerHTML = "";

  window.oakData.seasons.forEach(season => {
    const header = document.createElement("h4");
    header.textContent = "Season " + season.season;
    container.appendChild(header);

    const ul = document.createElement("ul");

    season.episodes.forEach(ep => {
      const li = document.createElement("li");
      li.className = "episode-item";

      // Fix weird unicode dash
      li.textContent = "S" + ep.season + "E" + ep.episode + " - " + ep.title;

      li.dataset.season = ep.season;
      li.dataset.episode = ep.episode;

      li.addEventListener("click", () => {
        window.highlightLocationsForEpisode(ep.season, ep.episode);

        // NEW: Render semantic panel
        if (typeof window.renderEpisodeSemantics === "function") {
          window.renderEpisodeSemantics(ep.season, ep.episode);
        }
      });

      ul.appendChild(li);
    });

    container.appendChild(ul);
  });
};

// ------------------------------------------------------------
// Highlight Locations on Map for Episode
// ------------------------------------------------------------
window.highlightLocationsForEpisode = function (season, episode) {
  const locs = window.getLocationsForEpisode(season, episode);
  if (!locs.length) return;

  const bounds = [];

  window.locationMarkers.forEach(m => {
    const locId = m._oakLocationId;
    const loc = locs.find(l => (l.id || l.location_id) === locId);

    if (loc) {
      const latlng = m.getLatLng();
      bounds.push(latlng);
      m.openPopup();
    }
  });

  if (bounds.length) {
    const group = L.latLngBounds(bounds);
    window.map.fitBounds(group, { maxZoom: 18 });
  }
};

// ------------------------------------------------------------
// Highlight Episode List for Selected Location
// ------------------------------------------------------------
window.highlightEpisodeListForLocation = function (location) {
  const container = document.getElementById("episode-list");
  if (!container) return;

  const episodes = window.getEpisodesForLocation(location);
  const items = container.querySelectorAll(".episode-item");

  items.forEach(item => {
    item.classList.remove("active");

    const s = parseInt(item.dataset.season, 10);
    const e = parseInt(item.dataset.episode, 10);

    if (episodes.some(ep => ep.season === s && ep.episode === e)) {
      item.classList.add("active");
    }
  });
};

// ------------------------------------------------------------
// NEW: Episode Semantic Panel Renderer
// ------------------------------------------------------------
window.renderEpisodeSemantics = function (season, episode) {
  if (!window.semanticData) {
    console.warn("[semantic] No semantic data loaded.");
    return;
  }

  const panel = document.getElementById("episode-semantic-panel");
  if (!panel) return;

  const { events, measurements, people, theories, locationMentions } = window.semanticData;

  function filterByEp(arr) {
    return arr.filter(
      r =>
        Number(r.season) === Number(season) &&
        Number(r.episode) === Number(episode)
    );
  }

  const ev = filterByEp(events);
  const meas = filterByEp(measurements);
  const ppl = filterByEp(people);
  const thy = filterByEp(theories);
  const loc = filterByEp(locationMentions);

  panel.innerHTML = `
    <h3>Episode Semantics</h3>

    <div class="semantic-section">
      <h4>Events (${ev.length})</h4>
      <ul>${ev.map(e => `<li>[${e.timestamp}] ${e.event_type}</li>`).join("")}</ul>
    </div>

    <div class="semantic-section">
      <h4>Locations (${loc.length})</h4>
      <ul>${loc.map(l => `<li>[${l.timestamp}] ${l.location_name}</li>`).join("")}</ul>
    </div>

    <div class="semantic-section">
      <h4>People (${ppl.length})</h4>
      <ul>${ppl.map(p => `<li>[${p.timestamp}] ${p.person}</li>`).join("")}</ul>
    </div>

    <div class="semantic-section">
      <h4>Theories (${thy.length})</h4>
      <ul>${thy.map(t => `<li>[${t.timestamp}] ${t.theory}</li>`).join("")}</ul>
    </div>

    <div class="semantic-section">
      <h4>Measurements (${meas.length})</h4>
      <ul>${meas.map(m => `<li>[${m.timestamp}] ${m.value} ${m.unit}</li>`).join("")}</ul>
    </div>
  `;
};