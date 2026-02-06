# Oak Island Chatbot - Implementation Quick Reference

## Files Modified/Created

### New Files

1. **`/app_public/chatbot/chatbot.html`** (46 lines)
   - Chatbot UI panel with message display, input, and suggestions

2. **`/app_public/chatbot/chatbot.css`** (260 lines)
   - Complete styling for chat interface with entity cards, related entities display

3. **`/app_public/js/chatbot.js`** (165 lines)
   - Frontend logic: PI_MODE detection, message rendering, semantic API calls

4. **`/api_server.py`** (571 lines)
   - Flask backend with unified knowledge base loader
   - Intent recognition and semantic query handler
   - RESTful API endpoints for search and semantic queries

5. **`/CHATBOT_KNOWLEDGE_BASE_GUIDE.md`** (550+ lines)
   - Complete documentation for feeding knowledge into the system

### Modified Files

1. **`/app_public/index.html`** 
   - Added `#main-container`, `#top-nav` for navigation
   - Added `#chatbot-view` and `#chatbot-root` containers
   - Included `chatbot.css` and `js/chatbot.js`

2. **`/app_public/styles.css`**
   - Added `.nav-button` styling
   - Added `.view` container styling
   - Updated layout to support view switching

3. **`/app_public/app.js`**
   - Added `initViewNavigation()` function
   - Integrated chatbot initialization on view switch

---

## System Architecture

```
┌─────────────────────────────────────┐
│     Frontend (chatbot.js)            │
│  - Detects PI_MODE                  │
│  - Renders entity cards              │
│  - Handles user input                │
└──────────────┬──────────────────────┘
               │ POST /api/semantic/query
               ↓
┌─────────────────────────────────────┐
│   Backend (api_server.py)            │
│  - KnowledgeBase class               │
│  - Intent recognition                │
│  - Semantic query handler            │
└──────────────┬──────────────────────┘
               │
        ┌──────┴──────┐
        ↓             ↓
   ┌─────────┐   ┌──────────┐
   │ episodes│   │ locations│
   │ people  │   │ artifacts│
   │theories │   │ events   │
   │events   │   │measurements
   └─────────┘   └──────────┘
```

---

## How Queries Flow

### 1. User Types Question

```
User: "What artifacts are at Smith's Cove?"
```

### 2. Frontend Sends POST Request

```javascript
POST /api/semantic/query
{
  "query": "What artifacts are at Smith's Cove?",
  "piMode": false
}
```

### 3. Backend Process

```python
1. infer_intent() → "location"
2. get_knowledge_base(pi_mode=False) → Load full data
3. kb.search("smith's cove") → Find locations
4. kb.get_location_details() → Get related artifacts
5. build_entity_card() → Format response
6. Return structured JSON response
```

### 4. Response Structure

```json
{
  "query": "What artifacts are at Smith's Cove?",
  "intent": "location",
  "title": "Smith's Cove",
  "summary": "Location: Smith's Cove. Type: feature.",
  "entities": [
    {
      "title": "Smith's Cove",
      "type": "location",
      "summary": "feature at (44.5239, -64.2989)"
    }
  ],
  "related_entities": {
    "artifacts_found": ["Stone Structure", "Cross"],
    "theories_mentioned": 8,
    "events_recorded": 15
  }
}
```

### 5. Frontend Renders Response

```javascript
renderResponse(messageEl, payload)
  ↓
1. Show title
2. Show summary
3. Render entity cards
4. Show related entities list
5. Display mode badge
```

---

## Intent Types Supported

| Intent | Keywords | Example |
|--------|----------|---------|
| **location** | where, place, pit, cove, shaft | "Where is the Money Pit?" |
| **episode** | season, episode, s##e## | "What happens in S1E1?" |
| **artifact** | artifact, find, treasure, discover | "What artifacts are found?" |
| **person** | person, people, who, name | "Who is Rick Lagina?" |
| **theory** | theory, theories, explain | "What theories exist?" |
| **timeline** | timeline, when, year, history | "Timeline for Money Pit" |
| **summary** | summarize, summary | "Summarize Smith's Cove" |
| **search** | (default) | "oak island" |

---

## PI_MODE vs WEB_MODE

### PI_MODE (Raspberry Pi)
```python
# Data loaded:
- episodes.json ✓
- locations.json ✓
- artifacts ✓

# Data skipped:
- people.json ✗
- theories.json ✗
- events.json ✗
- measurements.json ✗
```

