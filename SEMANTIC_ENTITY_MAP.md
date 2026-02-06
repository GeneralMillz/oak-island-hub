# Oak Island Hub: Semantic Entity Map
**Status:** Domain Analysis Complete | Generated: 2026-02-05

---

## I. DOMAIN OVERVIEW

The Oak Island Hub represents a **narrative-driven historical investigation system** where:
- **Core Domain:** Archaeological/Scientific investigation of Oak Island
- **Episodic Narrative:** 14 seasons (0-13) of television investigations
- **Primary Granularity:** Subtitle-level transcript events (temporally precise, sourced)
- **Semantic Approach:** Every fact is anchored to:
  - **WHO** made the observation (People)
  - **WHEN** it occurred (Season/Episode/Timestamp)
  - **WHERE** it was found (Locations)
  - **WHAT** was discovered (Artifacts, Measurements)
  - **WHY** they believe it (Theories, Evidence chains)

---

## II. CORE ENTITIES & RELATIONSHIPS

### **ENTITY 1: LOCATIONS** (Geographic/Spatial Domain)
**Purpose:** Represent physical places on Oak Island where investigation occurs
**Current Status:** JSON (5-10 records), fully imported from subscribers, geo-tagged
**Cardinality:** Small (< 100 unique locations)
**Relationships:** 
- Location ← Events (1:Many - events mention/occur at locations)
- Location ← Artifacts (1:Many - artifacts found at locations)
- Location ← Measurements (1:Many - measurements taken at locations)
- Location ← Boreholes (1:Many - boreholes drilled at locations)

**Key Fields:**
```
location {
  id: string (unique key: "money_pit", "smiths_cove", etc.)
  name: string (display name)
  type: enum ("shaft", "landmark", "feature", "shore", "swamp")
  latitude: float (geo-spatial anchor)
  longitude: float (geo-spatial anchor)
  description: text
  first_mentioned_season: int
  first_mentioned_episode: int
  category: string (from oak_island_data.json categories)
}
```

**Canonical Source:** docs/data/locations.json + oak_island_data.json[locations]
**Redundancy:** Minimal (tightly scoped, no duplication found)
**Usage in Frontend:** Map initialization, location picker, location detail view
**Optimization:** Keep as-is (small size, high utility)

---

### **ENTITY 2: EPISODES** (Temporal/Narrative Domain)
**Purpose:** Represent individual TV episodes as temporal anchors for events
**Current Status:** JSON (200+ records across seasons 1-14 + season 0 special)
**Cardinality:** Medium (~244 episodes total)
**Relationships:**
- Episode → Events (1:Many - contains many events)
- Episode → People mentions (1:Many - shows feature recurring people)
- Episode → Measurements (1:Many - measurements discussed in episode)
- Episode ← Season hierarchy (1:1)

**Key Fields:**
```
episode {
  id: string (e.g., "s01e01")
  season: int (0-13, where 0 = special)
  episode: int (episode within season)
  title: string
  air_date: ISO date (null for some specials)
  summary: text (episode summary, mostly null)
}
```

**Canonical Source:** docs/data/episodes.json + oak_island_data.json[seasons.episodes]
**Redundancy:** ⚠️ Dual storage (episodes.json + oak_island_data embedded)
**Usage in Frontend:** Episode picker, season selector, timeline navigation
**Optimization:** Consolidate - keep one canonical table, export from there

---

### **ENTITY 3: PEOPLE** (Human/Social Domain)
**Problem:** 84,871 transcript mentions → ~85 unique identifiable people (99.9% redundancy)
**Purpose:** Represent recurring investigators, experts, crew, historians
**Current Status:** Fragmented (84k mentions in people.json, no person master table)
**Cardinality:** ~85 unique people (Rick, Marty, Gary, Craig, Jack, etc.)

**Person Entity Structure:**
```
person {
  id: string ("rick_lagina", "marty_lagina", "gary_drayton", etc.)
  name: string (canonical name, normalized)
  role: enum ("host", "expert", "crew", "historian", "guest", "producer")
  role_detail: string (e.g., "Archaeological Expert", "Metal Detection")
  description: text
  first_appearance_season: int
  last_appearance_season: int
  mention_count: int (how many times mentioned in transcripts)
  confidence_flags: json (unclear names, ambiguous mentions)
}
```

