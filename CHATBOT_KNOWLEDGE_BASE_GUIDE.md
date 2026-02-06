# Oak Island Chatbot Knowledge Base Integration

## Overview

The Oak Island chatbot is powered by a unified knowledge base that loads data from six JSON sources:
- **episodes.json** - All episode metadata
- **locations.json** - Geographic locations and sites
- **people.json** - People mentioned in episodes (WEB_MODE only)
- **theories.json** - Theories and hypotheses (WEB_MODE only)
- **events.json** - Recorded events (WEB_MODE only)
- **measurements.json** - Measurements and data points (WEB_MODE only)

## Architecture

### Knowledge Loader (`KnowledgeBase` class in api_server.py)

The `KnowledgeBase` class unifies all data sources and builds searchable indices:

```python
kb = KnowledgeBase(DATA_DIR, pi_mode=False)  # Load knowledge base
results = kb.search("money pit", limit=10)   # Full-text search
episode_details = kb.get_episode_details(1, 1)  # Get S1E1 details
location_details = kb.get_location_details("Smith's Cove")  # Get location details
```

### Intent Recognition

The `infer_intent()` function detects user intent from natural language:
- **location** - "Where is the Money Pit?"
- **episode** - "What happens in S1E1?"
- **artifact** - "What artifacts are found?"
- **person** - "Who is Rick Lagina?"
- **theory** - "What theories are discussed?"
- **timeline** - "Timeline of events"
- **summary** - "Summarize the Money Pit"
- **search** - Generic search (default)

### Semantic Query Handler

The `/api/semantic/query` endpoint:
1. Accepts natural language queries
2. Detects intent
3. Retrieves relevant data from knowledge base
4. Formats structured response with:
   - Title
   - Summary
   - Entity cards (locations, episodes, artifacts, people)
   - Related entities
   - Suggestions for follow-up questions

### PI_MODE vs WEB_MODE

**PI_MODE (Raspberry Pi):**
- Loads only: episodes, locations, artifacts
- Skips: people, theories, events, measurements
- Fast, lightweight for low-spec hardware

**WEB_MODE (Desktop/Server):**
- Loads all datasets
- Full semantic search across all entity types
- Rich cross-references

---

## Feeding New Knowledge Into the System

### Method 1: Update Canonical Data Sources

1. **Canonical Data Location:** `/home/pi/oak-island-hub/data_canonical/`

   ```
   artifacts.csv         # Artifact registry
   boreholes.csv         # Borehole data
   episodes.csv          # Episode metadata
   events.csv            # Event records
   location_mentions.csv # Location references
   locations.csv         # Location registry
   measurements.csv      # Measurement data
   people.csv            # People mentions
   theories.csv          # Theory records
   ```

2. **Add/Update Records:** Edit the relevant CSV file:
   ```csv
   # Example: Adding a new location to locations.csv
   id,name,type,lat,lng,description
   new_site,Temple Area,excavation,44.5236,-64.3002,Recently discovered site
   ```

3. **Rebuild JSON Outputs:**
   ```bash
   cd /home/pi/oak-island-hub/pipeline
   python3 builders/build_json.py          # Rebuilds oak_island_data.json
   python3 builders/build_semantic_json.py # Rebuilds episodes.json, locations.json, etc.
   ```

4. **Copy to Frontend:**
   ```bash
   cp /home/pi/oak-island-hub/data_derived/*.json /home/pi/oak-island-hub/app_public/data/
   cp /home/pi/oak-island-hub/app_public/data/oak_island_data.json /home/pi/oak-island-hub/app_public/data/
   ```

5. **Restart API Server:**
   ```bash
   pkill -f api_server.py
   python3 /home/pi/oak-island-hub/api_server.py
   ```

### Method 2: Direct JSON Updates (Quick Testing)

For rapid prototyping, directly edit the JSON files:

1. **Edit JSON:** `/home/pi/oak-island-hub/app_public/data/<dataset>.json`

2. **Verify Syntax:**
   ```bash
   python3 -c "import json; json.load(open('/home/pi/oak-island-hub/app_public/data/locations.json'))"
   ```

