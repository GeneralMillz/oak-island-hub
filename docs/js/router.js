/**
 * router.js
 * 
 * Simple hash-based router for single-page app.
 * Routes: #/home, #/episodes, #/locations, #/events, #/artifacts, #/theories, #/people, #/chatbot
 */

class Router {
  constructor() {
    this.routes = new Map();
    this.currentRoute = 'home';
    this.contentElement = null;
    this.callbacks = [];
    
    window.addEventListener('hashchange', () => this.handleRouteChange());
  }

  /**
   * Register a route handler
   * @param {string} route - Route name (e.g., 'home')
   * @param {function} handler - Async function that returns HTML or renders to contentElement
   */
  register(route, handler) {
    this.routes.set(route, handler);
  }

  /**
   * Navigate to a route
   * @param {string} route - Route name
   */
  navigate(route) {
    window.location.hash = `#/${route}`;
  }

  /**
   * Get current route from hash
   */
  getRouteFromHash() {
    const hash = window.location.hash.slice(2) || 'home';
    return hash.split('?')[0] || 'home';
  }

  /**
   * Handle hash change
   */
  async handleRouteChange() {
    const route = this.getRouteFromHash();
    
    if (route === this.currentRoute) return;
    
    this.currentRoute = route;
    await this.renderRoute(route);
    this.updateNavTabs();
    this.triggerCallbacks();
  }

  /**
   * Render a route
   */
  async renderRoute(route) {
    if (!this.contentElement) {
      console.error('[Router] Content element not set');
      return;
    }

    const handler = this.routes.get(route);
    if (!handler) {
      this.contentElement.innerHTML = `<div class="error">Route not found: ${route}</div>`;
      return;
    }

    try {
      this.contentElement.innerHTML = '<div class="loading">Loading...</div>';
      await handler(this.contentElement);
    } catch (err) {
      console.error('[Router] Route error:', err);
      this.contentElement.innerHTML = `<div class="error">Error loading ${route}: ${err.message}</div>`;
    }
  }

  /**
   * Update nav tabs to show active route
   */
  updateNavTabs() {
    document.querySelectorAll('.nav-tab').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.route === this.currentRoute);
    });
  }

  /**
   * Listen for route changes
   */
  onChange(callback) {
    this.callbacks.push(callback);
  }

  /**
   * Trigger all change callbacks
   */
  triggerCallbacks() {
    this.callbacks.forEach(cb => cb(this.currentRoute));
  }

  /**
   * Initialize router
   */
  async init(contentElement) {
    this.contentElement = contentElement;
    
    // Handle initial route
    const route = this.getRouteFromHash();
    this.currentRoute = route;
    
    await this.renderRoute(route);
    this.updateNavTabs();
  }
}

// Global instance
window.router = new Router();
