-- ============================================================================
-- Oak Island Hub: SEMANTIC SQLITE SCHEMA
-- ============================================================================
-- Purpose: Canonical database for all Oak Island entities with semantic
--          relationships, junction tables, and intelligent indices
-- Generated: 2026-02-05
-- Design:
--   - Normalized tables for entities
--   - Junction tables for many:many relationships
--   - Mention tables for deduplication
--   - Comprehensive indices for query performance
--   - Referential integrity constraints
-- ============================================================================

-- Locations (geographic/spatial anchor - hub entity)
CREATE TABLE locations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL,  -- 'shaft', 'landmark', 'feature', 'shore', 'swamp'
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    category TEXT,  -- 'excavation', 'landmark', 'shaft', 'shore', 'swamp'
    description TEXT,
    first_mentioned_season INTEGER,
    first_mentioned_episode INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Episodes (temporal structure - time anchor)
CREATE TABLE episodes (
    id TEXT PRIMARY KEY,  -- 's01e01'
    season INTEGER NOT NULL,
    episode INTEGER NOT NULL,
    title TEXT NOT NULL,
    air_date TEXT,  -- ISO date, can be null
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(season, episode)
);

-- People (unique individuals - normalized from 84,871 mentions to ~85 unique)
CREATE TABLE people (
    id TEXT PRIMARY KEY,  -- 'rick_lagina', 'marty_lagina', etc.
    name TEXT NOT NULL UNIQUE,
    role TEXT,  -- 'host', 'expert', 'crew', 'historian', 'guest', 'producer'
    role_detail TEXT,  -- e.g., 'Archaeological Expert', 'Metal Detection'
    description TEXT,
    first_appearance_season INTEGER,
    last_appearance_season INTEGER,
    mention_count INTEGER DEFAULT 0,
    confidence_flags TEXT,  -- JSON: unclear names, ambiguous references
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Person Mentions (junction table - preserves all 84,871 mentions)
CREATE TABLE person_mentions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT NOT NULL,
    season INTEGER NOT NULL,
    episode INTEGER NOT NULL,
    timestamp TEXT NOT NULL,  -- HH:MM:SS.mmm (seek position in episode video)
    text TEXT NOT NULL,  -- quoted transcript line,
    confidence REAL DEFAULT 1.0,
    mention_type TEXT,  -- 'speaker', 'referenced', 'inferred'
    source_file TEXT,  -- 's00e01.en.srt'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (person_id) REFERENCES people(id),
    FOREIGN KEY (season, episode) REFERENCES episodes(season, episode)
);

-- Theories (unique beliefs/hypotheses - normalized from 34,841 mentions to 16 unique)
CREATE TABLE theories (
    id TEXT PRIMARY KEY,  -- 'treasure', 'templar_cross', 'french', etc.
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    theory_type TEXT,  -- 'treasure', 'historical', 'religious', 'military'
    evidence_count INTEGER DEFAULT 0,
    first_mentioned_season INTEGER,
    last_mentioned_season INTEGER,
    related_artifacts TEXT,  -- JSON array of artifact IDs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Theory Mentions (junction table - preserves all 34,841 mentions)
CREATE TABLE theory_mentions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    theory_id TEXT NOT NULL,
    season INTEGER NOT NULL,
    episode INTEGER NOT NULL,
    timestamp TEXT NOT NULL,  -- HH:MM:SS.mmm
    text TEXT NOT NULL,  -- quoted context
    confidence REAL DEFAULT 1.0,
    mention_type TEXT,  -- 'stated', 'discussed', 'implied', 'challenged'
    source_file TEXT,  -- 's00e01.en.srt'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (theory_id) REFERENCES theories(id),
    FOREIGN KEY (season, episode) REFERENCES episodes(season, episode)
);

-- Events (activities/discoveries - 6,216 unique, already deduplicated at transcript level)
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER NOT NULL,
    episode INTEGER NOT NULL,
    timestamp TEXT,  -- HH:MM:SS.mmm (seek position in episode video)
    event_type TEXT NOT NULL,  -- 'discovery', 'water_issue', 'digging', etc.
    text TEXT NOT NULL,  -- quoted from transcript
    confidence REAL DEFAULT 1.0,
    location_id TEXT,  -- can be null if location ambiguous
    location_hint TEXT,  -- e.g., 'near the oak shelf'
    source_ref TEXT,  -- 's01e01.en.srt' or 's01e01.en.srt:1234'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations(id),
    FOREIGN KEY (season, episode) REFERENCES episodes(season, episode)
);

