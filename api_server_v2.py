#!/usr/bin/env python3
"""
Oak Island Hub Semantic API Server

REST API backed by normalized SQLite semantic database.

Provides efficient querying of:
- Locations (5 geographic locations)
- Episodes (244 TV episodes across 13 seasons)
- Events (6,216 discoveries/activities)
- Artifacts (81 physical objects found)
- Theories (16 canonical theories with 3,871+ mentions)
- People (25 key investigators + hosts)
- Measurements (2,758 scientific measurements)

Features:
  ✓ Zero external dependencies (stdlib only)
  ✓ CORS support for browser access
  ✓ Automatic fallback to JSON files if DB unavailable
  ✓ Pagination and filtering
  ✓ Full-text search across entities
  ✓ Comprehensive error handling

Usage:
    python3 api_server_v2.py                      # Production (localhost:5000)
    python3 api_server_v2.py --dev --port 8000   # Development mode

Environment:
    DATABASE_PATH=./oak_island_hub.db   Override database location
    FLASK_ENV=development               Enable debug logging
"""

from flask import Flask, request, jsonify, send_from_directory, make_response
from pathlib import Path
import sqlite3
import json
import logging
import argparse
from typing import Optional, Dict, List, Any, Tuple
from urllib.parse import quote_plus
import threading

# ============================================================================
# CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR / "docs"
DATA_DIR = APP_DIR / "data"
DB_PATH = BASE_DIR / "oak_island_hub.db"  # Semantic database path

app = Flask(__name__, static_folder=str(APP_DIR), static_url_path="")