**Mentions Table (1:Many relationship):**
```
person_mention {
  id: autoincrement
  person_id: FK → people.id
  season: int
  episode: int
  timestamp: string (HH:MM:SS.mmm)
  text: string (quoted transcript line)
  confidence: float (0.0-1.0)
  mention_type: enum ("speaker", "referenced", "inferred")
  source_file: string ("sXXeYY.en.srt")
}
```

**Current Data Structure (Frontend):**
```json
{
  "season": "0",
  "episode": "1",
  "timestamp": "00:10:03.940",
  "person": "Rick",
  "text": "Five years ago...",
  "confidence": "1.0",
  "source_refs": "s00e01.en.srt"
}
```

**Redundancy Analysis:**
- Total entries: 84,871
- Unique person names: ~85
- Ratio: 1,000:1
- **What this means:** Same person mentioned ~1,000 times in transcripts (normal for recurring character)
- **What we keep:** 1 canonical person record + junction table for mentions
- **Savings:** 2.0 MB → 50 KB (97% reduction)

**Usage in Frontend:** Character profiles, role descriptions, guest expert info
**Fuzzy Matching Issues:** 
- "Rick" vs "Rick Lagina" vs "RICK_LAGINA"
- Names appear in different contexts (speaker, referenced, inferred)
- Some mentions are misattributed (dialog mistaken for character name)

---

### **ENTITY 4: THEORIES** (Knowledge/Belief Domain)
**Problem:** 34,841 transcript mentions → 16 unique theories (99.6% redundancy)
**Purpose:** Represent historical/archaeological hypotheses, beliefs, explanations
**Current Status:** Fragmented (34k mentions in theories.json, no theory master table)
**Cardinality:** 16 unique theories (treasure, templar_cross, templar, french, etc.)

**Theory Entity Structure:**
```
theory {
  id: string ("treasure", "templar_cross", "french_pirate", etc.)
  name: string (display name: "Templar Cross Theory", "French Connection")
  theory_type: enum ("treasure", "historical", "religious", "military")
  description: text
  evidence_count: int (how many events mention this theory)
  first_mentioned_season: int
  last_mentioned_season: int
  related_entities: json (artifacts, locations involved)
}
```

**Theory Mentions Table (1:Many):**
```
theory_mention {
  id: autoincrement
  theory_id: FK → theories.id
  season: int
  episode: int
  timestamp: string
  text: string (quoted context)
  confidence: float
  mention_type: enum ("stated", "discussed", "implied", "challenged")
  source_file: string
}
```

**Current Data Structure (Frontend):**
```json
{
  "season": "0",
  "episode": "3",
  "timestamp": "00:04:45.620",
  "theory": "british",
  "text": "people in Europe, in England, they knew nothing",
  "confidence": "1.0",
  "source_refs": "s00e03.en.srt"
}
```

**Theory Distribution (from audit):**
1. treasure: 1,605 mentions
2. templar_cross: 483
3. templar: 476
4. french: 253
5. nolan_cross: 244
6. spanish: 176
7. british: 138
8. zena_map: 116
9. pirates: 114
10. roman: 86
11-16. (6 others < 40 mentions each)

**Redundancy Analysis:**
- Total entries: 34,841
- Unique theories: 16
- Ratio: 2,177:1
- **What this means:** Theories are discussed 2,000+ times across episodes (repeated discussion)
- **What we keep:** 1 canonical theory record + junction table for mentions
- **Savings:** 849 KB → 10 KB (98% reduction)

**Usage in Frontend:** Theory filters, theory details, evidence chain visualization
**Semantic Relationships:**
- Theory → Events (mentions in context)
- Theory → Artifacts (supporting evidence)
- Theory → Locations (geographic hypothesis)
- Theory → Theory (theory conflicts/supports)

---

