/**
 * data_semantic_api.js
 * 
 * REST API client for the semantic database.
 * Provides lazy-loaded data from /api/v2/* endpoints.
 * Falls back to JSON slices if API is unavailable.
 */

// ============================================================================
// API CLIENT
// ============================================================================

class SemanticAPIClient {
  constructor(baseUrl = '/api/v2') {
    this.baseUrl = baseUrl;
    this.available = false;
    this.cache = {};
    
    // Check API availability on init
    this.checkAvailability();
  }
  
  async checkAvailability() {
    try {
      const response = await fetch(`${this.baseUrl}/../status`);
      this.available = response.ok;
      if (this.available) {
        console.log('[API] ✓ Semantic API available at', this.baseUrl);
      } else {
        console.log('[API] ✗ API unavailable, will use JSON fallback');
      }
    } catch (err) {
      console.warn('[API] Connection failed, using JSON fallback:', err.message);
      this.available = false;
    }
  }
  
  // Locations
  async getLocations() {
    if (this.cache.locations) return this.cache.locations;
    
    if (!this.available) {
      return this._loadJsonSlice('locations_min');
    }
    
    try {
      const response = await fetch(`${this.baseUrl}/locations`);
      const data = await response.json();
      this.cache.locations = data;
      return data;
    } catch (err) {
      console.warn('[API] Location fetch failed:', err);
      return this._loadJsonSlice('locations_min');
    }
  }
  
  async getLocationDetail(locationId) {
    const cacheKey = `location_${locationId}`;
    if (this.cache[cacheKey]) return this.cache[cacheKey];
    
    if (!this.available) return null;
    
    try {
      const response = await fetch(`${this.baseUrl}/locations/${locationId}`);
      const data = await response.json();
      this.cache[cacheKey] = data;
      return data;
    } catch (err) {
      console.warn('[API] Location detail fetch failed:', err);
      return null;
    }
  }
  
  // Episodes
  async getEpisodes(season = null) {
    const cacheKey = season ? `episodes_s${season}` : 'episodes_all';
    if (this.cache[cacheKey]) return this.cache[cacheKey];
    
    if (!this.available) {
      const data = this._loadJsonSlice('episodes_list');
      if (season && data && data[`season_${season}`]) {
        return data[`season_${season}`];
      }
      return data;
    }
    
    try {
      const url = season 
        ? `${this.baseUrl}/episodes?season=${season}`
        : `${this.baseUrl}/episodes`;
      const response = await fetch(url);
      const data = await response.json();
      this.cache[cacheKey] = data;
      return data;
    } catch (err) {
      console.warn('[API] Episodes fetch failed:', err);
      return [];
    }
  }
  
  // Events (with pagination)
  async getEvents(filters = {}) {
    const { locationId = null, season = null, limit = 100, offset = 0 } = filters;
    
    if (!this.available) return [];
    
    try {
      const params = new URLSearchParams();
      if (locationId) params.append('location_id', locationId);
      if (season) params.append('season', season);
      params.append('limit', limit);
      params.append('offset', offset);
      
      const response = await fetch(`${this.baseUrl}/events?${params}`);
      const data = await response.json();
      return data;
    } catch (err) {
      console.warn('[API] Events fetch failed:', err);
      return { total: 0, count: 0, events: [] };
    }
  }
  
  // Artifacts
  async getArtifacts(filters = {}) {
    const { locationId = null, season = null, type = null } = filters;
    
    if (!this.available) {
      return this._loadJsonSlice('artifacts_summary') || [];
    }
    
    try {
      const params = new URLSearchParams();
      if (locationId) params.append('location_id', locationId);
      if (season) params.append('season', season);
      if (type) params.append('type', type);
      
      const response = await fetch(`${this.baseUrl}/artifacts?${params}`);
      const data = await response.json();
      return data;
    } catch (err) {
      console.warn('[API] Artifacts fetch failed:', err);
      return this._loadJsonSlice('artifacts_summary') || [];
    }
  }
  
  // Theories
  async getTheories() {
    if (this.cache.theories) return this.cache.theories;
    
    if (!this.available) {
      return this._loadJsonSlice('theories_summary') || [];
    }
    
    try {
      const response = await fetch(`${this.baseUrl}/theories`);
      const data = await response.json();
      this.cache.theories = data;
      return data;
    } catch (err) {
      console.warn('[API] Theories fetch failed:', err);
      return this._loadJsonSlice('theories_summary') || [];
    }
  }
  
  async getTheoryMentions(theoryId, filters = {}) {
    const { limit = 100, offset = 0 } = filters;
    
    if (!this.available) return [];
    
    try {
      const params = new URLSearchParams();
      params.append('limit', limit);
      params.append('offset', offset);
      
      const response = await fetch(`${this.baseUrl}/theories/${theoryId}/mentions?${params}`);
      const data = await response.json();
      return data;
    } catch (err) {
      console.warn('[API] Theory mentions fetch failed:', err);
      return { total_mentions: 0, mentions: [] };
    }
  }
  
