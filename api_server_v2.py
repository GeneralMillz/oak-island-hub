#!/usr/bin/env python3
"""
Oak Island Hub API Server with SQLite Support

This server provides:
1. Static file serving from docs/
2. Legacy JSON endpoint /api/semantic/query (chatbot)
3. NEW: SQLite-backed REST endpoints for efficient data querying
   - GET /api/v2/locations
   - GET /api/v2/locations/:id
   - GET /api/v2/events?location_id=...&season=...
   - GET /api/v2/artifacts?location_id=...
   - GET /api/v2/theories
   - GET /api/v2/people
   - GET /api/v2/episodes?season=...

The API gracefully falls back to JSON data if SQLite database is unavailable.

Usage:
    python3 api_server.py                          # Production (localhost:5000)
    python3 api_server.py --dev --port 8000       # Development
    
Environment Variables:
    FLASK_ENV=development         Enable debug mode
    DATABASE_PATH=./data          Path to oak_island_hub.db directory
    CHATBOT_API_BASE=http://...   Override chatbot endpoint
"""

from flask import Flask, request, jsonify, send_from_directory, make_response
from pathlib import Path
import json
import re
import sqlite3
import logging
from collections import defaultdict
from typing import Optional, Dict, List, Any

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR / "docs"  # Updated from app_public to docs
DATA_DIR = APP_DIR / "data"
DB_PATH = BASE_DIR / "data" / "oak_island_hub.db"

app = Flask(__name__, static_folder=str(APP_DIR), static_url_path="")

# ============================================================================
# CORS MIDDLEWARE
# ============================================================================

@app.before_request
def handle_preflight():
    """Handle CORS preflight requests."""
    if request.method == "OPTIONS":
        response = make_response("", 204)
        response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin", "*"))
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        response.headers.add("Access-Control-Max-Age", "3600")
        return response
    return None

@app.after_request
def add_cors_headers(response):
    """Add CORS headers to all responses."""
    response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin", "*"))
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    response.headers.add("Access-Control-Max-Age", "3600")
    response.headers.add("Vary", "Origin")
    return response

# ============================================================================
# DATABASE UTILITIES
# ============================================================================