### **ENTITY 5: EVENTS** (Activity/Discovery Domain)
**Purpose:** Represent specific discoveries, observations, activities in transcripts
**Current Status:** JSON (6,216 records), already deduplicated at transcript level
**Cardinality:** Medium (6,216 unique events)
**Relationships:**
- Event ← Episode (Many:1 - multiple events per episode)
- Event ← Location (Many:1 - event occurs at location)
- Event ← People (Many:Many - through mentions)
- Event ← Theories (Many:Many - theory discussions)

**Key Fields:**
```
event {
  id: int (autoincrement primary key)
  season: int
  episode: int
  timestamp: string (HH:MM:SS.mmm) - seek position in episode
  event_type: string - see enum below
  text: string - quoted transcript line
  confidence: float (0.0-1.0, mostly 1.0)
  location_id: string FK (can be null)
  location_hint: string (if ambiguous)
  source_ref: string (e.g., "s01e01.en.srt", line number)
}
```

**Event Types (10 categories identified):**
```
{
  "discovery": 2197,    // Found something
  "water_issue": 1118,  // Water/flooding discussion
  "digging": 1076,      // Excavation activity
  "equipment": 876,     // Tool/setup discussion
  "theory_mention": 643,// Theory referenced
  "measurement": 534,   // Measurement taken/discussed
  "expert_opinion": 412,
  "artifact_analysis": 389,
  "location_focus": 334,
  "finding": 267        // Conclusion/summary
}
```

**Redundancy Analysis:**
- Total entries: 6,216
- Unique events: 6,216 (no duplication - already one entry per event)
- **What this means:** Events are truly atomic, one per transcript mention
- **What we keep:** All (already optimized)
- **Savings:** 0% (already normalized)

**Usage in Frontend:** Timeline view, location details, search, discovery feed
**Optimization Path:** Lazy-load via API (pagination + filtering)

---

### **ENTITY 6: ARTIFACTS** (Physical Object Domain)
**Purpose:** Represent discovered objects, items of interest
**Current Status:** JSONL (82 records), extracted from subtitles
**Cardinality:** Small (~100 unique artifacts)
**Relationships:**
- Artifact ← Location (Many:1 - found at location)
- Artifact ← Episode (Many:1 - discovered in episode)
- Artifact ← Theory (Many:Many - evidence for theory)

**Key Fields:**
```
artifact {
  id: string ("s01e04_a001_stone", naming convention)
  name: string
  description: text
  artifact_type: string enum (
    "coin", "wood", "stone", "metal", "bone", 
    "ceramic", "tool", "structure", "inscription"
  )
  location_id: string FK (can be null if ambiguous)
  location_hint: string (e.g., "near the oak shelf")
  season: int
  episode: int
  depth_m: float (if known)
  depth_reference: string ("below water table", "in shaft", etc.)
  confidence: float
  source_file: string
  theory_ids: array FK (which theories does this support?)
}
```

**Current Data Structure (JSONL):**
```json
{
  "fact_type": "artifact",
  "artifact_id": "s01e04_a001_discovered-a-sixth-stone",
  "attributes": {
    "name": "Discovered a sixth stone with a",
    "description": "discovered a sixth stone with a",
    "depth_m": null,
    "location_hint": null
  },
  "episode": {"season": 1, "episode": 4},
  "source": {"origin": "subtitles", "file": "s01e04.en.srt"},
  "confidence": 0.95
}
```

**Usage in Frontend:** Artifact gallery, location detail view, artifact timeline
**Optimization:** Currently small, can remain JSON or move to API

---

### **ENTITY 7: MEASUREMENTS** (Quantitative Data Domain)
**Purpose:** Represent scientific/dimensional measurements discussed in episodes
**Current Status:** JSON (33,097 lines), extracted from subtitles
**Cardinality:** Medium (2,767 records)
**Relationships:**
- Measurement ← Episode  (Many:1)
- Measurement ← Location (Many:1, often null)

**Key Fields:**
```
measurement {
  id: string
  season: int
  episode: int
  timestamp: string (HH:MM:SS.mmm)
  measurement_type: string enum (
    "distance", "depth", "temperature", "distance", 
    "magnetic", "radiation", "year", "age", "height"
  )
  value: float (or string for complex values)
  unit: string ("m", "ft", "C", "F", "gauss", "year", "ppm")
  direction: string (if applicable: "north", "east", "down", etc.)
  context: string (sentence where measurement appears)
  location_id: string FK (optional)
  confidence: float
  source_file: string
}
```

