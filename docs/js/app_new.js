/**
 * app.js
 * 
 * Application bootstrap and initialization.
 * Sets up router, navigation, and loads the default home page.
 */

(function() {
  // Global configuration
  window.APP_CONFIG = {
    apiBase: '/api/v2',
    defaultRoute: 'home',
    debug: false
  };

  /**
   * Initialize navigation tab handlers
   */
  function initNavigation() {
    const navTabs = document.querySelectorAll('.nav-tab');
    navTabs.forEach(tab => {
      tab.addEventListener('click', (e) => {
        const route = tab.dataset.route;
        window.router.navigate(route);
      });
    });
  }

  /**
   * Initialize router handlers
   */
  async function initSectionLoaders() {
    // Sections should be loaded from their respective .html files
    // Each section's <script> block registers its route handler
    console.log('[App] Section loaders registered');
  }

  /**
   * Start the application
   */
  async function start() {
    console.log('[App] Starting Oak Island Research Center');

    try {
      // Check API availability
      await window.apiService.checkAvailability();
      
      // Initialize navigation
      initNavigation();
      
      // Initialize section loaders
      await initSectionLoaders();

      // Get content container
      const contentContainer = document.getElementById('content');
      if (!contentContainer) {
        console.error('[App] Content container not found');
        return;
      }

      // Initialize router with content container
      await window.router.init(contentContainer);

      // Navigate to default route if hash is not set
      if (!window.location.hash) {
        window.router.navigate(window.APP_CONFIG.defaultRoute);
      }

      console.log('[App] Application ready');
    } catch (error) {
      console.error('[App] Fatal initialization error:', error);
      const content = document.getElementById('content');
      if (content) {
        content.innerHTML = `<div class="error">Failed to start application: ${error.message}</div>`;
      }
    }
  }

  /**
   * Initialize on DOMContentLoaded
   */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
