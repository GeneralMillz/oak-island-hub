# Oak Island Research Center UI - Complete Rebuild Plan

**Status:** Planning Phase  
**Date:** February 6, 2026  
**Scope:** Full front-end redesign with modular architecture  

---

## 📋 ARCHITECTURE OVERVIEW

### **Entry Point**
- `/docs/index.html` - Main SPA shell with top navigation
- Navigation bar with tabs: Home | Episodes | Locations | Events | Artifacts | Theories | People | Chatbot

### **Routing System**
- Hash-based routing: `#/home`, `#/episodes`, `#/locations`, etc.
- Default route: `#/home` (Home / Overview)
- State preserved in URL for bookmarking

### **API Integration**
- Centralized API client (`js/api.js`)
- All endpoints fetched from `/api/v2/*`
- Automatic fallback to JSON slices
- Caching to reduce requests

---

## 🗂️ FILE STRUCTURE

### **HTML Files**
```
docs/
├── index.html                           (Main SPA shell - UPDATED)
├── sections/
│   ├── home.html                       (Home/Overview - NEW)
│   ├── episodes.html                   (Episodes Explorer - NEW)
│   ├── locations.html                  (Locations Explorer - NEW)
│   ├── events.html                     (Events Timeline - NEW)
│   ├── artifacts.html                  (Artifacts & Evidence - NEW)
│   ├── theories.html                   (Theories Hub - NEW)
│   ├── people.html                     (People & Contributors - NEW)
│   └── chatbot.html                    (Chatbot - MOVED/UPDATED)
```

### **CSS Files**
```
docs/
├── styles.css                          (Main stylesheet - UPDATED)
└── sections/
    └── shared.css                      (Shared component styles - NEW)
```

### **JavaScript Modules**
```
docs/js/
├── api.js                              (API client - NEW)
├── router.js                           (SPA routing - NEW)
├── ui.js                               (Shared UI helpers - NEW)
├── home.js                             (Home section logic - NEW)
├── episodes.js                         (Episodes section logic - NEW)
├── locations.js                        (Locations section logic - UPDATED)
├── events.js                           (Events section logic - NEW)
├── artifacts.js                        (Artifacts section logic - NEW)
├── theories.js                         (Theories section logic - NEW)
├── people.js                           (People section logic - NEW)
├── map.js                              (Leaflet map logic - REUSE/REFACTOR)
├── markers.js                          (Map markers - REUSE)
├── data.js                             (Data loader - KEEP AS-IS)
├── data_semantic_api.js                (API client - KEEP AS-IS)
├── state.js                            (State management - KEEP AS-IS)
├── utils.js                            (Utilities - KEEP AS-IS)
├── validation.js                       (Validation - KEEP AS-IS)
├── search.js                           (Search logic - KEEP AS-IS)
├── filters.js                          (Filter logic - KEEP AS-IS)
├── details.js                          (Detail rendering - KEEP AS-IS)
├── chatbot.js                          (Chatbot logic - KEEP AS-IS)
└── app.js                              (Bootstrap - UPDATED)
```

---

## 📄 DETAILED FILE SPECIFICATIONS

### **1. docs/index.html** (UPDATED)
**Purpose:** Main SPA shell  
**Contents:**
- DOCTYPE + head (styles, meta)
- Top navigation bar with tabs
- Content container (dynamically loaded sections)
- Script loader

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Oak Island Research Center</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <div id="app">
    <nav id="top-nav" class="research-nav">
      <div class="nav-logo">🏝️ Oak Island Research</div>
      <div class="nav-tabs">
        <button class="nav-tab" data-route="home" data-label="Home">Home</button>
        <button class="nav-tab" data-route="episodes" data-label="Episodes">Episodes</button>
        <button class="nav-tab" data-route="locations" data-label="Locations">Locations</button>
        <button class="nav-tab" data-route="events" data-label="Events">Events</button>
        <button class="nav-tab" data-route="artifacts" data-label="Artifacts">Artifacts</button>
        <button class="nav-tab" data-route="theories" data-label="Theories">Theories</button>
        <button class="nav-tab" data-route="people" data-label="People">People</button>
        <button class="nav-tab" data-route="chatbot" data-label="Chat">Chat</button>
      </div>
    </nav>
    
    <div id="content" class="research-content">
      <!-- Dynamically loaded section HTML -->
    </div>
  </div>

  <!-- Scripts -->
  <script src="js/utils.js"></script>
  <script src="js/state.js"></script>
  <script src="js/api.js"></script>
  <script src="js/ui.js"></script>
  <script src="js/router.js"></script>
  <script src="js/home.js"></script>
  <script src="js/episodes.js"></script>
  <script src="js/locations.js"></script>
  <script src="js/events.js"></script>
  <script src="js/artifacts.js"></script>
  <script src="js/theories.js"></script>
  <script src="js/people.js"></script>
  <script src="js/chatbot.js"></script>
  <script src="js/app.js"></script>
