-- =========================
-- Oak Island Research Database Schema (SQLite Version)
-- =========================

-- =========================
-- Core Entities
-- =========================

CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER NOT NULL,
    episode INTEGER NOT NULL,
    title TEXT NOT NULL,
    air_date TEXT,
    summary TEXT,
    runtime INTEGER,
    tmdb_episode_id INTEGER,
    tmdb_show_id INTEGER,
    UNIQUE(season, episode)
);

CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id TEXT UNIQUE,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    lat REAL,
    lng REAL,
    first_documented_year INTEGER,
    description TEXT
);

CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id TEXT UNIQUE,
    name TEXT NOT NULL,
    type TEXT,
    location_id INTEGER,
    season INTEGER,
    episode INTEGER,
    confidence REAL,
    description TEXT,
    FOREIGN KEY(location_id) REFERENCES locations(id)
);

CREATE TABLE IF NOT EXISTS boreholes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    borehole_id TEXT UNIQUE,
    name TEXT NOT NULL,
    location_id INTEGER,
    lat REAL,
    lng REAL,
    collar_elevation_m REAL,
    max_depth_m REAL,
    drill_method TEXT,
    era TEXT,
    source_priority TEXT,
    source_refs TEXT,
    FOREIGN KEY(location_id) REFERENCES locations(id)
);

CREATE TABLE IF NOT EXISTS borehole_intervals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    borehole_id INTEGER,
    depth_from_m REAL,
    depth_to_m REAL,
    material TEXT,
    water_intrusion INTEGER,
    sample_taken INTEGER,
    sample_type TEXT,
    lab_result_ref TEXT,
    confidence REAL,
    source_refs TEXT,
    FOREIGN KEY(borehole_id) REFERENCES boreholes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id INTEGER,
    timestamp TEXT,
    measurement_type TEXT,
    value TEXT,
    unit TEXT,
    direction TEXT,
    context TEXT,
    confidence REAL,
    source_refs TEXT,
    FOREIGN KEY(episode_id) REFERENCES episodes(id)
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id INTEGER,
    timestamp TEXT,
    event_type TEXT,
    text TEXT,
    confidence REAL,
    source_refs TEXT,
    FOREIGN KEY(episode_id) REFERENCES episodes(id)
);

CREATE TABLE IF NOT EXISTS theories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id INTEGER,
    timestamp TEXT,
    theory TEXT,
    text TEXT,
    confidence REAL,
    source_refs TEXT,
    FOREIGN KEY(episode_id) REFERENCES episodes(id)
);

CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT,
    name TEXT NOT NULL,
    role TEXT,
    UNIQUE(name)
);

-- =========================
-- Many-to-Many Linking Tables
-- =========================

CREATE TABLE IF NOT EXISTS event_people (
    event_id INTEGER,
    person_id INTEGER,
    PRIMARY KEY (event_id, person_id),
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY(person_id) REFERENCES people(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS event_locations (
    event_id INTEGER,
    location_id INTEGER,
    PRIMARY KEY (event_id, location_id),
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY(location_id) REFERENCES locations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS artifact_episodes (
    artifact_id INTEGER,
    episode_id INTEGER,
    PRIMARY KEY (artifact_id, episode_id),
    FOREIGN KEY(artifact_id) REFERENCES artifacts(id) ON DELETE CASCADE,
    FOREIGN KEY(episode_id) REFERENCES episodes(id) ON DELETE CASCADE
);

-- =========================
-- Geospatial Tables
-- =========================

CREATE TABLE IF NOT EXISTS geometries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    geojson TEXT,
    source TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS lidar_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL,
    type TEXT,
    bounds TEXT,
    metadata TEXT
);

-- =========================
-- Auxiliary Tables
-- =========================

CREATE TABLE IF NOT EXISTS transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id INTEGER,
    text TEXT,
    source_file TEXT,
    FOREIGN KEY(episode_id) REFERENCES episodes(id)
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_time TEXT DEFAULT CURRENT_TIMESTAMP,
    level TEXT,
    message TEXT,
    context TEXT
);

CREATE TABLE IF NOT EXISTS conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT,
    entity_id TEXT,
    conflict_type TEXT,
    details TEXT,
    resolved INTEGER DEFAULT 0
);

-- =========================
-- Indexes
-- =========================

CREATE INDEX IF NOT EXISTS idx_episodes_season_episode ON episodes(season, episode);
CREATE INDEX IF NOT EXISTS idx_events_episode_id ON events(episode_id);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_locations_type ON locations(type);
CREATE INDEX IF NOT EXISTS idx_artifacts_location_id ON artifacts(location_id);
CREATE INDEX IF NOT EXISTS idx_boreholes_location_id ON boreholes(location_id);
CREATE INDEX IF NOT EXISTS idx_measurements_episode_id ON measurements(episode_id);
CREATE INDEX IF NOT EXISTS idx_theories_episode_id ON theories(episode_id);
CREATE INDEX IF NOT EXISTS idx_people_name ON people(name);

-- =========================
-- Summary Tables (SQLite replacement for Materialized Views)
-- =========================

CREATE TABLE IF NOT EXISTS episodes_list AS SELECT * FROM episodes WHERE 0;
CREATE TABLE IF NOT EXISTS locations_min AS SELECT * FROM locations WHERE 0;
CREATE TABLE IF NOT EXISTS theories_summary AS SELECT * FROM theories WHERE 0;
CREATE TABLE IF NOT EXISTS people_summary AS SELECT * FROM people WHERE 0;
CREATE TABLE IF NOT EXISTS artifacts_summary AS SELECT * FROM artifacts WHERE 0;
CREATE TABLE IF NOT EXISTS boreholes_summary AS SELECT * FROM boreholes WHERE 0;
CREATE TABLE IF NOT EXISTS database_metadata AS SELECT 0 AS episode_count;