### WEB_MODE (Desktop/Server)
```python
# All data loaded:
- episodes.json ✓
- locations.json ✓
- artifacts ✓
- people.json ✓
- theories.json ✓
- events.json ✓
- measurements.json ✓
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/search?q=...` | GET | General search |
| `/api/episodes?q=...` | GET | Search episodes |
| `/api/locations?q=...` | GET | Search locations |
| `/api/theories?q=...` | GET | Search theories (WEB only) |
| `/api/people?q=...` | GET | Search people (WEB only) |
| `/api/events?q=...` | GET | Search events (WEB only) |
| `/api/semantic/query` | POST | Main semantic query |

---

## Entity Cards

Each entity is rendered as a card with:
- **Title** - Entity name
- **Type** - Entity type (location, episode, artifact, person, theory, event)
- **Summary** - Key information
- **Data** - Full entity object

Example:
```
┌─────────────────────────────────┐
│ Money Pit                       │
│ location                        │
│ shaft at (44.5236, -64.3002)   │
└─────────────────────────────────┘
```

---

## Response Formatting

### Title
```javascript
response["title"] = f"S{season}E{episode} - {title}"
```

### Summary
```javascript
response["summary"] = f"Season {season}, Episode {episode}"
```

### Entity Cards
```javascript
response["entities"] = [
  build_entity_card("episode", ep, kb),
  build_entity_card("location", loc, kb),
  // ...
]
```

### Related Entities
```javascript
response["related_entities"] = {
  "artifacts_found": ["Artifact1", "Artifact2"],
  "theories_mentioned": 5,  // Number
  "people_featured": ["Rick", "Marty"]
}
```

---

## Adding New Knowledge

### Quick (Direct JSON Edit)
```bash
1. Edit /app_public/data/<dataset>.json
2. Restart api_server.py
```

### Proper (Via Pipeline)
```bash
1. Edit /data_canonical/*.csv
2. Run python3 builders/build_json.py
3. Copy JSON to /app_public/data/
4. Restart api_server.py
```

---

## Testing Queries

### Test in Browser Console
```javascript
fetch('/api/semantic/query', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    query: 'What is the Money Pit?',
    piMode: false
  })
})
.then(r => r.json())
.then(data => console.log(data))
```

### Test with curl
```bash
curl -X POST http://localhost:8080/api/semantic/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Money Pit","piMode":false}'
```

### Test Intent Detection
```python
from api_server import infer_intent
print(infer_intent("What is at Smith's Cove?"))  # → "location"
```

---

## Performance Notes

### Memory Usage
- Full knowledge base load: ~50-100 MB (WEB_MODE)
- PI_MODE: ~10-20 MB
- Search indices: ~20-30 MB

### Search Speed
- First request: ~200-500ms (cold load)
- Subsequent: ~10-50ms (cached)

### Bottlenecks
- JSON parsing (first load)
- Full-text index building
- No database optimization yet

---

## Debugging

### Enable logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check knowledge base
```python
from api_server import get_knowledge_base
kb = get_knowledge_base(pi_mode=False)
print(f"Episodes: {len(kb.episodes)}")
print(f"Locations: {len(kb.locations)}")
print(f"Artifacts: {len(kb.artifacts)}")
```

### Test intent
```python
from api_server import infer_intent
for query in ["where", "when", "who", "what"]:
  print(f"{query} → {infer_intent(query)}")
```

### Check PI_MODE
```javascript
// Browser console
console.log(window.PI_MODE)
```

---

## Common Issues & Fixes

| Problem | Solution |
|---------|----------|
| Empty results | Check JSON files exist in `/app_public/data/` |
| API 404 | Ensure Flask is running on port 8080 |
| PI_MODE always WEB | Check ARM detection in `detectPiMode()` |
| Slow search | Data too large; use PI_MODE |
| Encoding errors | Ensure JSON files are UTF-8 |
| Import errors | Install Flask: `pip install flask` |

---

## Next Steps

### 1. Deploy
```bash
python3 /home/pi/oak-island-hub/api_server.py &
```

### 2. Test
Open browser to chatbot view and ask questions

### 3. Add Knowledge
Update JSON files or CSV sources as documented in `CHATBOT_KNOWLEDGE_BASE_GUIDE.md`

### 4. Customize
Add new intents, handlers, and response formats as needed

---

## File Dependencies

```
chatbot view
  ↓
  ├─ chatbot.html (UI)
  ├─ chatbot.css (Styling)
  ├─ chatbot.js (Logic)
  │   ↓
  │   └─ /api/semantic/query
  │       ↓
  │       └─ api_server.py (Backend)
  │           ├─ KnowledgeBase (Loader)
  │           ├─ infer_intent (Intent)
  │           ├─ semantic_query_handler (Processing)
  │           └─ build_entity_card (Formatting)
  │
  └─ JSON Data Files
      ├─ episodes.json
      ├─ locations.json
      ├─ people.json
      ├─ theories.json
      ├─ events.json
      └─ measurements.json
```