**Measurement Types (extracted from data):**
- Quantitative: distance, depth, temperature, height, radius, volume, weight
- Temporal: year, age, date
- Geophysical: magnetic_field, radiation, gravity
- Archaeological: artifact_count, depth_range, age_estimate

**Usage in Frontend:** Measurement timeline, location analysis, scientific data view
**Optimization:** Lazy-load by location (save 792 KB init)

---

### **ENTITY 8: BOREHOLES** (Geological/Subsurface Domain)
**Purpose:** Represent drilling operations, subsurface exploration, coring data
**Current Status:** JSONL (1,120 records), extracted from subtitles
**Cardinality:** Medium (~50 unique boreholes, 1,120 mentions)
**Relationships:**
- Borehole ← Location (Many:1)
- Borehole ← Episode (Many:1)
- Borehole ← Measurements (Many:Many - depth, core analysis, etc.)
- Borehole ← Artifacts (Many:Many - finds within borehole)

**Key Fields:**
```
borehole {
  id: string ("10x", "C-1", "10-X", naming convention)
  location_id: string FK
  bore_number: string (canonical identifier)
  depth_meters: float (maximum depth reached)
  diameter_mm: float (if known)
  description: text
  first_drilled_season: int
  last_accessed_season: int
  drill_type: string ("core", "rotary", "hand-auger", "unknown")
  
  // Relationships to other entities
  interval_ids: array FK (stratigraphic layers)
  artifact_find_ids: array FK (what was found in it)
  measurement_ids: array FK (core analysis, etc.)
}
```

**Current Data Structure (JSONL):**
```json
{
  "fact_type": "borehole",
  "borehole_id": "10x",
  "attributes": {
    "name": "10x",
    "location_hint": null
  },
  "episode": {"season": 2, "episode": 8},
  "source": {"origin": "subtitles", "file": "s02e08.en.srt"},
  "confidence": 0.95
}
```

**Borehole Mentions (1,120 total):**
- 10x: ~400 mentions (most famous borehole)
- C-1: ~150 mentions
- 10-X: ~80 mentions
- Others: 500 mentions across 40+ distinct boreholes

**Usage in Frontend:** Geological map view, subsurface cross-sections, drilling timeline
**Optimization:** Keep all records (important for domain)

---

### **ENTITY 9: TRANSCRIPTS** (Source Data Domain)
**Note:** NOT frontend-facing, but critical for ETL source
**Purpose:** Raw transcript storage for re-extraction and fact verification
**Current Status:** 93,061 records in `data_extracted/facts/transcripts.jsonl` (21 MB)
**Cardinality:** 93,061+ lines across 100 subtitle files
**Relationships:**
- Transcript → Episode (Many:1)
- Transcript ← Events (extraction source)
- Transcript ← People (extraction source)
- Transcript ← Theories (extraction source)
- Transcript ← Measurements (extraction source)

**Key Fields:**
```
transcript_line {
  id: string
  season: int
  episode: int
  timestamp: string (HH:MM:SS.mmm)
  duration: float (seconds)
  speaker: string (who said it, can be null)
  text: string (dialog/narration line exactly)
  source_file: string ("s00e01.en.srt")
  line_number: int (in SRT file)
}
```

**Usage:** ETL re-runs, fact verification, quote extraction, full-text search
**Archive Strategy:** Not needed in active database (can regenerate from subtitles)
**Storage:** Keep in data_raw/subtitles/ + SRT files

---

## III. SEMANTIC RELATIONSHIPS (The Knowledge Graph)

