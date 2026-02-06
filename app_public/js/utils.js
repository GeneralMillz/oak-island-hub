// Utility functions
window.normalizeString = function(str) {
  return (str || "").toString().trim().toLowerCase();
};

window.matchesTextSearch = function(location, query) {
  if (!query) return true;
  const q = window.normalizeString(query);
  return (
    window.normalizeString(location.name).includes(q) ||
    window.normalizeString(location.type).includes(q) ||
    window.normalizeString(location.description).includes(q)
  );
};

window.matchesGlobalSearchLocation = function(location, query) {
  if (!query) return true;
  const q = window.normalizeString(query);

  if (window.normalizeString(location.name).includes(q)) return true;
  if (window.normalizeString(location.type).includes(q)) return true;
  if (window.normalizeString(location.description).includes(q)) return true;

  if (location.artifacts) {
    return location.artifacts.some(a =>
      window.normalizeString(a.name).includes(q) ||
      window.normalizeString(a.description).includes(q)
    );
  }

  return false;
};

// Enhanced Fuse.js search function
window.searchLocationsWithFuse = function(query) {
  if (!query || !window.Fuse) return [];

  const locations = window.oakData?.locations || [];

  // Prepare search data
  const searchData = locations.map(location => ({
    ...location,
    searchText: [
      location.name,
      location.type,
      location.description,
      ...(location.artifacts?.map(a => `${a.name} ${a.description}`) || [])
    ].join(' ').toLowerCase()
  }));

  const fuse = new Fuse(searchData, {
    keys: ['searchText'],
    threshold: 0.3, // More lenient matching
    includeScore: true,
    includeMatches: true,
    minMatchCharLength: 2
  });

  const results = fuse.search(query);
  return results.map(result => ({
    location: result.item,
    score: result.score,
    matches: result.matches
  }));
};

window.matchesCategory = function(location, categoriesSet) {
  if (!categoriesSet || categoriesSet.size === 0) return true;
  return categoriesSet.has(location.type);
};

window.matchesSeason = function(location, season) {
  if (!season || season === "all") return true;
  const s = parseInt(season, 10);
  if (!location.relatedSeasons) return true;
  if (Array.isArray(location.relatedSeasons)) {
    return location.relatedSeasons.includes(s);
  }
  return false;
};

window.matchesYear = function(location, year) {
  if (!year || year === "all") return true;
  const y = parseInt(year, 10);
  
  // Map era_primary to approximate discovery year
  const era = (location.era_primary || "").toLowerCase();
  if (era === "modern") {
    // Modern discoveries (during the show) visible from 2014 onwards
    return y >= 2014;
  } else if (era === "classic" || era === "") {
    // Classic discoveries (pre-show) visible for all timeline years
    return true;
  }
  
  // Fallback: if no era specified, assume classic
  return true;
};

window.getLatLngFromLocation = function(location) {
  if (!location) return null;

  const lat = Number(location.lat);
  const lng = Number(location.lng);

  if (!isFinite(lat) || !isFinite(lng)) return null;

  return [lat, lng];
};

window.getEpisodesForLocation = function(location) {
  if (!window.oakData || !window.oakData.seasons) return [];
  if (!location.artifacts || !location.artifacts.length) return [];

  const seen = new Set();
  const episodes = [];

  location.artifacts.forEach(a => {
    const s = parseInt(a.episode_season || a.episodeSeason || 0, 10);
    const e = parseInt(a.episode_number || a.episodeNumber || 0, 10);
    const title = a.episode_title || a.episodeTitle || "";

    if (!s || !e) return;
    const key = `s${s}e${e}`;
    if (seen.has(key)) return;
    seen.add(key);

    episodes.push({ season: s, episode: e, title });
  });

  episodes.sort((a, b) =>
    a.season === b.season ? a.episode - b.episode : a.season - b.season
  );
  return episodes;
};

window.getLocationsForEpisode = function(season, episode) {
  if (!window.oakData || !window.oakData.locations) return [];
  const s = parseInt(season, 10);
  const e = parseInt(episode, 10);

  return window.oakData.locations.filter(loc => {
    if (!loc.artifacts) return false;
    return loc.artifacts.some(a => {
      const as = parseInt(a.episode_season || a.episodeSeason || 0, 10);
      const ae = parseInt(a.episode_number || a.episodeNumber || 0, 10);
      return as === s && ae === e;
    });
  });
};
