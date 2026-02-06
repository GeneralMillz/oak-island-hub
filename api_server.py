#!/usr/bin/env python3
from flask import Flask, request, jsonify, send_from_directory, make_response
from pathlib import Path
import json
import re
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR / "app_public"
DATA_DIR = APP_DIR / "data"

app = Flask(__name__, static_folder=str(APP_DIR), static_url_path="")

@app.before_request
def handle_preflight():
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
  response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin", "*"))
  response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
  response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
  response.headers.add("Access-Control-Max-Age", "3600")
  response.headers.add("Vary", "Origin")
  return response

DATA_CACHE = {}
KNOWLEDGE_BASE = None


def load_json(path):
  """Load JSON file with caching."""
  if path in DATA_CACHE:
    return DATA_CACHE[path]
  with Path(path).open("r", encoding="utf-8") as f:
    data = json.load(f)
  DATA_CACHE[path] = data
  return data


def normalize(text):
  """Normalize text for comparison."""
  return re.sub(r"\s+", " ", (text or "").strip().lower())


# ============================================================================
# KNOWLEDGE BASE CLASS
# ============================================================================

class KnowledgeBase:
  """Unified knowledge loader for all Oak Island datasets."""
  
  def __init__(self, data_dir, pi_mode=False):
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
  
  def _load_oak_data(self):
    """Load primary Oak Island dataset."""
    return load_json(self.data_dir / "oak_island_data.json") or {}
  
  def _load_episodes(self):
    """Load episodes dataset."""
    data = load_json(self.data_dir / "episodes.json")
    if isinstance(data, dict) and "episodes" in data:
      return data["episodes"]
    return data or []
  
  def _load_people(self):
    """Load people dataset (skip in PI_MODE)."""
    if self.pi_mode:
      return []
    return load_json(self.data_dir / "people.json") or []
  
  def _load_theories(self):
    """Load theories dataset (skip in PI_MODE)."""
    if self.pi_mode:
      return []
    return load_json(self.data_dir / "theories.json") or []
  
  def _load_events(self):
    """Load events dataset (skip in PI_MODE)."""
    if self.pi_mode:
      return []
    return load_json(self.data_dir / "events.json") or []
  
  def _load_locations(self):
    """Load locations dataset."""
    return load_json(self.data_dir / "locations.json") or []
  
  def _load_measurements(self):
    """Load measurements dataset (skip in PI_MODE)."""
    if self.pi_mode:
      return []
    return load_json(self.data_dir / "measurements.json") or []
  
  def _build_artifacts(self):
    """Extract artifacts from locations."""
    artifacts = []
    for loc in self.oak_data.get("locations", []):
      for art in (loc.get("artifacts") or []):
        artifacts.append({
          "name": art.get("name") or art.get("artifact"),
          "location": loc.get("name"),
          "type": art.get("type"),
          "raw": art
        })
    return artifacts
  
  def _build_indices(self):
    """Build searchable indices across all datasets."""
    indices = {
      "episodes_by_number": {},
      "people_by_name": defaultdict(list),
      "theories_by_type": defaultdict(list),
      "events_by_type": defaultdict(list),
      "locations_by_name": {},
      "artifacts_by_name": {},
      "full_text": defaultdict(list)
    }
    
    # Index episodes
    for ep in self.episodes:
      key = f"{ep.get('season')}_{ep.get('episode')}"
      indices["episodes_by_number"][key] = ep
    
    # Index people
    for person_record in self.people:
      person_name = person_record.get("person", "").strip()
      if person_name:
        indices["people_by_name"][normalize(person_name)].append(person_record)
        indices["full_text"][normalize(person_name)].append(("person", person_record))
    
    # Index theories
    for theory_record in self.theories:
      theory_type = theory_record.get("theory", "").strip()
      if theory_type:
        indices["theories_by_type"][normalize(theory_type)].append(theory_record)
        indices["full_text"][normalize(theory_type)].append(("theory", theory_record))
    
    # Index events
    for event_record in self.events:
      event_type = event_record.get("event_type", "").strip()
      if event_type:
        indices["events_by_type"][normalize(event_type)].append(event_record)
        indices["full_text"][normalize(event_type)].append(("event", event_record))
    
    # Index locations
    for loc in self.locations:
      loc_name = loc.get("name", "").strip()
      if loc_name:
        indices["locations_by_name"][normalize(loc_name)] = loc
        indices["full_text"][normalize(loc_name)].append(("location", loc))
    
    # Index artifacts
    for art in self.artifacts:
      art_name = art.get("name", "").strip()
      if art_name:
        indices["artifacts_by_name"][normalize(art_name)] = art
        indices["full_text"][normalize(art_name)].append(("artifact", art))
    
    return indices
  
  def search(self, query, limit=10):
    """Full-text search across all entity types."""
    q = normalize(query)
    results = {"episodes": [], "people": [], "theories": [], "events": [], "locations": [], "artifacts": []}
    
    if not q:
      return results
    
    for key, entities in self.indices["full_text"].items():
      if q in key:
        for entity_type, entity in entities[:limit]:
          if entity_type not in results:
            results[entity_type] = []
          if len(results[entity_type]) < limit:
            results[entity_type].append(entity)
    
    return results
  
  def get_episode_details(self, season, episode):
    """Get all details for a specific episode."""
    key = f"{season}_{episode}"
    ep = self.indices["episodes_by_number"].get(key)
    
    if not ep:
      return None
    
    details = {"episode": ep, "people": [], "theories": [], "events": [], "artifacts": []}
    
    for person_rec in self.people:
      if person_rec.get("season") == str(season) and person_rec.get("episode") == str(episode):
        details["people"].append(person_rec)
    
    for theory_rec in self.theories:
      if theory_rec.get("season") == str(season) and theory_rec.get("episode") == str(episode):
        details["theories"].append(theory_rec)
    
    for event_rec in self.events:
      if event_rec.get("season") == str(season) and event_rec.get("episode") == str(episode):
        details["events"].append(event_rec)
    
    return details
  
  def get_location_details(self, location_name):
    """Get all details for a location."""
    norm_name = normalize(location_name)
    loc = self.indices["locations_by_name"].get(norm_name)
    
    if not loc:
      return None
    
    details = {"location": loc, "episodes": [], "artifacts": [], "theories": [], "events": []}
    
    for art in self.artifacts:
      if normalize(art.get("location", "")) == norm_name:
        details["artifacts"].append(art)
    
    for theory_rec in self.theories:
      if normalize(theory_rec.get("text", "")).find(normalize(loc.get("name"))) >= 0:
        if len(details["theories"]) < 5:
          details["theories"].append(theory_rec)
    
    for event_rec in self.events:
      if normalize(event_rec.get("text", "")).find(normalize(loc.get("name"))) >= 0:
        if len(details["events"]) < 5:
          details["events"].append(event_rec)
    
    return details
  
  def search_by_episode(self, season, episode, limit=5):
    """Get all data for an episode."""
    return self.get_episode_details(season, episode)
  
  def search_by_location(self, location_name, limit=5):
    """Get all data for a location."""
    return self.get_location_details(location_name)
  
  def search_by_keyword(self, keyword, limit=10):
    """Search across all datasets by keyword."""
    return self.search(keyword, limit)