### Graph Structure:
```
LOCATIONS (hub - everything connects to location)
├── Events (what happened WHERE)
│   ├── People (who discovered)
│   ├── Theories (what they believe about it)
│   ├── Artifacts (what was found)
│   └── Measurements (how much/how big)
├── Artifacts (what was found WHERE)
│   ├── Theories (what theory does it support)
│   └── Boreholes (depth/recovery method)
├── Measurements (readings taken WHERE)
│   └── Types (depth, temperature, magnetic, etc.)
└── Boreholes (drilling data at location)
    ├── Intervals (stratigraphic layers)
    ├── Artifacts (core finds)
    └── Measurements (core analysis)

EPISODES (temporal axis)
├── Events (episodes contain events)
├── People mentions (who appears)
├── Theories discussed (beliefs in episode)
└── Measurements mentioned (quantitative data)

PEOPLE (human dimension)
├── Mentions (all transcript appearances)
├── Events (discoveries made/witnessed)
└── Expertise (by role - host, expert, crew)

THEORIES (knowledge/belief system)
├── Mentions (all times discussed)
├── Evidence chain (linked artifacts/events)
├── Locations (geographic hypothesis)
└── Theory conflicts (contradictions)
```

### Critical Relationships for Queries:

**1. Evidence Chain:**
```
Theory → Theory_mentions → Events → Artifacts → Physical verification
```
Used for: "What evidence supports this theory?"

**2. Temporal Query:**
```
Episode → Events → Temporal ordering
```
Used for: "What happened in season 3?" → "Timeline of discoveries"

**3. Spatial Query:**
```
Location → Events/Artifacts/Measurements → Geospatial analysis
```
Used for: "What happened at Money Pit?" → "All discoveries at location"

**4. Person Investigation:**
```
People → Person_mentions → Episodes/Events → Their contributions
```
Used for: "What did Rick discover?" → "Episodes featuring Rick"

---

## IV. DATA CLASSIFICATION

### TIER 1: CANONICAL (Single Source of Truth)
These become SQLite tables, are normalized and deduplicated:
- Locations (small, authoritative)
- Episodes (medium, authoritative)
- People (normalized from 84k mentions → ~85 unique)
- Theories (normalized from 34k mentions → 16 unique)
- Events (already normalized, 6,216 unique)
- Artifacts (small, tightly scoped)
- Measurements (medium, all kept)
- Boreholes (medium, all kept)

### TIER 2: RELATIONAL (Junction Tables)
Store the many:many and one:many relationships:
- person_mentions (84,871 entries - who said what when)
- theory_mentions (34,841 entries - theory discussions)
- artifact_findings (events where artifacts discovered)
- measurement_events (measurement discussions)
- borehole_intervals (stratigraphic layers within boreholes)
- borehole_artifacts (finds recovered from boreholes)

### TIER 3: SOURCE (Non-frontend)
Kept in raw format for ETL/verification purposes:
- Subtitles (SRT files in data_raw/subtitles/)
- Transcripts (JSONL in data_extracted/facts/transcripts.jsonl) [Archive]
- TMDB metadata (in data_raw/tmdb/) [Delete - regenerable]
- LiDAR GeoTIFF (in data_raw/lidar/) [Archive - used for tiles]

### TIER 4: DERIVED (Generated Views)
Frontend-ready JSON exports from database:
- locations_min.json (small location list, < 10 KB)
- episodes_list.json (all episodes, < 50 KB)
- people_summary.json (unique people, ~50 KB)
- theories_summary.json (unique theories, ~10 KB)
- events_by_location.json (lazy-loaded, paginated)
- artifacts_by_location.json (lazy-loaded)
- measurements_by_location.json (lazy-loaded)

---

## V. DEDUPLICATION STRATEGY

### People Deduplication (84,871 → 85 unique)

**Challenges:**
- Name variations: "Rick" vs "Rick Lagina" vs "RICK_LAGINA"
- Incomplete names extracted from dialog
- Same person referred to differently

**Strategy:**
1. Extract unique names from all 84k mentions
2. Cluster by Levenshtein distance (fuzzy matching)
3. Manual review of ambiguous clusters
4. Create canonical ID: lowercase + underscore (rick_lagina)
5. Create mapping table: original_name → canonical_id

**Mapping Examples:**
```
"Rick" → rick_lagina (primary host)
"Rick Lagina" → rick_lagina
"Marty" → marty_lagina
"Marty Lagina" → marty_lagina
"Gary" → gary_drayton
"Gary Drayton" → gary_drayton
```

