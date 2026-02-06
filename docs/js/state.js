// Central shared state for the app
window.oakData = null;
window.map = null;

window.locationMarkers = [];
window.boreholeMarkers = [];
window.artifactMarkers = [];

// Marker cluster groups
window.locationCluster = null;
window.boreholeCluster = null;
window.artifactCluster = null;

window.activeCategories = new Set();
window.activeSeason = "all";
window.activeYear = "all";
window.textSearchQuery = "";
window.globalSearchQuery = "";
window.activeEpisode = null;

// Overlays
window.historicalOverlay = null;
window.lidarOverlay = null;

// Layer visibility
window.showLocations = true;
window.showBoreholes = true;
window.showArtifacts = true;

// Setters
window.setOakData = function(data) { window.oakData = data; };
window.setMap = function(m) { window.map = m; };
window.setHistoricalOverlay = function(o) { window.historicalOverlay = o; };
window.setLidarOverlay = function(o) { window.lidarOverlay = o; };

window.setLocationCluster = function(c) { window.locationCluster = c; };
window.setBoreholeCluster = function(c) { window.boreholeCluster = c; };
window.setArtifactCluster = function(c) { window.artifactCluster = c; };

window.setShowLocations = function(v) { window.showLocations = v; };
window.setShowBoreholes = function(v) { window.showBoreholes = v; };
window.setShowArtifacts = function(v) { window.showArtifacts = v; };

window.setActiveSeason = function(v) { window.activeSeason = v; };
window.setActiveYear = function(v) { window.activeYear = v; };
window.setTextSearchQuery = function(v) { window.textSearchQuery = v; };
window.setGlobalSearchQuery = function(v) { window.globalSearchQuery = v; };