3. **Clear Cache & Restart:**
   ```bash
   pkill -f api_server.py
   rm /tmp/*.json 2>/dev/null || true  # Clear any cached data
   python3 /home/pi/oak-island-hub/api_server.py
   ```

### Method 3: Add Extracted Data via Pipeline

If you have new subtitles, transcripts, or raw data:

1. **Place Raw Data:** `/home/pi/oak-island-hub/data_raw/`

2. **Run Extractors:**
   ```bash
   cd /home/pi/oak-island-hub/pipeline
   python3 extractors/extract_theories.py          # Extract theories from subtitles
   python3 extractors/extract_people.py            # Extract people mentions
   python3 extractors/extract_locations_from_subtitles.py
   ```

3. **Run Normalizers:**
   ```bash
   python3 normalizers/normalize_theories.py
   python3 normalizers/normalize_people.py
   ```

4. **Run Builders to Regenerate JSON:**
   ```bash
   python3 builders/build_semantic_json.py
   ```

5. **Deploy to Frontend & Restart Server**

---

## Data Formats

### locations.json

```json
[
  {
    "id": "money_pit",
    "name": "Money Pit",
    "type": "shaft",
    "lat": 44.523550,
    "lng": -64.300020,
    "description": "Main excavation site",
    "artifacts": [
      {
        "name": "Wooden Beam",
        "type": "wood",
        "depth": 90
      }
    ]
  }
]
```

### episodes.json

```json
{
  "episodes": [
    {
      "season": 1,
      "episode": 1,
      "title": "What Lies Below",
      "airDate": "2014-01-06",
      "shortSummary": "Rick and Marty begin their investigation..."
    }
  ]
}
```

### theories.json

```json
[
  {
    "season": "1",
    "episode": "1",
    "timestamp": "00:45:30.000",
    "theory": "french",
    "text": "The French may have buried treasure here...",
    "confidence": "0.8",
    "source_refs": "s01e01.en.srt"
  }
]
```

### people.json

```json
[
  {
    "season": "1",
    "episode": "1",
    "timestamp": "00:10:00.000",
    "person": "Rick Lagina",
    "text": "Let's go dig.",
    "confidence": "1.0",
    "source_refs": "s01e01.en.srt"
  }
]
```

### events.json

```json
[
  {
    "season": "1",
    "episode": "1",
    "timestamp": "00:20:00.000",
    "event_type": "discovery",
    "text": "They found an artifact...",
    "confidence": "0.9",
    "source_refs": "s01e01.en.srt"
  }
]
```

### measurements.json

```json
[
  {
    "season": "1",
    "episode": "1",
    "timestamp": "00:30:00.000",
    "measurement_type": "depth",
    "value": "90",
    "unit": "feet",
    "context": "Shaft depth measurement",
    "confidence": "0.85",
    "source_refs": "s01e01.en.srt"
  }
]
```

---

## API Response Format

### Semantic Query Response

The `/api/semantic/query` endpoint returns:

```json
{
  "query": "What is the Money Pit?",
  "intent": "location",
  "mode": "WEB_MODE",
  "title": "Money Pit",
  "summary": "Main excavation site on Oak Island...",
  "entities": [
    {
      "title": "Money Pit",
      "type": "location",
      "summary": "shaft at (44.5236, -64.3002)",
      "data": { ... location object ... }
    }
  ],
  "related_entities": {
    "artifacts_found": ["Wooden Beam", "Coin"],
    "theories_mentioned": 5,
    "events_recorded": 12
  },
  "suggestions": [
    "What artifacts are in the Money Pit?",
    "Timeline for Money Pit digs"
  ]
}
```

---

## Customization: Adding New Intent Handlers

To add support for a new query type:

### 1. Add Intent Detection

Edit `infer_intent()` in `api_server.py`:

```python
def infer_intent(query):
  q = normalize(query)
  # ... existing code ...
  
  # ADD NEW INTENT
  if any(word in q for word in ["connection", "connects", "related"]):
    return "connection_analysis"
  
  return "search"
```

### 2. Add Handler in `semantic_query_handler()`