# ============================================================================
# DATABASE MANAGER
# ============================================================================

    """Manages connections to semantic SQLite database with fallback to JSON."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.available = False
        self.json_cache = {}
        self._cache_lock = threading.Lock()

        # Check if database exists
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                conn.close()

                if table_count > 0:
                    self.available = True
                    logger.info(f"✓ Semantic database available: {db_path}")
                else:
                    logger.warning(f"✗ Database has no tables: {db_path}")
            except Exception as e:
                logger.warning(f"✗ Database check failed: {e}")
        else:
            logger.warning(f"✗ Database not found: {db_path}")
    
    def query_one(self, sql: str, params: Tuple = ()) -> Optional[Dict]:
        """Execute query and return single result as dict."""
        if not self.available:
            return None
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql, params)
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Query error: {e}")
            return None
    
    def query_all(self, sql: str, params: Tuple = ()) -> List[Dict]:
        """Execute query and return results as list of dicts."""
        if not self.available:
            return []
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql, params)
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Query error: {e}")
            return []

db = SemanticDB(DB_PATH)

# ============================================================================
# JSON FALLBACK HELPERS
# ============================================================================

    """Load optimized JSON slice with caching (thread-safe)."""
    cache_key = f"slice_{filename}"
    with db._cache_lock:
        if cache_key in db.json_cache:
            return db.json_cache[cache_key]

    path = DATA_DIR / f"{filename}_summary.json"
    if not path.exists():
        # Try alternate names
        path = DATA_DIR / f"{filename}.json"

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        with db._cache_lock:
            db.json_cache[cache_key] = data
        return data
    except Exception as e:
        logger.warning(f"Failed to load {filename}: {e}")
        return None

# ============================================================================
# CORS MIDDLEWARE
# ============================================================================

# CORS is enabled for all origins by default for public API/browser access.
# If you need to restrict CORS in production, set allowed_origins accordingly.
ALLOWED_ORIGINS = None  # Set to a list of allowed origins to restrict

@app.before_request
def handle_preflight():
    """Handle CORS preflight requests (OPTIONS)."""
    if request.method == "OPTIONS":
        origin = request.headers.get("Origin", "*")
        # If ALLOWED_ORIGINS is set, restrict CORS
        if ALLOWED_ORIGINS is not None and origin not in ALLOWED_ORIGINS:
            origin = "null"
        response = make_response("", 204)
        response.headers.add("Access-Control-Allow-Origin", origin)
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers.add("Access-Control-Allow-Methods", "GET, OPTIONS")
        response.headers.add("Access-Control-Max-Age", "3600")
        return response

@app.after_request
def add_cors_headers(response):
    """Add CORS headers to all responses."""
    origin = request.headers.get("Origin", "*")
    # If ALLOWED_ORIGINS is set, restrict CORS
    if ALLOWED_ORIGINS is not None and origin not in ALLOWED_ORIGINS:
        origin = "null"
    response.headers.add("Access-Control-Allow-Origin", origin)
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET, OPTIONS")
    response.headers.add("Vary", "Origin")
    return response

# ============================================================================
# API ENDPOINTS: LOCATIONS
# ============================================================================

@app.route('/api/v2/locations', methods=['GET'])
def get_locations():
    """Get all locations (minimal data for map initialization).
    
    Returns:
        [{
            "id": "money_pit",
            "name": "Money Pit",
            "type": "excavation",
            "lat": 44.52355,
            "lng": -64.30002
        }, ...]
    """
    if not db.available:
        data = load_json_slice("locations_min")
        return jsonify(data or [])
    
    locations = db.query_all("""
        SELECT id, name, type, latitude as lat, longitude as lng
        FROM locations
        ORDER BY name
    """)
    
    return jsonify(locations)

@app.route('/api/v2/locations/<location_id>', methods=['GET'])
def get_location_detail(location_id: str):
    """Get location with all related events, artifacts, and measurements.
    
    Args:
        location_id: Location identifier (e.g., 'money_pit')
    
    Returns:
        {
            "id": "money_pit",
            "name": "Money Pit",
            "type": "excavation",
            "lat": 44.52355,
            "lng": -64.30002,
            "events": [...],
            "artifacts": [...],
            "measurements": [...]
        }
    """
    if not db.available:
        data = load_json_slice("locations_min")
        for loc in (data or []):
            if loc.get('id') == location_id:
                return jsonify(loc)
        return jsonify({'error': 'Location not found'}), 404
    
    # Get location
    location = db.query_one("""
        SELECT id, name, type, latitude as lat, longitude as lng
        FROM locations
        WHERE id = ?
    """, (location_id,))
    
    if not location:
        return jsonify({'error': 'Location not found'}), 404
    
    # Get related events
    location['events'] = db.query_all("""
        SELECT season, episode, timestamp, event_type, text
        FROM events
        WHERE location_id = ?
        LIMIT 100
    """, (location_id,))
    
    # Get related artifacts
    location['artifacts'] = db.query_all("""
        SELECT id, name, artifact_type as type, season, episode, confidence
        FROM artifacts
        WHERE location_id = ?
        LIMIT 50
    """, (location_id,))
    
    # Get related measurements
    location['measurements'] = db.query_all("""
        SELECT measurement_type, value, unit, season, episode
        FROM measurements
        WHERE location_id = ?
        LIMIT 100
    """, (location_id,))
    
    return jsonify(location)

# ============================================================================
# API ENDPOINTS: EPISODES
# ============================================================================

@app.route('/api/v2/episodes', methods=['GET'])
def get_episodes():
    """Get episodes, optionally filtered by season.
    
    Query Parameters:
        season: Filter by season number (1-13)
    
    Returns:
        [{
            "id": "s01e01",
            "season": 1,
            "episode": 1,
            "title": "What Lies Below",
            "air_date": null
        }, ...]
    """
    season = request.args.get('season')
    
    if not db.available:
        data = load_json_slice("episodes_list")
        if season and data and isinstance(data, dict):
            season_data = data.get(f"season_{season}")
            return jsonify(season_data or [])
        return jsonify(data or {})
    
    if season:
        episodes = db.query_all("""
            SELECT id, season, episode, title, air_date
            FROM episodes
            WHERE season = ?
            ORDER BY episode
        """, (int(season),))
    else:
        episodes = db.query_all("""
            SELECT id, season, episode, title, air_date
            FROM episodes
            ORDER BY season, episode
        """)
    
    return jsonify(episodes)

# ============================================================================
# API ENDPOINTS: EVENTS
# ============================================================================

@app.route('/api/v2/events', methods=['GET'])
def get_events():
    """Get events with optional filtering and pagination.
    
    Query Parameters:
        location_id: Filter by location ID
        season: Filter by season
        episode: Filter by episode
        limit: Results per page (default 100, max 1000)
        offset: Pagination offset (default 0)
    
    Returns:
        {
            "total": 6216,
            "count": 100,
            "events": [...]
        }
    """
    if not db.available:
        return jsonify({'events': [], 'count': 0, 'total': 0})
    
    limit = min(int(request.args.get('limit', 100)), 1000)
    offset = int(request.args.get('offset', 0))
    
    where_clause = "WHERE 1=1"
    params = []
    
    if request.args.get('location_id'):
        where_clause += " AND location_id = ?"
        params.append(request.args.get('location_id'))
    
    if request.args.get('season'):
        where_clause += " AND season = ?"
        params.append(int(request.args.get('season')))
    
    if request.args.get('episode'):
        where_clause += " AND episode = ?"
        params.append(int(request.args.get('episode')))
    
    # Count total
    count_result = db.query_one(f"SELECT COUNT(*) as total FROM events {where_clause}", tuple(params))
    total = count_result['total'] if count_result else 0
    
    # Get paginated results
    params_with_limit = params + [limit, offset]
    events = db.query_all(f"""
        SELECT season, episode, timestamp, event_type, text, confidence
        FROM events
        {where_clause}
        ORDER BY season, episode, timestamp
        LIMIT ? OFFSET ?
    """, tuple(params_with_limit))
    
    return jsonify({
        'total': total,
        'count': len(events),
        'offset': offset,
        'events': events
    })

# ============================================================================
# API ENDPOINTS: ARTIFACTS
# ============================================================================

@app.route('/api/v2/artifacts', methods=['GET'])
def get_artifacts():
    """Get artifacts with optional filtering.
    
    Query Parameters:
        location_id: Filter by location
        season: Filter by season
        type: Filter by artifact type
    
    Returns:
        [{
            "id": "s01e04_a001_stone",
            "name": "Inscribed stone",
            "type": "artifact",
            "location_id": "money_pit",
            "season": 1,
            "episode": 4,
            "confidence": 0.95
        }, ...]
    """
    if not db.available:
        data = load_json_slice("artifacts_summary")
        return jsonify(data or [])
    
    where_clause = "WHERE 1=1"
    params = []
    
    if request.args.get('location_id'):
        where_clause += " AND location_id = ?"
        params.append(request.args.get('location_id'))
    
    if request.args.get('season'):
        where_clause += " AND season = ?"
        params.append(int(request.args.get('season')))
    
    if request.args.get('type'):
        where_clause += " AND type = ?"
        params.append(request.args.get('type'))
    
    artifacts = db.query_all(f"""
        SELECT id, name, artifact_type as type, location_id, season, episode, confidence FROM artifacts
        {where_clause}
        ORDER BY season, episode
    """, tuple(params))
    
    return jsonify(artifacts)

# ============================================================================
# API ENDPOINTS: THEORIES
# ============================================================================

@app.route('/api/v2/theories', methods=['GET'])
def get_theories():
    """Get all theories with mention counts and evidence.
    
    Returns:
        [{
            "id": "treasure",
            "name": "Hidden Treasure",
            "type": "primary",
            "evidence_count": 1605,
            "mentions": 1605
        }, ...]
    """
    if not db.available:
        data = load_json_slice("theories_summary")
        return jsonify(data or [])
    
    theories = db.query_all("""
        SELECT id, name, theory_type as type, evidence_count,
               (SELECT COUNT(*) FROM theory_mentions WHERE theory_id = theories.id) as mentions
        FROM theories
        ORDER BY evidence_count DESC
    """)
    
    return jsonify(theories)

@app.route('/api/v2/theories/<theory_id>/mentions', methods=['GET'])
def get_theory_mentions(theory_id: str):
    """Get all mentions of a specific theory.
    
    Query Parameters:
        season: Filter by season
        limit: Results per page
        offset: Pagination offset
    
    Returns:
        {
            "theory_id": "treasure",
            "total_mentions": 1605,
            "mentions": [...]
        }
    """
    if not db.available:
        return jsonify({'mentions': [], 'total': 0})
    
    limit = min(int(request.args.get('limit', 100)), 1000)
    offset = int(request.args.get('offset', 0))
    
    # Count
    count_result = db.query_one("""
        SELECT COUNT(*) as total FROM theory_mentions WHERE theory_id = ?
    """, (theory_id,))
    total = count_result['total'] if count_result else 0
    
    # Get mentions
    mentions = db.query_all("""
        SELECT season, episode, timestamp, text, confidence
        FROM theory_mentions
        WHERE theory_id = ?
        ORDER BY season, episode
        LIMIT ? OFFSET ?
    """, (theory_id, limit, offset))
    
    return jsonify({
        'theory_id': theory_id,
        'total_mentions': total,
        'mentions': mentions
    })

# ============================================================================
# API ENDPOINTS: PEOPLE
# ============================================================================

@app.route('/api/v2/people', methods=['GET'])
def get_people():
    """Get all people (hosts, experts, team members).
    
    Returns:
        [{
            "id": "rick_lagina",
            "name": "Rick Lagina",
            "role": "Fearless Leader",
            "mentions": 2655,
            "first_season": 1,
            "last_season": 13
        }, ...]
    """
    if not db.available:
        data = load_json_slice("people_summary")
        return jsonify(data or [])
    
    people = db.query_all("""
        SELECT id, name, role,
               (SELECT COUNT(*) FROM person_mentions WHERE person_id = people.id) as mentions,
               first_appearance_season as first_season, last_appearance_season as last_season
        FROM people
        ORDER BY name
    """)
    
    return jsonify(people)

@app.route('/api/v2/people/<person_id>', methods=['GET'])
def get_person_detail(person_id: str):
    """Get person details with all mentions across episodes.
    
    Query Parameters:
        season: Filter mentions by season
        limit: Results per page
    
    Returns:
        {
            "id": "rick_lagina",
            "name": "Rick Lagina",
            "role": "Fearless Leader",
            "mentions_total": 2655,
            "first_season": 1,
            "last_season": 13,
            "mentions": [...]
        }
    """
    if not db.available:
        data = load_json_slice("people_summary")
        for person in (data or []):
            if person.get('id') == person_id:
                return jsonify(person)
        return jsonify({'error': 'Person not found'}), 404
    
    person = db.query_one("""
        SELECT id, name, role, 
               first_appearance_season as first_season, 
               last_appearance_season as last_season
        FROM people
        WHERE id = ?
    """, (person_id,))
    
    if not person:
        return jsonify({'error': 'Person not found'}), 404
    
    limit = int(request.args.get('limit', 100))
    
    # Get mentions
    mentions = db.query_all("""
        SELECT season, episode, timestamp, text, confidence
        FROM person_mentions
        WHERE person_id = ?
        ORDER BY season, episode
        LIMIT ?
    """, (person_id, limit))
    
    person['mentions_total'] = len(mentions)
    person['mentions'] = mentions
    
    return jsonify(person)

# ============================================================================
# API ENDPOINTS: SEARCH
# ============================================================================

@app.route('/api/v2/search', methods=['GET'])
def search():
    """Full-text search across locations, theories, people, and artifacts.
    
    Query Parameters:
        q: Search query (required)
        type: Limit to entity type (location, theory, person, artifact)
        limit: Results per page (default 50)
    
    Returns:
        {
            "query": "treasure",
            "results": {
                "locations": [...],
                "theories": [...],
                "people": [...],
                "artifacts": [...]
            }
        }
    """
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'error': 'Query must be at least 2 characters'}), 400
    
    search_term = f"%{query}%"
    limit = int(request.args.get('limit', 50))
    
    results = {
        'query': query,
        'results': {
            'locations': [],
            'theories': [],
            'people': [],
            'artifacts': []
        }
    }
    
    if not db.available:
        return jsonify(results)
    
    # Search locations
    results['results']['locations'] = db.query_all("""
        SELECT id, name, type, latitude as lat, longitude as lng
        FROM locations
        WHERE name LIKE ?
        LIMIT ?
    """, (search_term, limit))
    
    # Search theories
    results['results']['theories'] = db.query_all("""
        SELECT id, name, theory_type as type, evidence_count
        FROM theories
        WHERE name LIKE ?
        LIMIT ?
    """, (search_term, limit))
    
    # Search people
    results['results']['people'] = db.query_all("""
        SELECT id, name, role, 
               first_appearance_season as first_season, 
               last_appearance_season as last_season
        FROM people
        WHERE name LIKE ?
        LIMIT ?
    """, (search_term, limit))
    
    # Search artifacts
    results['results']['artifacts'] = db.query_all("""
        SELECT id, name, artifact_type as type, location_id, season, episode
        FROM artifacts
        WHERE name LIKE ?
        LIMIT ?
    """, (search_term, limit))
    
    return jsonify(results)

# ============================================================================
# API ENDPOINTS: STATUS & HEALTH
# ============================================================================

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get API and database status.
    
    Returns:
        {
            "status": "ok",
            "database": {
                "available": true,
                "path": "/home/pi/oak-island-hub/oak_island_hub.db"
            },
            "version": "2.0"
        }
    """
    status_data = {
        'status': 'ok',
        'database': {
            'available': db.available,
            'path': str(DB_PATH) if db.available else None
        },
        'version': '2.0',
        'api': 'Semantic REST API'
    }
    
    if db.available:
        # Get database statistics
        stats = db.query_one("""
            SELECT 
                (SELECT COUNT(*) FROM locations) as locations,
                (SELECT COUNT(*) FROM episodes) as episodes,
                (SELECT COUNT(*) FROM people) as people,
                (SELECT COUNT(*) FROM theories) as theories,
                (SELECT COUNT(*) FROM events) as events,
                (SELECT COUNT(*) FROM artifacts) as artifacts,
                (SELECT COUNT(*) FROM measurements) as measurements
        """)
        if stats:
            status_data['counts'] = dict(stats)
    
    return jsonify(status_data)