-- Artifacts (physical objects discovered)
CREATE TABLE artifacts (
    id TEXT PRIMARY KEY,  -- 's01e04_a001_stone'
    name TEXT NOT NULL,
    description TEXT,
    artifact_type TEXT,  -- 'coin', 'wood', 'stone', 'metal', 'bone', 'ceramic'
    location_id TEXT,  -- FK, can be null if ambiguous
    location_hint TEXT,
    season INTEGER,
    episode INTEGER,
    depth_m REAL,  -- depth where found
    depth_reference TEXT,  -- 'below water table', 'in shaft', etc.
    confidence REAL DEFAULT 1.0,
    source_file TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations(id),
    FOREIGN KEY (season, episode) REFERENCES episodes(season, episode)
);

-- Artifact-Event Links (what artifacts were found in which events)
CREATE TABLE artifact_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id TEXT NOT NULL,
    event_id INTEGER NOT NULL,
    season INTEGER,
    episode INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (artifact_id) REFERENCES artifacts(id),
    FOREIGN KEY (event_id) REFERENCES events(id)
);

-- Artifact-Theory Links (which theories do artifacts support)
CREATE TABLE artifact_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id TEXT NOT NULL,
    theory_id TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (artifact_id) REFERENCES artifacts(id),
    FOREIGN KEY (theory_id) REFERENCES theories(id),
    UNIQUE(artifact_id, theory_id)
);

-- Measurements (scientific/dimensional data)
CREATE TABLE measurements (
    id TEXT PRIMARY KEY,  -- unique identifier
    season INTEGER NOT NULL,
    episode INTEGER NOT NULL,
    timestamp TEXT,  -- HH:MM:SS.mmm
    measurement_type TEXT NOT NULL,  -- 'distance', 'depth', 'temperature', etc.
    value REAL NOT NULL,  -- numeric value
    unit TEXT NOT NULL,  -- 'm', 'ft', 'C', 'F', 'gauss', 'year', 'ppm'
    direction TEXT,  -- 'north', 'east', 'down', etc. if applicable
    context TEXT,  -- full sentence where measurement appears
    location_id TEXT,  -- FK, optional (not always localized)
    confidence REAL DEFAULT 1.0,
    source_file TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations(id),
    FOREIGN KEY (season, episode) REFERENCES episodes(season, episode)
);

-- Boreholes (subsurface drilling operations)
CREATE TABLE boreholes (
    id TEXT PRIMARY KEY,  -- '10x', 'C-1', '10-X'
    location_id TEXT,  -- FK
    bore_number TEXT,  -- canonical identifier
    depth_meters REAL,
    diameter_mm REAL,
    description TEXT,
    first_drilled_season INTEGER,
    last_accessed_season INTEGER,
    drill_type TEXT,  -- 'core', 'rotary', 'hand-auger', 'unknown'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations(id)
);

-- Borehole-Interval (stratigraphic layers within boreholes)
CREATE TABLE borehole_intervals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    borehole_id TEXT NOT NULL,
    interval_number INTEGER,
    depth_from_m REAL,
    depth_to_m REAL,
    material_type TEXT,  -- 'soil', 'rock', 'wood', 'artifact', 'clay'
    description TEXT,
    context TEXT,
    season INTEGER,
    episode INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (borehole_id) REFERENCES boreholes(id),
    FOREIGN KEY (season, episode) REFERENCES episodes(season, episode)
);

-- Borehole-Artifact (artifacts recovered from boreholes)
CREATE TABLE borehole_artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    borehole_id TEXT NOT NULL,
    artifact_id TEXT NOT NULL,
    depth_recovered_m REAL,
    recovery_season INTEGER,
    recovery_episode INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (borehole_id) REFERENCES boreholes(id),
    FOREIGN KEY (artifact_id) REFERENCES artifacts(id)
);

-- ============================================================================
-- INDICES FOR COMMON QUERY PATTERNS
-- ============================================================================

-- Location queries
CREATE INDEX idx_locations_type ON locations(type);
CREATE INDEX idx_locations_category ON locations(category);
CREATE INDEX idx_locations_geo ON locations(latitude, longitude);

-- Episode queries
CREATE INDEX idx_episodes_season ON episodes(season);
CREATE INDEX idx_episodes_season_episode ON episodes(season, episode);

-- Event queries
CREATE INDEX idx_events_location ON events(location_id);
CREATE INDEX idx_events_season_episode ON events(season, episode);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_timestamp ON events(season, episode, timestamp);

-- Person mention queries
CREATE INDEX idx_person_mentions_person ON person_mentions(person_id);
CREATE INDEX idx_person_mentions_season_episode ON person_mentions(season, episode);
CREATE INDEX idx_person_mentions_timestamp ON person_mentions(season, episode, timestamp);

-- Theory mention queries
CREATE INDEX idx_theory_mentions_theory ON theory_mentions(theory_id);
CREATE INDEX idx_theory_mentions_season_episode ON theory_mentions(season, episode);
CREATE INDEX idx_theory_mentions_timestamp ON theory_mentions(season, episode, timestamp);

