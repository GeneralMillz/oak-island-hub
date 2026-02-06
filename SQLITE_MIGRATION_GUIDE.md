# Oak Island Hub: SQLite Architecture Migration Guide

## Overview

This document describes the transition from a **static JSON-based architecture** to a **dynamic SQLite database** with REST API endpoints. The migration is:

- ✅ **Additive**: Raw JSON files remain untouched
- ✅ **Reversible**: Can fall back to JSON at any time
- ✅ **Incremental**: Deploy in phases
- ✅ **Backward Compatible**: Existing endpoints continue working

## Architecture Comparison

### BEFORE: Static JSON
```
User Input → Frontend (JS) → Load large JSON files (5.1MB) → Render UI
```

**Issues:**
- All data loaded on page init (slow)
- Data duplication across files (people names, theories, events)
- No efficient filtering/searching
- Poor performance on low-end devices

### AFTER: SQLite + REST API
```
User Input → Frontend (JS) → API Endpoint → SQLite Query → Minimal JSON → Render UI
```

**Benefits:**
- Load only what's needed (locations list first)
- Efficient filtering & searching at database level
- Deduplication (single "Rick" record, not repeated 10,000 times)
- Pagination & lazy loading built-in
- 70-80% reduction in frontend data payload

## Data Architecture

### SQLite Schema

**8 main entities** (normalized):

```
LOCATIONS
  ├─ id TEXT PRIMARY KEY
  ├─ name TEXT UNIQUE
  ├─ type TEXT (shaft, landmark, feature, etc.)
  ├─ latitude REAL
  ├─ longitude REAL
  └─ description TEXT

EPISODES
  ├─ id TEXT PRIMARY KEY
  ├─ season INTEGER
  ├─ episode INTEGER
  ├─ title TEXT
  ├─ air_date TEXT
  └─ summary TEXT

PEOPLE
  ├─ id TEXT PRIMARY KEY
  ├─ name TEXT UNIQUE
  ├─ role TEXT (host, expert, researcher)
  └─ description TEXT

THEORIES
  ├─ id TEXT PRIMARY KEY
  ├─ name TEXT UNIQUE
  ├─ theory_type TEXT
  └─ description TEXT

EVENTS
  ├─ id INTEGER PRIMARY KEY
  ├─ season INTEGER
  ├─ episode INTEGER
  ├─ timestamp TEXT (HH:MM:SS.mmm)
  ├─ event_type TEXT
  ├─ text TEXT
  ├─ location_id TEXT FK
  └─ confidence REAL

ARTIFACTS
  ├─ id TEXT PRIMARY KEY
  ├─ name TEXT
  ├─ artifact_type TEXT
  ├─ location_id TEXT FK
  ├─ season INTEGER
  └─ episode INTEGER

MEASUREMENTS
  ├─ id TEXT PRIMARY KEY
  ├─ location_id TEXT FK
  ├─ measurement_type TEXT
  ├─ value REAL
  ├─ unit TEXT
  └─ confidence REAL

BOREHOLES
  ├─ id TEXT PRIMARY KEY
  ├─ location_id TEXT FK
  ├─ bore_number TEXT
  ├─ depth_meters REAL
  └─ description TEXT
```

### Deduplication Results

**Before (JSON):**
- people.json: 84,872 lines (mostly duplicate person names across episodes)
- theories.json: 34,841 lines (mostly duplicate theory mentions)
- events.json: 55,946 lines (granular, unindexed)
- **Total: 5.1MB**

**After (SQLite):**
- people table: ~100 unique people
- theories table: ~15 unique theories
- events table: ~55,946 records (but indexed, queryable)
- events consolidated into seasons/episodes/types
- **Estimated: 2-3MB database + 500KB JSON exports**

## Implementation Steps

### Step 1: Initialize SQLite Database

Run the ETL pipeline to populate the database from existing JSON files:

```bash
cd /home/pi/oak-island-hub

# Create database and load all data
python3 pipeline/etl_pipeline.py \
  --db-path ./data \
  --data-dir ./docs/data \
  --reset

# Output:
# ✅ Database created at ./data/oak_island_hub.db
# ✅ Loaded 5 locations
# ✅ Loaded 10+ seasons of episodes
# ✅ Extracted ~100 unique people
# ✅ Extracted ~15 unique theories
# ✅ Loaded 55k+ events
# ✅ Exported minimal JSON views for frontend
```

**Flags:**
- `--reset`: Drop existing database (safe; raw JSON intact)
- `--dry-run`: Show what would be loaded (no changes)
- `--db-path`: Directory for database (default: ./data)
- `--data-dir`: Source JSON directory (default: ./docs/data)

### Step 2: Deploy Updated API Server

**Option A: Replace existing server** (if fully tested)

```bash
# Backup current server
cp api_server.py api_server_backup.py

# Use new server with SQLite support
mv api_server_v2.py api_server.py

# Start server
python3 api_server.py --dev
```

**Option B: Run alongside existing server** (safer)