```python
def semantic_query_handler(query, pi_mode=False):
  kb = get_knowledge_base(pi_mode=pi_mode)
  intent = infer_intent(query)
  
  response = {
    "query": query,
    "intent": intent,
    "mode": "PI_MODE" if pi_mode else "WEB_MODE",
    # ... standard response fields ...
  }
  
  # ... existing intent handlers ...
  
  # ADD NEW HANDLER
  elif intent == "connection_analysis":
    term_a, term_b = parse_two_terms(query)
    results_a = kb.search(term_a, limit=50)
    results_b = kb.search(term_b, limit=50)
    
    response["title"] = f"Connection: {term_a} <-> {term_b}"
    response["summary"] = "Finding connections between entities..."
    # Build response with overlapping results
  
  return response
```

### 3. Update Frontend Rendering (Optional)

If your response format is different, update `renderResponse()` in `chatbot.js`.

---

## Performance Tuning

### Cache Strategy

The `KnowledgeBase` is instantiated once and cached:

```python
KNOWLEDGE_BASE = None  # Global singleton

def get_knowledge_base(pi_mode=False):
  global KNOWLEDGE_BASE
  if KNOWLEDGE_BASE is None:
    KNOWLEDGE_BASE = KnowledgeBase(DATA_DIR, pi_mode=pi_mode)
  return KNOWLEDGE_BASE
```

To clear the cache between requests:

```python
KNOWLEDGE_BASE = None  # Force reload next request
```

### Search Index Optimization

The knowledge base builds indices in `_build_indices()`. To add a new searchable field:

```python
def _build_indices(self):
  # ... existing code ...
  
  # ADD NEW INDEX
  for artifact in self.artifacts:
    artifact_type = artifact.get("type", "").strip()
    if artifact_type:
      indices["artifacts_by_type"][normalize(artifact_type)].append(artifact)
      indices["full_text"][normalize(artifact_type)].append(("artifact", artifact))
  
  return indices
```

---

## Troubleshooting

### Knowledge Base Doesn't Load

1. Check file permissions:
   ```bash
   ls -la /home/pi/oak-island-hub/app_public/data/*.json
   ```

2. Verify JSON syntax:
   ```bash
   python3 -c "import json; json.load(open('/path/to/file.json'))" && echo "OK"
   ```

3. Check logs:
   ```bash
   tail -50 /tmp/api_server.log
   ```

### Queries Return Empty Results

1. Verify data is loaded:
   ```bash
   curl http://localhost:8080/api/episodes?q=test
   ```

2. Check indices are built:
   ```bash
   python3 -c "
   from api_server import get_knowledge_base
   kb = get_knowledge_base()
   print(f'Episodes: {len(kb.episodes)}')
   print(f'Locations: {len(kb.locations)}')
   print(f'Artifacts: {len(kb.artifacts)}')
   "
   ```

### PI_MODE Not Respecting Data Limits

Verify PI_MODE detection:

```javascript
// In browser console
console.log("PI_MODE:", window.PI_MODE);
```

Or force it in localStorage:

```javascript
localStorage.setItem('PI_MODE', 'true');  // Force PI_MODE
localStorage.setItem('PI_MODE', 'false'); // Force WEB_MODE
location.reload();
```

---

## Testing

### Test Basic Search

```bash
curl -X POST http://localhost:8080/api/semantic/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the Money Pit?", "piMode": false}'
```

### Test PI_MODE

```bash
curl -X POST http://localhost:8080/api/semantic/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Tell me about theories", "piMode": true}'
```

### Test Intent Detection

```bash
python3 << 'EOF'
from api_server import infer_intent

tests = [
  "Where is Smith's Cove?",
  "What theories are discussed?",
  "Timeline for the Money Pit",
  "Who is Zena Halpern?",
  "Summarize the season",
]

for query in tests:
  intent = infer_intent(query)
  print(f"{query:40} -> {intent}")
EOF
```

---

## Summary

The chatbot knowledge base is flexible and extensible:

1. **Add data** via CSV → rebuild JSON
2. **Quick test** by editing JSON directly
3. **Add pipelines** for new data extraction
4. **Customize** intent handling and response formatting
5. **Optimize** with indices and caching

All knowledge flows through the `KnowledgeBase` class, making it easy to add new features and data sources.