**Result:** 
- 85 unique person records
- 84,871 mentions → person_mentions table (FK to people.id)
- Savings: 2.0 MB → 50 KB

---

### Theory Deduplication (34,841 → 16 unique)

**Challenges:**
- Theory IDs may be inconsistent (templar vs templar_cross)
- Same theory discussed with different framing
- Theory combinations and conflicts

**Strategy:**
1. Extract unique theory IDs from 34k mentions
2. Normalize naming: snake_case
3. Group related theories (templar family, french connection, etc.)
4. Create descriptions and theory_type enums
5. Create mapping for aliases

**Theory Categories:**
- Treasure-related: treasure, nolan_cross, zena_map, oak_gem
- Religious: templar, templar_cross, roman, religious_relic
- Historical: french, british, spanish, pirates
- Local: indigenous, geological_deposits

**Result:**
- 16 unique theory records
- 34,841 mentions → theory_mentions table
- Savings: 849 KB → 10 KB

---

## VI. FRONTEND DATA SLICES (Lazy-Loading Strategy)

Instead of loading 5.1 MB at startup, export minimal views from database:

### Initial Load (44 KB total):
```
1. oak_island_data.json (48 KB)
   - Seasons structure only
   - No embedded episodes (moved to separate)

2. locations_min.json (4 KB)
   - Just coordinates, names, IDs

3. episode_titles.json (20 KB)
   - Minimal episode list

Total: ~72 KB (vs 5.1 MB previously = 98% reduction)
```

### On-Demand APIs (via api_server_v2.py):
```
GET /api/v2/locations              # All locations (< 5 KB)
GET /api/v2/locations/:id          # Location detail (30 KB) + events
GET /api/v2/events?location=:id    # Events for location (paginated)
GET /api/v2/events?season=:s       # Events for season
GET /api/v2/theories               # All theories (< 10 KB)
GET /api/v2/people                 # All people (< 50 KB)
GET /api/v2/artifacts              # All artifacts (< 50 KB)
GET /api/v2/measurements/:loc_id   # Measurements for location
```

**Benefits:**
- Initial load: 44 KB (vs 5.1 MB)
- Subsequent loads: 10-50 KB on demand
- Better user experience: fast first paint
- Bandwidth favorable: lazy loading reduces peak usage

---

## VII. DATA FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────┐
│  RAW SOURCES (data_raw/)                             │
├─────────────────────────┬───────────────────────────┤
│ Subtitles (100 SRT)     │ TMDB Metadata            │
│ (6.6 MB)                │ (188 KB)                 │
└────────────┬────────────┴──────────┬────────────────┘
             │                       │
             │ Extract facts         │ API fetch (regenerable)
             │ (NFT via NER/ML)      │
             ▼                       ▼
┌─────────────────────────────────────────────────────┐
│  EXTRACTED FACTS (data_extracted/facts/)             │
├──────────────┬──────────────┬──────────────────────┤
│ people.jsonl │ theories.jsonl│ events.jsonl       │
│ (9.4k lines) │ (3.9k lines) │ (6.2k lines)      │
│ 84,871 total │ 34,841 total │ 6,216 unique      │
│ 85 unique    │ 16 unique    │ (already deduped) │
└──────┬───────┴──────┬───────┴──────┬──────────────┘
       │              │              │
       │  ETL         │ ETL         │  ETL (normalize + dedupe)
       │  (fuzzy      │  (cluster   │
       │  match)      │  similar)   │
       ▼              ▼             ▼
┌─────────────────────────────────────────────────────┐
│  SEMANTIC SQLITE DATABASE (oak_island_hub.db)       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  CANONICAL TABLES:                                 │
│  • locations (9 rows)                             │
│  • episodes (244 rows)                            │
│  • people (85 rows) ← deduplicated                │
│  • theories (16 rows) ← deduplicated              │
│  • events (6,216 rows)                            │
│  • artifacts (82 rows)                            │
│  • measurements (2,767 rows)                      │
│  • boreholes (45 rows)                            │
│                                                     │
│  JUNCTION/MENTION TABLES:                         │
│  • person_mentions (84,871 rows)                  │
│  • theory_mentions (34,841 rows)                  │
│  • artifact_findings (links artifacts→events)    │
│  • borehole_intervals (stratigraphic data)       │
│  • borehole_artifacts (finds recovered)          │
│                                                     │
└────┬───────────┬────────────────┬──────────────────┘
     │           │                │
     │ Export    │ Export         │ Export
     │ (minimal) │ (paginated)    │ (on-demand)
     ▼           ▼                ▼
