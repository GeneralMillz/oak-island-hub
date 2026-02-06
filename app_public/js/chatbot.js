// chatbot.js
// Frontend logic for the Oak Island chatbot interface.

(function () {
  const CHATBOT_VIEW_ID = "chatbot-view";
  const CHATBOT_ROOT_ID = "chatbot-root";
  const CHATBOT_HTML_PATH = "chatbot/chatbot.html";

  function detectPiMode() {
    if (typeof window.PI_MODE === "boolean") return window.PI_MODE;
    const isARM = /armv|aarch/i.test(navigator.userAgent || navigator.platform);
    const lowCores = (navigator.hardwareConcurrency || 4) <= 4;
    const smallScreen = window.innerWidth < 1024;
    window.PI_MODE = isARM || (lowCores && smallScreen);
    return window.PI_MODE;
  }

  function getModeLabel() {
    return detectPiMode() ? "PI_MODE" : "WEB_MODE";
  }

  function createMessage(role, html) {
    const container = document.createElement("div");
    container.className = `chatbot-message ${role}`;
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.innerHTML = html;
    container.appendChild(bubble);
    return container;
  }

  function renderEntityCard(entity) {
    const { title, type, summary, data } = entity;
    return `
      <div class="entity-card entity-${type}">
        <h3>${escapeHtml(title)}</h3>
        <p class="entity-type">${type}</p>
        <p class="entity-summary">${escapeHtml(summary)}</p>
      </div>
    `;
  }

  function renderResponse(messageEl, payload) {
    const { title, summary, entities, related_entities, mode } = payload;
    let html = `<div class="response-title">${escapeHtml(title)}</div>`;
    
    if (summary) {
      html += `<div class="response-summary">${escapeHtml(summary)}</div>`;
    }
    
    // Render entity cards
    if (entities && Array.isArray(entities) && entities.length > 0) {
      html += `<div class="entities-container">`;
      for (const entity of entities.slice(0, 8)) {
        html += renderEntityCard(entity);
      }
      html += `</div>`;
    }
    
    // Render related entities
    if (related_entities && typeof related_entities === "object") {
      const keys = Object.keys(related_entities);
      if (keys.length > 0) {
        html += `<div class="related-entities">`;
        for (const key of keys) {
          const value = related_entities[key];
          if (Array.isArray(value)) {
            if (value.length > 0) {
              html += `<div class="related-section"><h4>${escapeHtml(key)}</h4><ul>`;
              for (const item of value.slice(0, 5)) {
                if (typeof item === "string") {
                  html += `<li>${escapeHtml(item)}</li>`;
                } else if (typeof item === "object" && item.label) {
                  html += `<li>${escapeHtml(item.label)}</li>`;
                }
              }
              html += `</ul></div>`;
            }
          } else if (typeof value === "number") {
            html += `<div class="related-stat"><span class="label">${escapeHtml(key)}:</span> <span class="value">${value}</span></div>`;
          }
        }
        html += `</div>`;
      }
    }
    
    if (mode) {
      html += `<div class="response-mode">Mode: ${escapeHtml(mode)}</div>`;
    }
    
    messageEl.querySelector(".bubble").innerHTML = html;
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  async function callSemanticApi(query) {
    const piMode = detectPiMode();
    const apiBase = (window.CHATBOT_API_BASE || "").replace(/\/+$/, "");
    const endpoint = `${apiBase}/semantic/query`;
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, piMode })
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `Request failed (${response.status})`);
    }

    return response.json();
  }

  function scrollMessages(messagesEl) {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function bindChatbotHandlers() {
    const messagesEl = document.getElementById("chatbot-messages");
    const inputEl = document.getElementById("chatbot-input");
    const sendEl = document.getElementById("chatbot-send");
    const suggestionsEl = document.getElementById("chatbot-suggestions");
    const modeEl = document.getElementById("chatbot-mode");

    if (!messagesEl || !inputEl || !sendEl || !modeEl) return;

    modeEl.textContent = `Mode: ${getModeLabel()}`;

    const sendMessage = async (text) => {
      const trimmed = (text || "").trim();
      if (!trimmed) return;

      const userMessage = createMessage("user", escapeHtml(trimmed));
      messagesEl.appendChild(userMessage);

      const pending = createMessage("bot", "Thinking...");
      messagesEl.appendChild(pending);
      scrollMessages(messagesEl);

      inputEl.value = "";

      try {
        const payload = await callSemanticApi(trimmed);
        renderResponse(pending, payload);
      } catch (err) {
        pending.querySelector(".bubble").innerHTML = `<div class="error">Error: ${escapeHtml(err.message)}</div>`;
      }
      scrollMessages(messagesEl);
    };

    sendEl.addEventListener("click", () => sendMessage(inputEl.value));
    inputEl.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        sendMessage(inputEl.value);
      }
    });

    if (suggestionsEl) {
      suggestionsEl.addEventListener("click", (event) => {
        const button = event.target.closest("button");
        if (!button) return;
        sendMessage(button.textContent);
      });
    }
  }

  async function loadChatbotHtml() {
    const root = document.getElementById(CHATBOT_ROOT_ID);
    if (!root || root.dataset.loaded === "true") return;

    const response = await fetch(CHATBOT_HTML_PATH);
    if (!response.ok) {
      root.innerHTML = "<p>Failed to load chatbot UI.</p>";
      return;
    }

    const html = await response.text();
    root.innerHTML = html;
    root.dataset.loaded = "true";
    bindChatbotHandlers();
  }

  window.initChatbot = function () {
    const view = document.getElementById(CHATBOT_VIEW_ID);
    if (!view) return;
    loadChatbotHtml();
  };
})();