</body>
</html>
```

---

### **2. docs/sections/home.html** (NEW)
**Purpose:** Overview dashboard with stats and quick links  
**Contents:**
- Welcome header
- API status card
- Quick stat cards (episodes, locations, theories, etc)
- Quick link grid
- Recent activity feed

---

### **3. docs/sections/episodes.html** (NEW)
**Purpose:** Episodes Explorer  
**Contents:**
- Season filter dropdown
- Episodes list
- Episode detail panel
- Events for selected episode

---

### **4. docs/sections/locations.html** (NEW)
**Purpose:** Locations Explorer with map  
**Contents:**
- Leaflet map
- Location list sidebar
- Location detail panel
- Associated events and artifacts

---

### **5. docs/sections/events.html** (NEW)
**Purpose:** Events Timeline browser  
**Contents:**
- Filter controls (season, location, type)
- Events list/timeline view
- Event detail panel

---

### **6. docs/sections/artifacts.html** (NEW)
**Purpose:** Artifacts & Evidence catalog  
**Contents:**
- Filter controls (location, season, type)
- Artifacts grid/list
- Artifact detail panel
- Connected theories and locations

---

### **7. docs/sections/theories.html** (NEW)
**Purpose:** Theories Hub  
**Contents:**
- Theories list sorted by evidence count
- Theory detail panel
- Evidence summary
- Related episodes, events, artifacts

---

### **8. docs/sections/people.html** (NEW)
**Purpose:** People & Contributors  
**Contents:**
- People list with roles
- Person detail panel
- Mentions and contributions
- Related episodes

---

### **9. docs/sections/chatbot.html** (NEW/MOVED)
**Purpose:** Chatbot interface  
**Contents:**
- Move existing chatbot HTML here
- Keep existing functionality

---

## 🎨 NEW JAVASCRIPT MODULES

### **docs/js/api.js** (NEW)
**Purpose:** Centralized API client with error handling  
**Exports:**
```javascript
- fetchAPI(endpoint, params) - Fetch with error handling
- getStatus()
- getEpisodes(season?)
- getLocations()
- getEvents(filters)
- getArtifacts(filters)
- getTheories()
- getPeople()
- search(query)
```

**Features:**
- Automatic JSON fallback
- Caching support
- Error handling with user feedback
- Request deduplication

---

### **docs/js/router.js** (NEW)
**Purpose:** Single-Page App routing  
**Exports:**
```javascript
- initRouter()
- navigate(route)
- currentRoute
- onRouteChange(callback)
```

**Features:**
- Hash-based routing
- Default route: #/home
- Deep linking support
- Updates nav tabs on route change

---

### **docs/js/ui.js** (NEW)
**Purpose:** Shared UI utilities  
**Exports:**
```javascript
- renderList(items, template)
- renderDetailPanel(data)
- renderMap(element, options)
- showLoading(element)
- showError(element, message)
- renderStats(stats)
- renderFilter(filters)
```

**Features:**
- DOM templating
- Loading/error states
- Common rendering patterns
- Consistent HTML structure

---

### **docs/js/home.js** (NEW)
**Purpose:** Home page logic  
**Exports:**
```javascript
- renderHome()
```

**Fetches from API:**
- /api/status (for stats)
- /api/v2/episodes (count)
- /api/v2/locations (count)
- /api/v2/theories (count)
- /api/v2/people (count)

---

### **docs/js/episodes.js** (UPDATED/NEW)
**Purpose:** Episodes section logic  
**Fetches from API:**
- /api/v2/episodes?season=N
- /api/v2/events?season=N

---

### **docs/js/locations.js** (UPDATED)
**Purpose:** Locations section logic  
**Fetches from API:**
- /api/v2/locations
- /api/v2/locations/:id
- /api/v2/events?location_id=X

---

### **docs/js/events.js** (NEW)
**Purpose:** Events timeline logic  
**Fetches from API:**
- /api/v2/events?location_id=X&season=Y&type=Z
- Pagination support

---

### **docs/js/artifacts.js** (NEW)
**Purpose:** Artifacts section logic  
**Fetches from API:**
- /api/v2/artifacts?location_id=X&season=Y&type=Z

---

### **docs/js/theories.js** (NEW)
**Purpose:** Theories section logic  
**Fetches from API:**
- /api/v2/theories
- /api/v2/theories/:id/mentions

---

### **docs/js/people.js** (NEW)
**Purpose:** People section logic  
**Fetches from API:**
- /api/v2/people
- /api/v2/people/:id

---

### **docs/js/app.js** (UPDATED)
**Purpose:** Bootstrap and initialization  
**Changes:**
- Remove old navigation logic
- Call router initialization instead
- Set default route to #/home
- Initialize API on page load

---

## 🎨 STYLING UPDATES

### **docs/styles.css** (SIGNIFICANT UPDATES)
**New design system:**
- Research center color scheme (dark blue + accent)
- Navigation bar styling
- Card/panel layout system
- Grid system for lists
- Detail panel sidebar
- Map container styling
- Timeline styling
- Filter controls
- Responsive mobile design

---

## 📊 LOADED FILES PER SECTION

| Section | HTML | JS | API Calls | Notes |
|---------|------|----|-----------|----|
| Home | home.html | home.js | /api/status, /api/v2/* | Stats + quick links |
| Episodes | episodes.html | episodes.js | /api/v2/episodes, /api/v2/events | Season filter |
| Locations | locations.html | locations.js | /api/v2/locations, /api/v2/events | Map + list |
| Events | events.html | events.js | /api/v2/events | Multiple filters |
| Artifacts | artifacts.html | artifacts.js | /api/v2/artifacts | Location/season filter |
| Theories | theories.html | theories.js | /api/v2/theories | Evidence sorted |
| People | people.html | people.js | /api/v2/people | Contributions |
| Chatbot | chatbot.html | chatbot.js | /api/semantic/* | Chat only |

---

## 📤 DEPLOYMENT CHECKLIST

- [ ] All HTML files created
- [ ] All JS modules created
- [ ] CSS updated with new design
- [ ] Router working (navigation switches sections)
- [ ] API calls working (data loads)
- [ ] Default route set to home
- [ ] Leaflet map working in locations section
- [ ] All sections load without errors
- [ ] Mobile responsive
- [ ] Works on Render without hardcoded URLs

---

## 🚀 IMPLEMENTATION SEQUENCE

1. **Phase 1: Foundation**
   - Update index.html with new navigation structure
   - Create api.js (centralized API client)
   - Create router.js (SPA routing)
   - Create ui.js (shared utilities)
   - Update app.js (bootstrap)

2. **Phase 2: Home Page**
   - Create home.html
   - Create home.js
   - Test routing and stats loading

3. **Phase 3: Content Sections**
   - Create episodes section
   - Create locations section (with map)
   - Create events section
   - Create artifacts section
   - Create theories section
   - Create people section
   - Create chatbot section (moved from default)

4. **Phase 4: Styling**
   - Update CSS for new design
   - Ensure responsive layout
   - Test on mobile

5. **Phase 5: Testing & Deployment**
   - Test all sections and navigation
   - Test on Render deployment
   - Verify all API calls work
   - Commit to GitHub

---

## 📝 SUMMARY

**Total New Files:** 9 (7 HTML sections + 2 CSS files)  
**Total New JS Modules:** 8  
**Updated Existing Files:** index.html, app.js, styles.css  
**Kept As-Is:** data.js, data_semantic_api.js, chatbot.js (preserved), map.js (refactored)

**Total Lines of Code:** ~3000-4000 lines  
**Time Estimate:** 2-3 hours to build + test

---

## ✋ NEXT STEP

Awaiting confirmation to proceed with implementation.

**Proceed with UI rebuild?** (Yes/No)