-- Artifact queries
CREATE INDEX idx_artifacts_location ON artifacts(location_id);
CREATE INDEX idx_artifacts_type ON artifacts(artifact_type);
CREATE INDEX idx_artifacts_season_episode ON artifacts(season, episode);

-- Artifact relationship queries
CREATE INDEX idx_artifact_findings_artifact ON artifact_findings(artifact_id);
CREATE INDEX idx_artifact_findings_event ON artifact_findings(event_id);
CREATE INDEX idx_artifact_evidence_artifact ON artifact_evidence(artifact_id);
CREATE INDEX idx_artifact_evidence_theory ON artifact_evidence(theory_id);

-- Measurement queries
CREATE INDEX idx_measurements_location ON measurements(location_id);
CREATE INDEX idx_measurements_type ON measurements(measurement_type);
CREATE INDEX idx_measurements_season_episode ON measurements(season, episode);

-- Borehole queries
CREATE INDEX idx_boreholes_location ON boreholes(location_id);
CREATE INDEX idx_borehole_intervals_borehole ON borehole_intervals(borehole_id);
CREATE INDEX idx_borehole_artifacts_borehole ON borehole_artifacts(borehole_id);
CREATE INDEX idx_borehole_artifacts_artifact ON borehole_artifacts(artifact_id);

-- ============================================================================
-- VIEWS FOR COMMON ANALYTIC QUERIES
-- ============================================================================

-- View: Events with Location Names (for easier querying)
CREATE VIEW events_with_locations AS
SELECT 
    e.id,
    e.season,
    e.episode,
    e.timestamp,
    e.event_type,
    e.text,
    e.confidence,
    e.location_id,
    l.name as location_name,
    e.source_ref
FROM events e
LEFT JOIN locations l ON e.location_id = l.id;

-- View: Theory Mentions with Theory Names
CREATE VIEW theory_mentions_detailed AS
SELECT 
    tm.id,
    tm.theory_id,
    t.name as theory_name,
    t.theory_type,
    tm.season,
    tm.episode,
    tm.timestamp,
    tm.text,
    tm.confidence,
    tm.mention_type,
    tm.source_file
FROM theory_mentions tm
LEFT JOIN theories t ON tm.theory_id = t.id;

-- View: Person Mentions with Person Names
CREATE VIEW person_mentions_detailed AS
SELECT 
    pm.id,
    pm.person_id,
    p.name as person_name,
    p.role,
    pm.season,
    pm.episode,
    pm.timestamp,
    pm.text,
    pm.confidence,
    pm.mention_type,
    pm.source_file
FROM person_mentions pm
LEFT JOIN people p ON pm.person_id = p.id;

-- View: Location Investigation Summary (what was found at each location)
CREATE VIEW location_summary AS
SELECT 
    l.id,
    l.name,
    l.type,
    COUNT(DISTINCT e.id) as event_count,
    COUNT(DISTINCT a.id) as artifact_count,
    COUNT(DISTINCT m.id) as measurement_count,
    COUNT(DISTINCT b.id) as borehole_count
FROM locations l
LEFT JOIN events e ON l.id = e.location_id
LEFT JOIN artifacts a ON l.id = a.location_id
LEFT JOIN measurements m ON l.id = m.location_id
LEFT JOIN boreholes b ON l.id = b.location_id
GROUP BY l.id, l.name, l.type;

-- View: Theory Evidence Chain (artifacts supporting theories)
CREATE VIEW theory_evidence AS
SELECT 
    t.id,
    t.name as theory_name,
    COUNT(DISTINCT ae.artifact_id) as supporting_artifacts,
    COUNT(DISTINCT tm.id) as total_mentions,
    GROUP_CONCAT(a.name, '; ') as artifact_list
FROM theories t
LEFT JOIN artifact_evidence ae ON t.id = ae.theory_id
LEFT JOIN artifacts a ON ae.artifact_id = a.id
LEFT JOIN theory_mentions tm ON t.id = tm.theory_id
GROUP BY t.id, t.name;

-- View: Person Contributions (episodes, events discovered, artifacts found)
CREATE VIEW person_contributions AS
SELECT 
    p.id,
    p.name,
    p.role,
    COUNT(DISTINCT CONCAT(pm.season, pm.episode)) as episodes_featured,
    COUNT(DISTINCT pm.id) as total_mentions,
    COUNT(DISTINCT af.artifact_id) as artifacts_found
FROM people p
LEFT JOIN person_mentions pm ON p.id = pm.person_id
LEFT JOIN artifact_findings af ON pm.season = af.season 
    AND pm.episode = af.episode
GROUP BY p.id, p.name, p.role;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
