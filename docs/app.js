// app.js
// Global application bootstrap and mobile enhancements.
// This orchestrates the entire app startup sequence in a clean, predictable way.

// ------------------------------------------------------------
// Global config defaults (override before app.js if needed)
// ------------------------------------------------------------
window.CHATBOT_API_BASE = window.CHATBOT_API_BASE || "https://YOUR_RENDER_URL/api";
window.TILE_BASE_URL = window.TILE_BASE_URL || "https://YOUR_CDN_URL/tiles";

// ------------------------------------------------------------
// Mobile responsiveness enhancements
// ------------------------------------------------------------
function initMobileEnhancements() {
  const isTouchDevice =
    "ontouchstart" in window || navigator.maxTouchPoints > 0;

  if (isTouchDevice) {
    document.body.classList.add("touch-device");

    // Improve Leaflet popup behavior on mobile
    if (typeof L !== "undefined") {
      L.Popup.prototype.options.closeButton = true;
      L.Popup.prototype.options.autoClose = false;
    }

    // Ensure viewport meta tag exists
    if (!document.querySelector('meta[name="viewport"]')) {
      const viewport = document.createElement("meta");
      viewport.name = "viewport";
      viewport.content =
        "width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no";
      document.head.appendChild(viewport);
    }
  }

  // Handle orientation changes
  window.addEventListener("orientationchange", () => {
    setTimeout(() => {
      if (typeof window.renderMarkers === "function") {
        window.renderMarkers();
      }

      if (window.map && typeof window.map.fitBounds === "function") {
        window.map.fitBounds([
          [44.515, -64.303],
          [44.518, -64.299]
        ]);
      }
    }, 500);
  });
}

// ------------------------------------------------------------
// View navigation (Map / Chatbot)
// ------------------------------------------------------------
function initViewNavigation() {
  const buttons = Array.from(document.querySelectorAll(".nav-button"));
  const views = Array.from(document.querySelectorAll(".view"));

  if (!buttons.length || !views.length) return;

  async function activateView(viewId) {
    views.forEach(view => {
      view.classList.toggle("active", view.id === viewId);
    });
    buttons.forEach(btn => {
      btn.classList.toggle("active", btn.dataset.view === viewId);
    });

    if (viewId === "chatbot-view" && typeof window.initChatbot === "function") {
      window.initChatbot();
    }

    if (viewId === "map-view" && !window.mapInitialized) {
      try {
        if (typeof window.loadMapAssets === "function") {
          await window.loadMapAssets();
        }
        if (typeof window.initMap === "function") {
          window.initMap();
          window.mapInitialized = true;
        }
      } catch (err) {
        console.error("[app] Map asset loading error:", err);
      }
    }
  }

  buttons.forEach(btn => {
    btn.addEventListener("click", () => activateView(btn.dataset.view));
  });

  const activeButton = buttons.find(btn => btn.classList.contains("active"));
  if (activeButton) activateView(activeButton.dataset.view);
}

// ------------------------------------------------------------
// DOM Ready Bootstrap
// ------------------------------------------------------------
function startApp() {
  console.log("[app] DOM loaded, starting initialization...");

  try {
    initMobileEnhancements();
    console.log("[app] Mobile enhancements initialized.");
  } catch (err) {
    console.error("[app] Mobile enhancement error:", err);
  }

  try {
    if (typeof window.initSearchInputs === "function") {
      window.initSearchInputs();
      console.log("[app] Search inputs initialized.");
    }
  } catch (err) {
    console.error("[app] Search input initialization error:", err);
  }

  try {
    initViewNavigation();
    console.log("[app] View navigation initialized.");
  } catch (err) {
    console.error("[app] View navigation error:", err);
  }

  try {
    if (typeof window.loadData === "function") {
      window.loadData();
      console.log("[app] Data loading started.");
    }
  } catch (err) {
    console.error("[app] Data loading error:", err);
  }

  console.log("[app] Initialization sequence complete.");
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", startApp);
} else {
  startApp();
}