```bash
# Keep existing api_server.py on port 5000
python3 api_server.py &

# Run new server on different port
python3 api_server_v2.py --port 5001 &
```

### Step 3: Update Frontend (Phased)

**Phase 3A: Locations (minimal changes)**

Replace the static locations load in `docs/js/data.js`:

```javascript
// Old approach (before)
const locations = require('./locations.json');  // 4KB

// New approach (after)
async function loadLocations() {
    const response = await fetch('/api/v2/locations');
    return response.json();
}
```

**Phase 3B: Lazy-load events / artifacts**

Modify `docs/js/details.js` to fetch on demand:

```javascript
// When user clicks location detail view
async function showLocationDetails(locationId) {
    // Load detail from API (only when needed)
    const response = await fetch(`/api/v2/locations/${locationId}`);
    const location = await response.json();
    
    // location.events, location.artifacts, location.measurements
    renderDetails(location);
}
```

**Phase 3C: Search & filtering**

Update `docs/js/search.js` to use filtered API:

```javascript
async function findEventsByType(eventType, season) {
    const response = await fetch(
        `/api/v2/events?event_type=${eventType}&season=${season}`
    );
    return response.json();  // .events array
}
```

## Frontend Integration Examples

### Example 1: Load Locations (Map View)

```javascript
// In docs/js/data.js or new docs/js/api.js

const API_BASE = window.API_BASE || '/api/v2';

async function loadLocations() {
    try {
        const response = await fetch(`${API_BASE}/locations`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const locations = await response.json();
        window.locations = locations;
        
        // Fire event: locations loaded
        document.dispatchEvent(new CustomEvent('locationsLoaded', {
            detail: { count: locations.length }
        }));
        
        return locations;
    } catch (error) {
        console.error('Failed to load locations:', error);
        // Fallback to old JSON file
        return loadLocationsFromJSON();
    }
}
```

### Example 2: Lazy-load Events for Location

```javascript
// In docs/js/details.js

async function loadLocationEvents(locationId) {
    const response = await fetch(
        `${API_BASE}/events?location_id=${locationId}&limit=50`
    );
    
    if (!response.ok) {
        console.warn(`Failed to load events for ${locationId}`);
        return [];
    }
    
    const data = await response.json();
    return data.events;  // Array of events
}
```

### Example 3: Pagination

```javascript
async function loadEventsPage(page = 1, pageSize = 50) {
    const offset = (page - 1) * pageSize;
    
    const response = await fetch(
        `${API_BASE}/events?limit=${pageSize}&offset=${offset}`
    );
    
    const data = await response.json();
    
    return {
        events: data.events,
        total: data.total,
        page: page,
        pageSize: pageSize,
        totalPages: Math.ceil(data.total / pageSize)
    };
}
```

### Example 4: Searching (Filter by Type)

```javascript
async function findDiscoveryEvents(season, episode) {
    const response = await fetch(
        `${API_BASE}/events?event_type=discovery&season=${season}&episode=${episode}`
    );
    
    return (await response.json()).events;
}
```

## API Endpoints (v2)

### GET /api/v2/locations

Returns all locations (minimal list).

```bash
# Request
curl http://localhost:5000/api/v2/locations

# Response (4KB, vs 5.1MB full app load)
[
    {
        "id": "money_pit",
        "name": "Money Pit",
        "type": "shaft",
        "lat": 44.523550,
        "lng": -64.300020,
        "description": null
    },
    ...
]
```

### GET /api/v2/locations/:id

Returns location with related events, artifacts, measurements.

```bash
# Request
curl http://localhost:5000/api/v2/locations/money_pit

# Response (detailed view with related data)
{
    "id": "money_pit",
    "name": "Money Pit",
    "type": "shaft",
    "lat": 44.523550,
    "lng": -64.300020,
    "description": "...",
    "events": [
        {
            "season": 1,
            "episode": 1,
            "timestamp": "00:15:30.000",
            "event_type": "discovery",
            "text": "...",
            "confidence": 0.95
        }
    ],
    "artifacts": [...],
    "measurements": [...]
}
```

### GET /api/v2/events?location_id=...&season=...&event_type=...

Filtered events with pagination.

```bash
# Request: find all discoveries at Money Pit in season 2
curl "http://localhost:5000/api/v2/events?location_id=money_pit&season=2&event_type=discovery&limit=50"

# Response
{
    "events": [
        {
            "season": 2,
            "episode": 3,
            "timestamp": "00:22:15.601",
            "event_type": "discovery",
            "text": "...",
            "confidence": 0.95
        }
    ],
    "count": 1,
    "offset": 0,
    "total": 127
}
```

### GET /api/v2/artifacts?location_id=...

Find artifacts at a location.

```bash
curl "http://localhost:5000/api/v2/artifacts?location_id=smiths_cove"
```

### GET /api/v2/theories

List all theories.

```bash
curl http://localhost:5000/api/v2/theories
```

### GET /api/v2/people

List all people.

```bash
curl http://localhost:5000/api/v2/people
```

### GET /api/v2/episodes?season=...

List episodes for a season.

