/**
 * ui.js
 * 
 * Shared UI utilities for rendering common components.
 * All rendering functions return HTML strings or append to DOM.
 */

const UI = {
  /**
   * Render a loading spinner
   */
  renderLoading: () => `
    <div class="loading-container">
      <div class="spinner"></div>
      <p>Loading...</p>
    </div>
  `,

  /**
   * Render an error message
   */
  renderError: (message) => `
    <div class="error-container">
      <div class="error-icon">⚠️</div>
      <h3>Error</h3>
      <p>${message || 'Something went wrong'}</p>
    </div>
  `,

  /**
   * Render an empty state
   */
  renderEmpty: (message) => `
    <div class="empty-container">
      <div class="empty-icon">📭</div>
      <p>${message || 'No data found'}</p>
    </div>
  `,

  /**
   * Render stat cards
   */
  renderStats: (stats) => {
    const cards = Object.entries(stats).map(([key, value]) => `
      <div class="stat-card">
        <div class="stat-label">${key}</div>
        <div class="stat-value">${value}</div>
      </div>
    `).join('');
    
    return `<div class="stats-grid">${cards}</div>`;
  },

  /**
   * Render a list of items
   */
  renderList: (items, template) => {
    if (!items || items.length === 0) {
      return UI.renderEmpty();
    }

    const html = items.map((item, index) => {
      try {
        return template(item, index);
      } catch (err) {
        console.error('[UI] Template error:', err, item);
        return `<div class="list-item error">Error rendering item</div>`;
      }
    }).join('');

    return `<div class="list">${html}</div>`;
  },

  /**
   * Render a detail panel
   */
  renderDetailPanel: (title, content, footer = '') => `
    <div class="detail-panel">
      <div class="panel-header">
        <h2>${title}</h2>
      </div>
      <div class="panel-content">
        ${content}
      </div>
      ${footer ? `<div class="panel-footer">${footer}</div>` : ''}
    </div>
  `,

  /**
   * Render a filter bar
   */
  renderFilterBar: (filters) => {
    const html = Object.entries(filters).map(([key, options]) => {
      if (Array.isArray(options)) {
        const opts = options.map(o => `<option value="${o.value}">${o.label}</option>`).join('');
        return `
          <div class="filter-group">
            <label>${key}</label>
            <select id="filter-${key}" class="filter-select">
              <option value="">All</option>
              ${opts}
            </select>
          </div>
        `;
      }
      return '';
    }).join('');

    return `<div class="filter-bar">${html}</div>`;
  },

  /**
   * Render a grid of items
   */
  renderGrid: (items, template, cols = 3) => {
    if (!items || items.length === 0) {
      return UI.renderEmpty();
    }

    const html = items.map((item, index) => {
      try {
        return template(item, index);
      } catch (err) {
        console.error('[UI] Grid template error:', err);
        return `<div class="grid-item error">Error</div>`;
      }
    }).join('');

    return `<div class="grid" style="grid-template-columns: repeat(auto-fill, minmax(300px, 1fr))">${html}</div>`;
  },

  /**
   * Render a side-by-side layout
   */
  renderSideBySide: (leftContent, rightContent) => `
    <div class="side-by-side">
      <div class="left-panel">${leftContent}</div>
      <div class="right-panel">${rightContent}</div>
    </div>
  `,

  /**
   * Format date nicely
   */
  formatDate: (dateStr) => {
    if (!dateStr) return 'Unknown';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return dateStr;
    }
  },

  /**
   * Escape HTML to prevent XSS
   */
  escapeHtml: (text) => {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  },

  /**
   * Highlight search term in text
   */
  highlight: (text, term) => {
    if (!term) return text;
    const regex = new RegExp(`(${UI.escapeHtml(term)})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  },

  /**
   * Truncate text with ellipsis
   */
  truncate: (text, length = 100) => {
    if (!text) return '';
    return text.length > length ? text.substring(0, length) + '...' : text;
  },

  /**
   * Get initials from name
   */
  getInitials: (name) => {
    return name
      .split(' ')
      .map(part => part[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  },

  /**
   * Create a badge
   */
  renderBadge: (text, type = 'default') => `
    <span class="badge badge-${type}">${text}</span>
  `,

  /**
   * Create a button
   */
  renderButton: (label, onclick = '', type = 'default') => `
    <button class="btn btn-${type}" onclick="${onclick}">${label}</button>
  `,

  /**
   * Show a toast notification
   */
  showToast: (message, type = 'info') => {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => toast.remove(), 3000);
  },

  /**
   * Pagination controls
   */
  renderPagination: (total, limit, offset, onPageChange) => {
    const pages = Math.ceil(total / limit);
    const currentPage = Math.floor(offset / limit) + 1;

    if (pages <= 1) return '';

    let html = '<div class="pagination">';
    
    if (currentPage > 1) {
      html += `<button class="page-btn" onclick="${onPageChange}(${(currentPage - 2) * limit})">← Prev</button>`;
    }

    for (let i = 1; i <= Math.min(pages, 5); i++) {
      html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="${onPageChange}(${(i - 1) * limit})">${i}</button>`;
    }

    if (currentPage < pages) {
      html += `<button class="page-btn" onclick="${onPageChange}(${currentPage * limit})">Next →</button>`;
    }

    html += '</div>';
    return html;
  }
};

window.UI = UI;
