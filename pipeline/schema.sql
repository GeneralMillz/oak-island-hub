-- Oak Island Hub SQLite Schema
-- Canonical database for all Oak Island entities
-- Generated: 2026-02-05

-- Locations (geographic points, sites, features)
CREATE TABLE locations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL,  -- 'shaft', 'landmark', 'feature', 'shore', 'swamp', etc.
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    description TEXT,
    first_mentioned_season INTEGER,
    first_mentioned_episode INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Episodes (TV episode metadata)
CREATE TABLE episodes (
    id TEXT PRIMARY KEY,
    season INTEGER NOT NULL,
    episode INTEGER NOT NULL,
    title TEXT NOT NULL,
    air_date TEXT,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(season, episode)
);

-- People (recurring characters)
CREATE TABLE people (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    role TEXT,  -- 'host', 'expert', 'researcher', etc.
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Events (discoveries, activities, findings by season/episode)
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER NOT NULL,
    episode INTEGER NOT NULL,
    timestamp TEXT,  -- HH:MM:SS.mmm format
    event_type TEXT NOT NULL,  -- 'discovery', 'research', 'excavation', 'wood_find', etc.
    text TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    location_id TEXT,
    source_ref TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations(id),
    FOREIGN KEY (season, episode) REFERENCES episodes(season, episode)
);

-- Artifacts (objects found during excavation)
CREATE TABLE artifacts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    artifact_type TEXT,  -- 'coin', 'wood', 'stone', 'metal', etc.
    location_id TEXT,
    season INTEGER,
    episode INTEGER,
    confidence REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations(id),
    FOREIGN KEY (season, episode) REFERENCES episodes(season, episode)
);

-- Theories (historical/archaeological theories)
CREATE TABLE theories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    theory_type TEXT,  -- 'treasure', 'military', 'religious', 'historical', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Theory mentions (linking theories to events/episodes)
CREATE TABLE theory_mentions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    theory_id TEXT NOT NULL,
    season INTEGER,
    episode INTEGER,
    timestamp TEXT,
    text TEXT,
    confidence REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (theory_id) REFERENCES theories(id),
    FOREIGN KEY (season, episode) REFERENCES episodes(season, episode)
);

-- Measurements (scientific measurements at locations)
CREATE TABLE measurements (
    id TEXT PRIMARY KEY,
    location_id TEXT NOT NULL,
    measurement_type TEXT NOT NULL,  -- 'depth', 'temperature', 'magnetic', 'radiation', etc.
    value REAL NOT NULL,
    unit TEXT NOT NULL,  -- 'meters', 'celsius', 'gauss', etc.
    season INTEGER,
    episode INTEGER,
    timestamp TEXT,
    notes TEXT,
    confidence REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations(id),
    FOREIGN KEY (season, episode) REFERENCES episodes(season, episode)
);

-- Boreholes (subsurface drilling data)
CREATE TABLE boreholes (
    id TEXT PRIMARY KEY,
    location_id TEXT,
    bore_number TEXT,
    depth_meters REAL,
    description TEXT,
    season INTEGER,
    episode INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations(id),
    FOREIGN KEY (season, episode) REFERENCES episodes(season, episode)
);

-- Indices for common queries
CREATE INDEX idx_events_location ON events(location_id);
CREATE INDEX idx_events_season_episode ON events(season, episode);
CREATE INDEX idx_artifacts_location ON artifacts(location_id);
CREATE INDEX idx_theories_type ON theories(theory_type);
CREATE INDEX idx_theory_mentions_theory ON theory_mentions(theory_id);
CREATE INDEX idx_measurements_location ON measurements(location_id);
CREATE INDEX idx_boreholes_location ON boreholes(location_id);