```bash
curl "http://localhost:5000/api/v2/episodes?season=3"
```

## Deployment Checklist

### Pre-Deployment
- [ ] Run ETL pipeline locally: `python3 etl_pipeline.py --reset`
- [ ] Test new API endpoints: `curl /api/v2/locations`
- [ ] Verify database exists: `ls -lh ./data/oak_island_hub.db`
- [ ] Run backend on test server: `python3 api_server_v2.py --dev`
- [ ] Test fallback (disable DB, verify JSON still works)

### Frontend Testing
- [ ] Update `docs/js/data.js` to load locations from API
- [ ] Test map renders with API data
- [ ] Test location click → detail view (lazy-loads events)
- [ ] Test search/filters use API endpoints
- [ ] Verify PI_MODE still works (add `?piMode=true` to API calls)

### Production Deployment
- [ ] Copy ETL script to server: `pipeline/etl_pipeline.py`
- [ ] Copy schema: `pipeline/schema.sql`
- [ ] Run ETL on server: `python3 etl_pipeline.py --reset`
- [ ] Deploy new API server (either replace or run on new port)
- [ ] Update frontend to use `/api/v2/` endpoints
- [ ] Monitor performance & errors
- [ ] Keep old JSON files as fallback (in .gitignore)

### Rollback Strategy
If issues arise:

```bash
# Disable new API, use old server
python3 api_server_backup.py

# Or delete database to force JSON fallback
rm ./data/oak_island_hub.db
```

## Performance Expectations

### Initial Load

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| First paint | 2-3s (load 5.1MB) | 500ms (load 4KB) | **5-6x faster** |
| Memory usage | 50MB (all data in JS) | 10MB (minimal set) | **80% less** |
| Initial API calls | 1-2 | 3+ (but parallel) | **More strategic** |

### Location Detail View

| Operation | Before | After | Method |
|-----------|--------|-------|--------|
| Click location | Instant (cached) | 50-100ms | API fetch |
| Load events | None (all loaded) | Fast (indexed query) | DB query on demand |
| Paginate events | N/A | 20-50ms | Offset/limit |

### Search

| Operation | Before | After | Method |
|-----------|--------|-------|--------|
| Full-text search | 100-500ms (JS) | 5-50ms | DB index lookup |
| Filter by type | 500ms+ (JS array) | 10ms | DB WHERE clause |

## Migration Timeline

**Phase 1 (Week 1): Database Setup**
- [ ] Create SQLite schema
- [ ] Develop ETL pipeline
- [ ] Test locally with full data load
- [ ] Verify deduplication

**Phase 2 (Week 2): API Development**
- [ ] Implement v2 endpoints
- [ ] Test with frontend
- [ ] Performance profiling
- [ ] Fallback logic

**Phase 3 (Week 3): Frontend Integration**
- [ ] Update locations loading
- [ ] Implement lazy-loading for details
- [ ] Update search/filter logic
- [ ] Test all browsers/devices

**Phase 4 (Week 4): Production**
- [ ] Deploy to production server
- [ ] Monitor error rates
- [ ] Verify performance
- [ ] Document for team

## Troubleshooting

### Database Not Found
```bash
# Check if exists
ls -lh ./data/oak_island_hub.db

# Recreate if missing
python3 pipeline/etl_pipeline.py --reset
```

### API Returns 500 Error
```bash
# Check server logs
# API will automatically fallback to JSON if DB unavailable
# Verify database permissions
chmod 644 ./data/oak_island_hub.db
```

### Frontend Gets Wrong Data
```javascript
// Check API is being called
console.log('Fetching from:', '/api/v2/locations');

// Verify response structure
fetch('/api/v2/locations')
    .then(r => r.json())
    .then(data => console.log(data));
```

## FAQ

**Q: Will this break existing functionality?**
A: No. The API server falls back to JSON if SQLite is unavailable. Existing endpoints still work.

**Q: How do I roll back?**
A: Delete the database (`rm ./data/oak_island_hub.db`). The API will automatically use JSON files.

**Q: Can I run both old and new API?**
A: Yes. Run `api_server.py` on port 5000 and `api_server_v2.py` on port 5001 simultaneously.

**Q: Do I need to delete raw JSON files?**
A: No. Keep them in `.gitignore` for backup and rollback scenarios.

**Q: What about PI_MODE?**
A: Works the same way. Pass `?piMode=true` to API calls to skip expensive operations (semantic data, full event lists).

**Q: How much space does the database take?**
A: ~2-3MB (vs 5.1MB JSON). Compression possible with SQLite vacuum.

## References

- **Schema**: `pipeline/schema.sql`
- **ETL Pipeline**: `pipeline/etl_pipeline.py`
- **API Server**: `api_server_v2.py`
- **Frontend Integration**: See examples above
- **Entities**: 8 normalized tables with FKs and indices

## Support

For issues or questions:
1. Check `api_server.py --help` for server options
2. Run `python3 etl_pipeline.py --dry-run` to preview changes
3. Check `/api/status` endpoint for database health
4. Review logs in terminal output