class SQLiteDB:
    """SQLite database connection manager with read-only access."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.available = db_path.exists()
        
        if self.available:
            try:
                # Test connection
                conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
                conn.execute("SELECT 1")
                conn.close()
                logger.info(f"SQLite database available: {self.db_path}")
            except Exception as e:
                logger.warning(f"SQLite database check failed: {e}")
                self.available = False
    
    def query(self, sql: str, params: tuple = ()) -> List[Dict]:
        """Execute read-only query and return results as list of dicts."""
        if not self.available:
            return []
        
        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql, params)
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return []

db = SQLiteDB(DB_PATH)

# ============================================================================
# DATA CACHE (for JSON fallback)
# ============================================================================

DATA_CACHE = {}

def load_json(path: Path) -> Any:
    """Load JSON file with caching."""
    if str(path) in DATA_CACHE:
        return DATA_CACHE[str(path)]
    
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        DATA_CACHE[str(path)] = data
        return data
    except Exception as e:
        logger.error(f"Failed to load JSON {path}: {e}")
        return None

def normalize(text: str) -> str:
    """Normalize text for comparison."""
    return re.sub(r"\s+", " ", (text or "").strip().lower())

# ============================================================================
# LEGACY: KNOWLEDGE BASE (for backward compatibility)
# ============================================================================

class KnowledgeBase:
    """Unified knowledge loader for all Oak Island datasets (JSON-based fallback)."""
    
    def __init__(self, data_dir: Path, pi_mode: bool = False):
        self.data_dir = Path(data_dir)
        self.pi_mode = pi_mode
        self.oak_data = self._load_oak_data()
        self.episodes = self._load_episodes()
        self.people = self._load_people()
        self.theories = self._load_theories()
        self.events = self._load_events()
        self.locations = self._load_locations()
        self.measurements = self._load_measurements()
        self.artifacts = self._build_artifacts()
        self.indices = self._build_indices()
    
    def _load_oak_data(self) -> Dict:
        """Load primary Oak Island dataset."""
        return load_json(self.data_dir / "oak_island_data.json") or {}
    
    def _load_episodes(self) -> List:
        """Load episodes dataset."""
        data = load_json(self.data_dir / "episodes.json")
        if isinstance(data, dict) and "episodes" in data:
            return data["episodes"]
        return data or []
    
    def _load_people(self) -> List:
        """Load people dataset (skip in PI_MODE)."""
        if self.pi_mode:
            return []
        return load_json(self.data_dir / "people.json") or []
    
    def _load_theories(self) -> List:
        """Load theories dataset (skip in PI_MODE)."""
        if self.pi_mode:
            return []
        return load_json(self.data_dir / "theories.json") or []
    
    def _load_events(self) -> List:
        """Load events dataset (skip in PI_MODE)."""
        if self.pi_mode:
            return []
        return load_json(self.data_dir / "events.json") or []
    
    def _load_locations(self) -> List:
        """Load locations dataset."""
        return load_json(self.data_dir / "locations.json") or []
    
    def _load_measurements(self) -> List:
        """Load measurements dataset (skip in PI_MODE)."""
        if self.pi_mode:
            return []
        return load_json(self.data_dir / "measurements.json") or []
    
    def _build_artifacts(self) -> List:
        """Extract artifacts from events and locations."""
        artifacts = []
        # This can be enhanced to extract actual artifact references
        return artifacts
    
    def _build_indices(self) -> Dict:
        """Build inverted indices for fast lookup."""
        indices = {
            'people_by_name': {},
            'locations_by_id': {},
            'theories_by_name': {},
            'events_by_type': defaultdict(list),
        }
        
        for person in self.people:
            if isinstance(person, dict) and 'person' in person:
                indices['people_by_name'][normalize(person['person'])] = person
        
        for location in self.locations:
            if isinstance(location, dict) and 'id' in location:
                indices['locations_by_id'][location['id']] = location
        
        for theory in self.theories:
            if isinstance(theory, dict) and 'theory' in theory:
                indices['theories_by_name'][normalize(theory['theory'])] = theory
        
        for event in self.events:
            if isinstance(event, dict) and 'event_type' in event:
                indices['events_by_type'][event['event_type']].append(event)
        
        return indices

KNOWLEDGE_BASE: Optional[KnowledgeBase] = None

def get_knowledge_base(pi_mode: bool = False) -> KnowledgeBase:
    """Get or initialize the global knowledge base."""
    global KNOWLEDGE_BASE
    if KNOWLEDGE_BASE is None:
        KNOWLEDGE_BASE = KnowledgeBase(DATA_DIR, pi_mode=pi_mode)
    return KNOWLEDGE_BASE

# ============================================================================
# NEW: SQLITE-BACKED ENDPOINTS (API v2)
# ============================================================================

@app.route('/api/v2/locations', methods=['GET'])
def get_locations_v2():
    """Get all locations from SQLite database.
    
    Response:
        [
            {
                "id": "money_pit",
                "name": "Money Pit",
                "type": "shaft",
                "lat": 44.523550,
                "lng": -64.300020,
                "description": "..."
            },
            ...
        ]
    """
    if not db.available:
        # Fallback to JSON
        kb = get_knowledge_base(request.args.get('piMode') == 'true')
        return jsonify(kb.locations)
    
    results = db.query("SELECT id, name, type, latitude, longitude, description FROM locations")
    
    # Convert to expected format
    locations = [
        {
            'id': r['id'],
            'name': r['name'],
            'type': r['type'],
            'lat': r['latitude'],
            'lng': r['longitude'],
            'description': r['description']
        }
        for r in results
    ]
    
    return jsonify(locations)

@app.route('/api/v2/locations/<location_id>', methods=['GET'])
def get_location_v2(location_id: str):
    """Get a single location by ID with related events and artifacts.
    
    Response:
        {
            "id": "money_pit",
            "name": "Money Pit",
            "type": "shaft",
            "lat": 44.523550,
            "lng": -64.300020,
            "description": "...",
            "events": [...],
            "artifacts": [...],
            "measurements": [...]
        }
    """
    if not db.available:
        kb = get_knowledge_base(request.args.get('piMode') == 'true')
        for loc in kb.locations:
            if loc.get('id') == location_id:
                return jsonify(loc)
        return jsonify({'error': 'Location not found'}), 404
    
    # Get location
    locations = db.query(
        "SELECT id, name, type, latitude, longitude, description FROM locations WHERE id = ?",
        (location_id,)
    )
    
    if not locations:
        return jsonify({'error': 'Location not found'}), 404
    
    location = locations[0]
    location['lat'] = location.pop('latitude')
    location['lng'] = location.pop('longitude')
    
    # Get related events
    location['events'] = db.query(
        """SELECT season, episode, timestamp, event_type, text, confidence 
           FROM events WHERE location_id = ? LIMIT 50""",
        (location_id,)
    )
    
    # Get related artifacts
    location['artifacts'] = db.query(
        """SELECT id, name, description, artifact_type, season, episode 
           FROM artifacts WHERE location_id = ? LIMIT 20""",
        (location_id,)
    )
    
    # Get related measurements
    location['measurements'] = db.query(
        """SELECT measurement_type, value, unit, season, episode 
           FROM measurements WHERE location_id = ? LIMIT 50""",
        (location_id,)
    )
    
    return jsonify(location)

@app.route('/api/v2/events', methods=['GET'])
def get_events_v2():
    """Get events with optional filtering.
    
    Query Parameters:
        location_id: Filter by location
        season: Filter by season
        episode: Filter by episode
        event_type: Filter by type
        limit: Results per page (default 100, max 1000)
        offset: Pagination offset (default 0)
    
    Response:
        {
            "total": 12345,
            "count": 100,
            "offset": 0,
            "events": [...]
        }
    """
    if not db.available:
        kb = get_knowledge_base(request.args.get('piMode') == 'true')
        events = kb.events
        
        # Apply filters
        if request.args.get('location_id'):
            # No location filtering in JSON
            pass
        if request.args.get('season'):
            season = request.args.get('season')
            events = [e for e in events if str(e.get('season')) == season]
        
        return jsonify({'events': events[:100], 'count': len(events), 'total': len(events)})
    
    # Build query
    sql = "SELECT season, episode, timestamp, event_type, text, confidence FROM events WHERE 1=1"
    params = []
    
    if request.args.get('location_id'):
        sql += " AND location_id = ?"
        params.append(request.args.get('location_id'))
    
    if request.args.get('season'):
        sql += " AND season = ?"
        params.append(int(request.args.get('season')))
    
    if request.args.get('episode'):
        sql += " AND episode = ?"
        params.append(int(request.args.get('episode')))
    
    if request.args.get('event_type'):
        sql += " AND event_type = ?"
        params.append(request.args.get('event_type'))
    
    # Count total
    count_sql = f"SELECT COUNT(*) as count FROM ({sql})"
    count_result = db.query(count_sql, tuple(params))
    total = count_result[0]['count'] if count_result else 0
    
    # Apply pagination
    limit = min(int(request.args.get('limit', 100)), 1000)
    offset = int(request.args.get('offset', 0))
    
    sql += f" LIMIT {limit} OFFSET {offset}"
    
    events = db.query(sql, tuple(params))
    
    return jsonify({
        'events': events,
        'count': len(events),
        'offset': offset,
        'total': total
    })

@app.route('/api/v2/artifacts', methods=['GET'])
def get_artifacts_v2():
    """Get artifacts with optional filtering.
    
    Query Parameters:
        location_id: Filter by location
        artifact_type: Filter by type
        season: Filter by season
    """
    if not db.available:
        # Fallback to JSON or empty
        return jsonify({'artifacts': [], 'count': 0})
    
    sql = "SELECT id, name, description, artifact_type, location_id, season, episode FROM artifacts WHERE 1=1"
    params = []
    
    if request.args.get('location_id'):
        sql += " AND location_id = ?"
        params.append(request.args.get('location_id'))
    
    if request.args.get('artifact_type'):
        sql += " AND artifact_type = ?"
        params.append(request.args.get('artifact_type'))
    
    if request.args.get('season'):
        sql += " AND season = ?"
        params.append(int(request.args.get('season')))
    
    limit = min(int(request.args.get('limit', 100)), 1000)
    offset = int(request.args.get('offset', 0))
    
    sql += f" LIMIT {limit} OFFSET {offset}"
    
    artifacts = db.query(sql, tuple(params))
    
    return jsonify({
        'artifacts': artifacts,
        'count': len(artifacts)
    })

@app.route('/api/v2/theories', methods=['GET'])
def get_theories_v2():
    """Get all theories.
    
    Response:
        [
            {"id": "treasure", "name": "Treasure", "type": "treasure"},
            ...
        ]
    """
    if not db.available:
        kb = get_knowledge_base(request.args.get('piMode') == 'true')
        theories = [{'name': t.get('theory')} for t in kb.theories if 'theory' in t]
        return jsonify(theories)
    
    theories = db.query("SELECT id, name, theory_type FROM theories ORDER BY name")
    return jsonify(theories)

@app.route('/api/v2/people', methods=['GET'])
def get_people_v2():
    """Get all people.
    
    Response:
        [
            {"id": "rick_lagina", "name": "Rick Lagina", "role": "host"},
            ...
        ]
    """
    if not db.available:
        kb = get_knowledge_base(request.args.get('piMode') == 'true')
        people = [{'name': p.get('person')} for p in kb.people if 'person' in p]
        return jsonify(people)
    
    people = db.query("SELECT id, name, role FROM people ORDER BY name")
    return jsonify(people)

@app.route('/api/v2/episodes', methods=['GET'])
def get_episodes_v2():
    """Get episodes with optional season filter.
    
    Query Parameters:
        season: Filter by season number
    """
    if not db.available:
        kb = get_knowledge_base(request.args.get('piMode') == 'true')
        return jsonify(kb.episodes)
    
    sql = "SELECT id, season, episode, title, air_date, summary FROM episodes WHERE 1=1"
    params = []
    
    if request.args.get('season'):
        sql += " AND season = ?"
        params.append(int(request.args.get('season')))
    
    sql += " ORDER BY season, episode"
    
    episodes = db.query(sql, tuple(params))
    return jsonify(episodes)

# ============================================================================
# LEGACY: SEMANTIC/CHATBOT ENDPOINT (preserved for backward compatibility)
# ============================================================================

@app.post("/api/semantic/query")
def semantic_query():
    """
    Legacy endpoint: Query semantic knowledge base for chatbot.
    
    Request:
        {
            "query": "What is at Smith's Cove?",
            "piMode": false
        }
    
    Response:
        {
            "answer": "...",
            "sources": [...],
            "confidence": 0.95
        }
    """
    payload = request.get_json() or {}
    query = payload.get("query", "").strip()
    pi_mode = payload.get("piMode", False)
    
    if not query:
        return jsonify({"error": "Query is required"}), 400
    
    kb = get_knowledge_base(pi_mode=pi_mode)
    
    # Simple keyword-based search
    query_norm = normalize(query)
    keywords = query_norm.split()
    
    # Search locations
    matching_locations = []
    for loc in kb.locations:
        if all(kw in normalize(loc.get('name', '')) for kw in keywords):
            matching_locations.append(loc)
    
    # Build response
    response = {
        "answer": f"Found {len(matching_locations)} matching locations",
        "locations": matching_locations,
        "sources": [],
        "confidence": 0.8 if matching_locations else 0.0
    }
    
    return jsonify(response)

# ============================================================================
# STATIC FILE SERVING
# ============================================================================

@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_static(path):
    """Serve static files from docs/ directory."""
    file_path = APP_DIR / path
    
    # Security: prevent directory traversal
    if not str(file_path.resolve()).startswith(str(APP_DIR.resolve())):
        return jsonify({"error": "Access denied"}), 403
    
    if file_path.is_file():
        return send_from_directory(str(APP_DIR), path)
    
    # Fallback to index.html for SPA routing
    if (APP_DIR / 'index.html').exists():
        return send_from_directory(str(APP_DIR), 'index.html')
    
    return jsonify({"error": "Not found"}), 404

# ============================================================================
# STATUS AND HEALTH CHECKS
# ============================================================================

@app.route('/api/status', methods=['GET'])
def status():
    """Check API and database status."""
    return jsonify({
        'status': 'ok',
        'database': {
            'available': db.available,
            'path': str(DB_PATH) if db.available else None
        },
        'version': '2.0',
        'features': ['REST API v2 (SQLite)', 'Legacy Semantic Query (JSON)']
    })

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error"}), 500

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Oak Island Hub API Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--dev', action='store_true', help='Development mode')
    
    args = parser.parse_args()
    
    logger.info(f"Starting Oak Island Hub API Server")
    logger.info(f"  Static files: {APP_DIR}")
    logger.info(f"  Data files: {DATA_DIR}")
    logger.info(f"  Database: {DB_PATH} (available: {db.available})")
    logger.info(f"  Binding to {args.host}:{args.port}")
    
    app.run(
        host=args.host,
        port=args.port,
        debug=args.dev,
        use_reloader=args.dev
    )