┌─────────────────────────────────────────────────────┐
│  FRONTEND VIEWS (docs/data/)                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  INITIAL LOAD (44 KB):                            │
│  • oak_island_data.json (48 KB) [minimal]        │
│  • locations_min.json (4 KB)                     │
│  • episode_titles.json (20 KB)                   │
│                                                     │
│  ON-DEMAND (via API):                             │
│  • /api/v2/locations                              │
│  • /api/v2/locations/:id                          │
│  • /api/v2/events (paginated)                     │
│  • /api/v2/people                                 │
│  • /api/v2/theories                               │
│  • /api/v2/artifacts                              │
│                                                     │
└─────────────────────────────────────────────────────┘
     │
     │ JSON REST API
     │ (api_server_v2.py)
     ▼
┌─────────────────────────────────────────────────────┐
│  FRONTEND APPLICATION (docs/)                       │
├─────────────────────────────────────────────────────┤
│  Map View | Location Details | Timeline | Search  │
│  All powered by semantic database queries          │
└─────────────────────────────────────────────────────┘
```

---

## VIII. KEY INSIGHTS FOR SEMANTIC DESIGN

1. **Transcript-Level Granularity**: Every fact is anchored to:
   - Specific timestamp (seek position in episode video)
   - Source file (which subtitle file)
   - Original text (quoted)
   - Confidence score
   - This enables full traceability and verification

2. **Many:Many Relationships**: Smart use of junction tables:
   - 85 people × 84,871 mentions (very sparse)
   - 16 theories × 34,841 mentions (very sparse)
   - Stored efficiently in junction tables vs denormalized

3. **Spatial Anchor**: Locations are the primary hub:
   - Events are "at" locations
   - Artifacts are "found at" locations
   - Measurements are "taken at" locations
   - Geographic queries are natural: "What at Money Pit?"

4. **Temporal Axis**: Episodes structure everything:
   - Every fact tagged to (season, episode, timestamp)
   - Enables timeline queries: "Season 5 discoveries"
   - Enables order-dependent queries: "After Money Pit drilling"

5. **Evidence Chains**: Theory → Mentions → Events → Artifacts
   - Can construct narrative: "Why we believe Templar theory"
   - Link supporting artifacts to theory mentions
   - Show hypothesis evolution across seasons

6. **Deduplication at Mention Level**: NOT at fact level
   - Don't delete mentions (they're proof of discussion frequency)
   - Move to junction table (keep relationship structure)
   - One canonical record per unique entity
   - Many junction records for each mention

7. **Frontend Modularity**: Data sliced for each view:
   - Map view: needs locations + events (paginated)
   - Theory view: needs theories + mentions + evidence
   - Timeline: needs episodes + events (ordered)
   - People detail: needs person + all their mentions
   - Each view lazy-loads only what it needs

---

## IX. NEXT PHASES

**Phase 2: Semantic Schema Design** (Reference: SQLITE_ARCHITECTURE_PROPOSAL.md)
- Refine 8 core tables
- Add junction tables (mentions, findings)
- Design indices for common queries
- Add constraints for referential integrity

**Phase 3: Intelligent ETL Pipeline**
- Create `semantic_sqlite_pipeline/` directory
- Build 9 ETL scripts (ingest, dedupe, normalize, archive, verify)
- Implement fuzzy matching for people/theories
- Generate frontend views from database

**Phase 4: Execution**
- Run locally on Raspberry Pi
- Verify data integrity
- Performance test
- Deploy to production

---

**END OF SEMANTIC ENTITY MAP**

This map represents the complete domain understanding required to build the semantic ingestion engine. All downstream code generation will reference this as the single source of truth for entity definitions and relationships.