def get_knowledge_base(pi_mode=False):
  """Get or create knowledge base singleton."""
  global KNOWLEDGE_BASE
  if KNOWLEDGE_BASE is None:
    KNOWLEDGE_BASE = KnowledgeBase(DATA_DIR, pi_mode=pi_mode)
  return KNOWLEDGE_BASE


# ============================================================================
# SEMANTIC QUERY HANDLER
# ============================================================================

def infer_intent(query):
  """Detect user intent from natural language query."""
  q = normalize(query)
  
  if any(word in q for word in ["connect", "connection", "between", "relates"]):
    return "connection"
  if q.startswith("summarize") or q.startswith("summary") or "summary" in q:
    return "summary"
  if any(word in q for word in ["timeline", "when", "year", "history"]):
    return "timeline"
  if any(word in q for word in ["episode", "season"]):
    return "episode"
  if any(word in q for word in ["theory", "theories", "explain"]):
    return "theory"
  if any(word in q for word in ["artifact", "artifacts", "find", "treasure", "discover"]):
    return "artifact"
  if any(word in q for word in ["location", "where", "place", "pit", "cove", "shaft"]):
    return "location"
  if any(word in q for word in ["person", "people", "who", "name"]):
    return "person"
  if "event" in q or "happen" in q:
    return "event"
  
  return "search"


def build_entity_card(entity_type, entity, kb):
  """Build a rich card for an entity."""
  if entity_type == "episode":
    return {
      "title": f"S{entity.get('season')}E{entity.get('episode')} - {entity.get('title', 'Untitled')}",
      "type": "episode",
      "summary": f"Season {entity.get('season')}, Episode {entity.get('episode')}",
      "data": entity
    }
  elif entity_type == "location":
    return {
      "title": entity.get("name", "Unknown Location"),
      "type": "location",
      "summary": f"{entity.get('type', 'Location')} at ({entity.get('lat'):.4f}, {entity.get('lng'):.4f})",
      "data": entity
    }
  elif entity_type == "artifact":
    return {
      "title": entity.get("name", "Unknown Artifact"),
      "type": "artifact",
      "summary": f"Found at {entity.get('location', 'Unknown')}",
      "data": entity.get("raw", entity)
    }
  elif entity_type == "person":
    return {
      "title": entity.get("person", "Unknown"),
      "type": "person",
      "summary": f"Person mentioned in series",
      "data": entity
    }
  elif entity_type == "theory":
    return {
      "title": entity.get("theory", "Unknown Theory"),
      "type": "theory",
      "summary": entity.get("text", "")[:100],
      "data": entity
    }
  elif entity_type == "event":
    return {
      "title": entity.get("event_type", "Event"),
      "type": "event",
      "summary": entity.get("text", "")[:100],
      "data": entity
    }
  
  return {"title": str(entity), "type": entity_type, "data": entity}