# ============================================================================
# STATIC FILE SERVING
# ============================================================================

@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_static(path):
    """Serve static files from docs/ directory (SPA fallback)."""
    file_path = APP_DIR / path
    
    # Security: prevent directory traversal
    try:
        if not str(file_path.resolve()).startswith(str(APP_DIR.resolve())):
            return jsonify({'error': 'Access denied'}), 403
    except:
        return jsonify({'error': 'Invalid path'}), 400
    
    if file_path.is_file():
        return send_from_directory(str(APP_DIR), path)
    
    # Fallback to index.html for SPA routing
    if (APP_DIR / 'index.html').exists():
        return send_from_directory(str(APP_DIR), 'index.html')
    
    return jsonify({'error': 'Not found'}), 404



# ============================================================================
# ERROR HANDLERS
# ============================================================================


# --------------------------------------------------------------------------
# ERROR HANDLERS
# --------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors with structured logging and JSON."""
    logger.warning({
        'event': 'http_404',
        'path': request.path,
        'method': request.method,
        'remote_addr': request.remote_addr,
        'error': str(error)
    })
    return jsonify({
        'error': 'Not found',
        'status': 404,
        'path': request.path
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors with structured logging and JSON."""
    logger.error({
        'event': 'http_500',
        'path': request.path,
        'method': request.method,
        'remote_addr': request.remote_addr,
        'error': str(error)
    })
    return jsonify({
        'error': 'Internal server error',
        'status': 500,
        'path': request.path
    }), 500

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Oak Island Hub Semantic REST API Server'
    )
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--dev', action='store_true', help='Development mode')
    parser.add_argument('--db', type=str, help='Database path override')
    
    args = parser.parse_args()
    
    if args.db:
        import os
        os.environ['DATABASE_PATH'] = args.db
    
    logger.info("=" * 80)
    logger.info("Oak Island Hub Semantic API Server")
    logger.info("=" * 80)
    logger.info(f"  Static files: {APP_DIR}")
    logger.info(f"  Data directory: {DATA_DIR}")
    logger.info(f"  Database: {DB_PATH}")
    logger.info(f"  Available: {db.available}")
    logger.info(f"  Binding to: {args.host}:{args.port}")
    logger.info(f"  Debug mode: {args.dev}")
    logger.info("=" * 80)
    
    app.run(
        host=args.host,
        port=args.port,
        debug=args.dev,
        use_reloader=args.dev
    )
# api_server_v2.py


from flask import Flask, request, jsonify
from oak_chat.engine import answer_query
import logging

app = Flask(__name__)

# Use the root logger for consistency with the rest of the file
logger = logging.getLogger(__name__)

@app.post("/chat")
def chat():
    try:
        logger.info("Received /chat request from %s", request.remote_addr)
        try:
            data = request.get_json(force=True) or {}
        except Exception as e:
            logger.warning("Invalid JSON in /chat request: %s", e)
            return jsonify({"error": "Invalid JSON"}), 400

        user_query = data.get("query", "").strip()
        if not user_query:
            logger.info("/chat request missing 'query' field")
            return jsonify({"error": "Missing 'query'"}), 400

        try:
            result = answer_query(user_query)
        except Exception as exc:
            logger.exception("Error in answer_query for /chat: %s", exc)
            return jsonify({"error": "Internal server error"}), 500

        return jsonify({
            "answer": result.get("answer"),
            "route": result.get("route"),
        })
    except Exception as exc:
        logger.exception("Unexpected error in /chat endpoint: %s", exc)
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