  // People
  async getPeople() {
    if (this.cache.people) return this.cache.people;
    
    if (!this.available) {
      return this._loadJsonSlice('people_summary') || [];
    }
    
    try {
      const response = await fetch(`${this.baseUrl}/people`);
      const data = await response.json();
      this.cache.people = data;
      return data;
    } catch (err) {
      console.warn('[API] People fetch failed:', err);
      return this._loadJsonSlice('people_summary') || [];
    }
  }
  
  async getPersonDetail(personId) {
    const cacheKey = `person_${personId}`;
    if (this.cache[cacheKey]) return this.cache[cacheKey];
    
    if (!this.available) return null;
    
    try {
      const response = await fetch(`${this.baseUrl}/people/${personId}`);
      const data = await response.json();
      this.cache[cacheKey] = data;
      return data;
    } catch (err) {
      console.warn('[API] Person detail fetch failed:', err);
      return null;
    }
  }
  
  // Search
  async search(query, filters = {}) {
    const { type = null, limit = 50 } = filters;
    
    if (!query || query.length < 2) return null;
    
    if (!this.available) return null;
    
    try {
      const params = new URLSearchParams();
      params.append('q', query);
      params.append('limit', limit);
      if (type) params.append('type', type);
      
      const response = await fetch(`${this.baseUrl}/search?${params}`);
      const data = await response.json();
      return data;
    } catch (err) {
      console.warn('[API] Search failed:', err);
      return null;
    }
  }
  
  // ============================================================================
  // PRIVATE METHODS
  // ============================================================================
  
  _loadJsonSlice(sliceName) {
    const cacheKey = `slice_${sliceName}`;
    if (this.cache[cacheKey]) return this.cache[cacheKey];
    
    // This is synchronous - only works for already-loaded JSON
    // For actual loading, use fetchJsonSlice
    return this.cache[cacheKey] || null;
  }
  
  async fetchJsonSlice(sliceName) {
    const cacheKey = `slice_${sliceName}`;
    if (this.cache[cacheKey]) return this.cache[cacheKey];
    
    try {
      const response = await fetch(`data/${sliceName}_summary.json`);
      if (!response.ok) {
        // Try alternate name
        const alt = await fetch(`data/${sliceName}.json`);
        if (!alt.ok) return null;
        const data = await alt.json();
        this.cache[cacheKey] = data;
        return data;
      }
      const data = await response.json();
      this.cache[cacheKey] = data;
      return data;
    } catch (err) {
      console.warn(`[API] Failed to load JSON slice ${sliceName}:`, err);
      return null;
    }
  }
}

// ============================================================================
// GLOBAL INSTANCE
// ============================================================================

window.semanticAPI = new SemanticAPIClient();

// ============================================================================
// INTEGRATION WITH EXISTING DATA SYSTEM
// ============================================================================

async function loadSemanticDataViaAPI() {
  console.log('[Data] Loading semantic data via REST API...');
  
  // Load data in parallel where possible
  const [locations, episodes, theories, people, artifacts] = await Promise.all([
    window.semanticAPI.getLocations(),
    window.semanticAPI.getEpisodes(),
    window.semanticAPI.getTheories(),
    window.semanticAPI.getPeople(),
    window.semanticAPI.getArtifacts()
  ]);
  
  // Store in global window for compatibility
  window.semanticData = {
    locations: locations || [],
    episodes: episodes || [],
    theories: theories || [],
    people: people || [],
    artifacts: artifacts || [],
    // These are now lazy-loaded on demand:
    events: [],      // Use getEvents() to fetch
    measurements: [] // Use getEvents() or API fetch
  };
  
  window.semanticReady = true;
  window.dispatchEvent(new CustomEvent('semantic:ready'));
  
  console.log('[Data] Semantic data loaded (via API)');
  console.log('  Locations:', window.semanticData.locations.length);
  console.log('  Episodes:', window.semanticData.episodes.length);
  console.log('  Theories:', window.semanticData.theories.length);
  console.log('  People:', window.semanticData.people.length);
  console.log('  Artifacts:', window.semanticData.artifacts.length);
}

/**
 * Export API client for use in other modules
 */
window.getSemanticAPI = function() {
  return window.semanticAPI;
};

/**
 * Helper to get locations with proper error handling
 */
window.getLocations = async function() {
  return window.semanticAPI.getLocations();
};

/**
 * Helper to get events with filters
 */
window.getEvents = async function(filters = {}) {
  const result = await window.semanticAPI.getEvents(filters);
  return result.events || [];
};

/**
 * Helper to get event count
 */
window.getEventCount = async function(filters = {}) {
  const result = await window.semanticAPI.getEvents(filters);
  return result.total || 0;
};

/**
 * Helper to search across entities
 */
window.search = async function(query) {
  return window.semanticAPI.search(query);
};