def semantic_query_handler(query, pi_mode=False):
  """Main semantic query processor."""
  kb = get_knowledge_base(pi_mode=pi_mode)
  intent = infer_intent(query)
  
  response = {
    "query": query,
    "intent": intent,
    "mode": "PI_MODE" if pi_mode else "WEB_MODE",
    "title": "Search Results",
    "summary": "",
    "entities": [],
    "related_entities": {},
    "suggestions": [
      "What happened at Smith's Cove?",
      "Tell me about the Money Pit",
      "Which episodes mention treasure?",
      "Who is Rick Lagina?",
      "Timeline for Garden Shaft"
    ]
  }
  
  # LOCATION INTENT
  if intent == "location":
    terms = query.replace("where", "").replace("location", "").strip()
    results = kb.search(terms, limit=3)
    
    if results.get("locations"):
      loc = results["locations"][0]
      details = kb.get_location_details(loc.get("name", ""))
      response["title"] = loc.get("name", "Unknown Location")
      response["summary"] = f"Location: {loc.get('name')}. Type: {loc.get('type')}."
      response["entities"] = [build_entity_card("location", loc, kb)]
      
      if details:
        response["related_entities"] = {
          "artifacts_found": [a.get("name") for a in details.get("artifacts", [])[:5]],
          "theories_mentioned": len(details.get("theories", [])),
          "events_recorded": len(details.get("events", []))
        }
  
  # EPISODE INTENT
  elif intent == "episode":
    import re as regex
    match = regex.search(r"s(\d+)e(\d+)|season\s+(\d+).*episode\s+(\d+)", query, regex.IGNORECASE)
    if match:
      season = match.group(1) or match.group(3)
      episode = match.group(2) or match.group(4)
      details = kb.get_episode_details(int(season), int(episode))
      
      if details and details["episode"]:
        ep = details["episode"]
        response["title"] = f"S{season}E{episode} - {ep.get('title', 'Unknown')}"
        response["summary"] = f"Season {season}, Episode {episode}"
        response["entities"] = [build_entity_card("episode", ep, kb)]
        response["related_entities"] = {
          "people_featured": list(set([p.get("person") for p in details.get("people", [])[:5]])),
          "events_covered": len(details.get("events", [])),
          "theories_discussed": len(details.get("theories", []))
        }
    else:
      results = kb.search(query, limit=5)
      if results.get("episodes"):
        response["title"] = "Episode Search Results"
        response["summary"] = f"Found {len(results['episodes'])} matching episodes"
        response["entities"] = [build_entity_card("episode", ep, kb) for ep in results["episodes"][:5]]
  
  # ARTIFACT INTENT
  elif intent == "artifact":
    results = kb.search(query, limit=5)
    if results.get("artifacts"):
      response["title"] = "Artifact Search"
      response["summary"] = f"Found {len(results['artifacts'])} matching artifacts"
      response["entities"] = [build_entity_card("artifact", art, kb) for art in results["artifacts"][:5]]
    else:
      response["summary"] = "No artifacts found matching your query."
  
  # PERSON INTENT
  elif intent == "person":
    results = kb.search(query, limit=3)
    if results.get("people"):
      response["title"] = "Person Search"
      response["summary"] = f"Found {len(results['people'])} mentions"
      response["entities"] = [build_entity_card("person", p, kb) for p in results["people"][:5]]
    else:
      response["summary"] = "No people found matching your query."
  
  # THEORY INTENT
  elif intent == "theory":
    if pi_mode:
      response["summary"] = "Theories are not available in PI_MODE. Switch to WEB_MODE for full semantic analysis."
      response["mode"] = "PI_MODE (limited)"
    else:
      results = kb.search(query, limit=5)
      if results.get("theories"):
        response["title"] = "Theory Search"
        response["summary"] = f"Found {len(results['theories'])} theory mentions"
        response["entities"] = [build_entity_card("theory", t, kb) for t in results["theories"][:5]]
      else:
        response["summary"] = "No theories found matching your query."
  
  # SUMMARY INTENT
  elif intent == "summary":
    query_clean = query.replace("summarize", "").strip()
    results = kb.search(query_clean, limit=15)
    response["title"] = f"Summary: {query_clean}"
    response["summary"] = f"Comprehensive information about '{query_clean}':"
    
    all_entities = []
    for entity_type in ["locations", "episodes", "artifacts", "people"]:
      if results.get(entity_type):
        for entity in results[entity_type][:2]:
          all_entities.append(build_entity_card(entity_type[:-1], entity, kb))
    response["entities"] = all_entities[:8]
  
  # TIMELINE INTENT
  elif intent == "timeline":
    results = kb.search(query, limit=15)
    if results.get("episodes"):
      episodes = sorted(results["episodes"], key=lambda e: (int(e.get("season", 0)), int(e.get("episode", 0))))
      response["title"] = "Timeline"
      response["summary"] = f"Timeline of {len(episodes)} episodes"
      response["entities"] = [build_entity_card("episode", ep, kb) for ep in episodes[:8]]
  
  # DEFAULT: SEARCH
  else:
    results = kb.search(query, limit=20)
    response["title"] = "Search Results"
    all_entities = []
    
    for entity_type in ["locations", "episodes", "artifacts", "people", "theories", "events"]:
      if results.get(entity_type):
        for entity in results[entity_type][:2]:
          all_entities.append(build_entity_card(entity_type[:-1], entity, kb))
    
    response["entities"] = all_entities[:10]
    response["summary"] = f"Found {sum(len(v) for v in results.values())} results across all datasets"
  
  return response


# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.get("/")
def root():
  return send_from_directory(APP_DIR, "index.html")


@app.get("/api/search")
def api_search():
  """General search endpoint."""
  query = request.args.get("q", "")
  limit = int(request.args.get("limit", "20"))
  pi_mode = request.args.get("piMode", "").lower() in {"1", "true", "yes"}
  
  kb = get_knowledge_base(pi_mode=pi_mode)
  results = kb.search(query, limit=limit)
  
  return jsonify({
    "query": query,
    "piMode": pi_mode,
    "results": results
  })


@app.get("/api/episodes")
def api_episodes():
  """Search episodes."""
  query = request.args.get("q", "")
  kb = get_knowledge_base(pi_mode=False)
  results = kb.search(query, limit=30) if query else {"episodes": kb.episodes[:30]}
  
  return jsonify({
    "query": query,
    "episodes": results.get("episodes", [])
  })


@app.get("/api/locations")
def api_locations():
  """Search locations."""
  query = request.args.get("q", "")
  kb = get_knowledge_base(pi_mode=False)
  results = kb.search(query, limit=30) if query else {"locations": kb.locations[:30]}
  
  return jsonify({
    "query": query,
    "locations": results.get("locations", [])
  })


@app.get("/api/theories")
def api_theories():
  """Search theories (WEB_MODE only)."""
  pi_mode = request.args.get("piMode", "").lower() in {"1", "true", "yes"}
  if pi_mode:
    return jsonify({
      "query": request.args.get("q", ""),
      "theories": [],
      "note": "Theories disabled in PI_MODE"
    })
  
  query = request.args.get("q", "")
  kb = get_knowledge_base(pi_mode=False)
  results = kb.search(query, limit=30) if query else {"theories": kb.theories[:30]}
  
  return jsonify({
    "query": query,
    "theories": results.get("theories", [])
  })


@app.get("/api/people")
def api_people():
  """Search people (WEB_MODE only)."""
  pi_mode = request.args.get("piMode", "").lower() in {"1", "true", "yes"}
  if pi_mode:
    return jsonify({
      "query": request.args.get("q", ""),
      "people": [],
      "note": "People disabled in PI_MODE"
    })
  
  query = request.args.get("q", "")
  kb = get_knowledge_base(pi_mode=False)
  results = kb.search(query, limit=30) if query else {"people": kb.people[:30]}
  
  return jsonify({
    "query": query,
    "people": results.get("people", [])
  })


@app.get("/api/events")
def api_events():
  """Search events (WEB_MODE only)."""
  pi_mode = request.args.get("piMode", "").lower() in {"1", "true", "yes"}
  if pi_mode:
    return jsonify({
      "query": request.args.get("q", ""),
      "events": [],
      "note": "Events disabled in PI_MODE"
    })
  
  query = request.args.get("q", "")
  kb = get_knowledge_base(pi_mode=False)
  results = kb.search(query, limit=30) if query else {"events": kb.events[:30]}
  
  return jsonify({
    "query": query,
    "events": results.get("events", [])
  })


@app.post("/api/semantic/query")
def api_semantic_query():
  """Main semantic query endpoint."""
  payload = request.json or {}
  query = payload.get("query", "")
  pi_mode = bool(payload.get("piMode"))
  
  response = semantic_query_handler(query, pi_mode=pi_mode)
  
  return jsonify(response)


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=8080, debug=False)
