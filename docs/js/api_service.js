/**
 * api_service.js
 * 
 * Centralized API client for all semantic database queries.
 * Provides clean abstractions and automatic fallback to JSON files.
 * All endpoints are relative to the current domain.
 */

class APIService {
  constructor() {
    this.baseUrl = '/api/v2';
    this.statusUrl = '/api/status';
    this.cache = new Map();
    this.pending = new Map();
    this.available = false;
    
    this.checkAvailability();
  }

  /**
   * Check if the API is available
   */
  async checkAvailability() {
    try {
      const response = await fetch(this.statusUrl);
      this.available = response.ok;
      console.log('[API] Service', this.available ? 'available' : 'unavailable');
    } catch (err) {
      console.warn('[API] Status check failed:', err.message);
      this.available = false;
    }
  }

  /**
   * Generic fetch method with caching and deduplication
   */
  async fetch(path, options = {}) {
    const cacheKey = `${path}?${new URLSearchParams(options.params || {})}`;
    
    // Return cached result if available
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey);
    }

    // Deduplicate pending requests
    if (this.pending.has(cacheKey)) {
      return this.pending.get(cacheKey);
    }

    // Create new request
    const promise = this._fetchData(path, options);
    this.pending.set(cacheKey, promise);

    try {
      const result = await promise;
      this.cache.set(cacheKey, result);
      return result;
    } finally {
      this.pending.delete(cacheKey);
    }
  }

  /**
   * Internal fetch implementation
   */
  async _fetchData(path, options = {}) {
    if (!this.available) {
      console.warn('[API] API unavailable, returning empty result');
      return { success: false, data: [] };
    }

    try {
      const url = new URL(path.startsWith('/') ? path : `${this.baseUrl}/${path}`, window.location.origin);
      
      if (options.params) {
        Object.entries(options.params).forEach(([key, value]) => {
          if (value !== null && value !== undefined && value !== '') {
            url.searchParams.append(key, value);
          }
        });
      }

      const response = await fetch(url.toString());
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      return { success: true, data };
    } catch (err) {
      console.error('[API] Fetch error:', err.message);
      return { success: false, data: [], error: err.message };
    }
  }

  /**
   * Get API status (stats)
   */
  async getStatus() {
    return this.fetch(this.statusUrl);
  }

  /**
   * Get all locations or a specific location
   */
  async getLocations(locationId = null) {
    if (locationId) {
      return this.fetch(`/api/v2/locations/${locationId}`);
    }
    return this.fetch('/api/v2/locations');
  }

  /**
   * Get episodes, optionally filtered by season
   */
  async getEpisodes(season = null) {
    return this.fetch('/api/v2/episodes', {
      params: { season }
    });
  }

  /**
   * Get events with optional filters
   */
  async getEvents(filters = {}) {
    return this.fetch('/api/v2/events', {
      params: {
        location_id: filters.locationId,
        season: filters.season,
        type: filters.type,
        limit: filters.limit || 100,
        offset: filters.offset || 0
      }
    });
  }

  /**
   * Get artifacts with optional filters
   */
  async getArtifacts(filters = {}) {
    return this.fetch('/api/v2/artifacts', {
      params: {
        location_id: filters.locationId,
        season: filters.season,
        type: filters.type
      }
    });
  }

  /**
   * Get all theories
   */
  async getTheories() {
    return this.fetch('/api/v2/theories');
  }

  /**
   * Get mentions for a specific theory
   */
  async getTheoryMentions(theoryId, filters = {}) {
    return this.fetch(`/api/v2/theories/${theoryId}/mentions`, {
      params: {
        limit: filters.limit || 100,
        offset: filters.offset || 0
      }
    });
  }

  /**
   * Get all people
   */
  async getPeople() {
    return this.fetch('/api/v2/people');
  }

  /**
   * Get a specific person
   */
  async getPerson(personId) {
    return this.fetch(`/api/v2/people/${personId}`);
  }

  /**
   * Search across all entities
   */
  async search(query, filters = {}) {
    return this.fetch('/api/v2/search', {
      params: {
        q: query,
        type: filters.type,
        limit: filters.limit || 50
      }
    });
  }

  /**
   * Clear cache (for development)
   */
  clearCache() {
    this.cache.clear();
  }
}

// Global instance
window.apiService = new APIService();
