#!/usr/bin/env python3
"""
etl_ingest_semantic.py
=======================
Phase 1: Raw Data Ingestion into SQLite

Reads all raw data sources (JSON, JSONL) and populates the semantic database
with canonical entities:
  - Locations
  - Episodes
  - Events
  - Artifacts
  - Measurements
  - Boreholes
  - Temporal metadata

This is the foundational ETL step that prepares data for deduplication.

Usage:
    python3 etl_ingest_semantic.py --db oak_island_hub.db --source-dir ../docs/data --extracted-dir ../data_extracted

Author: Copilot (Semantic Pipeline)
Version: 1.0.0
"""

import json
import sqlite3
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def safe_int(val: Any) -> Optional[int]:
    """Safely convert value to int."""
    if val is None:
        return None
    try:
        return int(float(str(val).strip()))
    except (ValueError, AttributeError):
        return None

def safe_float(val: Any) -> Optional[float]:
    """Safely convert value to float."""
    if val is None:
        return None
    try:
        return float(str(val).strip())
    except (ValueError, AttributeError):
        return None

def load_json(path: Path) -> Any:
    """Load JSON file."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        return None

def load_jsonl(path: Path) -> List[Dict]:
    """Load JSONL file (one JSON object per line)."""
    records = []
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return records
    try:
        with open(path) as f:
            for i, line in enumerate(f, 1):
                if line.strip():
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON on line {i} of {path}: {e}")
        return records
    except Exception as e:
        logger.error(f"Error reading JSONL {path}: {e}")
        return records

# ============================================================================
# INGEST FUNCTIONS
# ============================================================================

def ingest_locations(conn: sqlite3.Connection, locations_json: List[Dict]):
    """Ingest locations from JSON."""
    logger.info(f"Ingesting {len(locations_json)} locations...")
    cursor = conn.cursor()
    
    for loc in locations_json:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO locations 
                (id, name, type, latitude, longitude, description, first_mentioned_season, first_mentioned_episode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                loc.get('id'),
                loc.get('name'),
                loc.get('type', 'unknown'),
                safe_float(loc.get('lat')) or safe_float(loc.get('latitude')),
                safe_float(loc.get('lng')) or safe_float(loc.get('longitude')),
                loc.get('description'),
                None,  # Will be updated during event processing
                None
            ))
        except Exception as e:
            logger.error(f"Error inserting location {loc.get('id')}: {e}")
    
    conn.commit()
    logger.info(f"✓ Ingested {len(locations_json)} locations")

def ingest_episodes(conn: sqlite3.Connection, episodes_data: List[Dict]):
    """Ingest episodes from JSON."""
    logger.info(f"Ingesting {len(episodes_data)} episodes...")
    cursor = conn.cursor()
    
    for ep in episodes_data:
        try:
            season = safe_int(ep.get('season'))
            episode = safe_int(ep.get('episode'))
            
            if season is None or episode is None:
                continue
            
            cursor.execute("""
                INSERT OR REPLACE INTO episodes 
                (id, season, episode, title, air_date, summary)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                f"s{season:02d}e{episode:02d}",
                season,
                episode,
                ep.get('title', ''),
                ep.get('air_date') or ep.get('airDate'),
                ep.get('summary') or ep.get('shortSummary')
            ))
        except Exception as e:
            logger.error(f"Error inserting episode {ep.get('season')}.{ep.get('episode')}: {e}")
    
    conn.commit()
    logger.info(f"✓ Ingested {len(episodes_data)} episodes")

def ingest_events(conn: sqlite3.Connection, events_json: List[Dict]):
    """Ingest events from JSON."""
    logger.info(f"Ingesting {len(events_json)} events...")
    cursor = conn.cursor()
    
    for event in events_json:
        try:
            season = safe_int(event.get('season'))
            episode = safe_int(event.get('episode'))
            
            if season is None or episode is None:
                logger.warning(f"Skipping event with missing season/episode: {event}")
                continue
            
            cursor.execute("""
                INSERT INTO events
                (season, episode, timestamp, event_type, text, confidence, source_ref)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                season,
                episode,
                event.get('timestamp'),
                event.get('event_type', 'unknown'),
                event.get('text', ''),
                safe_float(event.get('confidence', 1.0)),
                event.get('source_refs') or event.get('source_ref')
            ))
        except Exception as e:
            logger.error(f"Error inserting event: {e}")
    
    conn.commit()
    logger.info(f"✓ Ingested {len(events_json)} events")

def ingest_artifacts(conn: sqlite3.Connection, artifacts_jsonl: List[Dict]):
    """Ingest artifacts from JSONL."""
    logger.info(f"Ingesting {len(artifacts_jsonl)} artifacts...")
    cursor = conn.cursor()
    
    for artifact in artifacts_jsonl:
        try:
            attrs = artifact.get('attributes', {})
            ep = artifact.get('episode', {})
            
            cursor.execute("""
                INSERT OR REPLACE INTO artifacts
                (id, name, description, artifact_type, location_id, location_hint, 
                 season, episode, depth_m, depth_reference, confidence, source_file)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                artifact.get('artifact_id'),
                attrs.get('name', ''),
                attrs.get('description'),
                attrs.get('artifact_type', 'unknown'),
                attrs.get('location_id'),
                attrs.get('location_hint'),
                safe_int(ep.get('season')),
                safe_int(ep.get('episode')),
                safe_float(attrs.get('depth_m')),
                attrs.get('depth_reference'),
                safe_float(artifact.get('confidence', 1.0)),
                artifact.get('source', {}).get('file')
            ))
        except Exception as e:
            logger.error(f"Error inserting artifact {artifact.get('artifact_id')}: {e}")
    
    conn.commit()
    logger.info(f"✓ Ingested {len(artifacts_jsonl)} artifacts")

def ingest_measurements(conn: sqlite3.Connection, measurements_json: List[Dict]):
    """Ingest measurements from JSON."""
    logger.info(f"Ingesting {len(measurements_json)} measurements...")
    cursor = conn.cursor()
    
    for i, meas in enumerate(measurements_json):
        try:
            season = safe_int(meas.get('season'))
            episode = safe_int(meas.get('episode'))
            
            if season is None or episode is None:
                continue
            
            cursor.execute("""
                INSERT INTO measurements
                (id, season, episode, timestamp, measurement_type, value, unit, direction, 
                 context, confidence, source_file)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"m_{season}_{episode}_{i}",
                season,
                episode,
                meas.get('timestamp'),
                meas.get('measurement_type', 'unknown'),
                safe_float(meas.get('value')),
                meas.get('unit', ''),
                meas.get('direction'),
                meas.get('context'),
                safe_float(meas.get('confidence', 1.0)),
                meas.get('source_refs') or meas.get('source_file')
            ))
        except Exception as e:
            logger.error(f"Error inserting measurement: {e}")
    
    conn.commit()
    logger.info(f"✓ Ingested {len(measurements_json)} measurements")

def ingest_boreholes(conn: sqlite3.Connection, boreholes_jsonl: List[Dict]):
    """Ingest boreholes from JSONL."""
    logger.info(f"Ingesting {len(boreholes_jsonl)} borehole references...")
    cursor = conn.cursor()
    
    # Track unique boreholes (many mentions for same borehole)
    unique_boreholes = {}
    
    for borehole in boreholes_jsonl:
        try:
            attrs = borehole.get('attributes', {})
            bh_id = borehole.get('borehole_id')
            
            # De-duplicate at ingest time
            if bh_id and bh_id not in unique_boreholes:
                cursor.execute("""
                    INSERT OR IGNORE INTO boreholes
                    (id, bore_number, location_id, location_hint, drill_type)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    bh_id,
                    attrs.get('name', bh_id),
                    attrs.get('location_id'),
                    attrs.get('location_hint'),
                    attrs.get('drill_type', 'unknown')
                ))
                unique_boreholes[bh_id] = True
        except Exception as e:
            logger.error(f"Error inserting borehole {borehole.get('borehole_id')}: {e}")
    
    conn.commit()
    logger.info(f"✓ Ingested {len(unique_boreholes)} unique boreholes from {len(boreholes_jsonl)} references")

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Semantic ETL Phase 1: Ingest raw data into SQLite'
    )
    parser.add_argument('--db', default='oak_island_hub.db', help='SQLite database path')
    parser.add_argument('--source-dir', default='../docs/data', help='Frontend data directory')
    parser.add_argument('--extracted-dir', default='../data_extracted/facts', help='Extracted facts directory')
    parser.add_argument('--drop-existing', action='store_true', help='Drop existing database')
    
    args = parser.parse_args()
    
    source_dir = Path(args.source_dir).resolve()
    extracted_dir = Path(args.extracted_dir).resolve()
    db_path = Path(args.db).resolve()
    
    # Legacy support for relative paths
    if not source_dir.exists():
        source_dir = Path.cwd() / args.source_dir
    if not extracted_dir.exists():
        extracted_dir = Path.cwd() / args.extracted_dir
    
    logger.info(f"Semantic ETL Ingestion - Phase 1")
    logger.info(f"Database: {db_path}")
    logger.info(f"Source Directory: {source_dir}")
    logger.info(f"Extracted Directory: {extracted_dir}")
    
    # Drop existing if requested
    if args.drop_existing and db_path.exists():
        logger.info(f"Dropping existing database: {db_path}")
        db_path.unlink()
    
    # Create/connect database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Load schema
    schema_path = Path(__file__).parent / 'schema.sql'
    if schema_path.exists():
        logger.info(f"Loading schema from {schema_path}...")
        with open(schema_path) as f:
            schema_sql = f.read()
        cursor.executescript(schema_sql)
        conn.commit()
        logger.info("✓ Schema loaded")
    else:
        logger.error(f"Schema file not found: {schema_path}")
        return 1
    
    # Load and ingest locations
    logger.info("\n=== LOCATIONS ===")
    locations = load_json(source_dir / 'locations.json') or []
    ingest_locations(conn, locations)
    
    # Extract locations from oak_island_data.json
    oak_island_data = load_json(source_dir / 'oak_island_data.json') or {}
    if 'locations' in oak_island_data:
        ingest_locations(conn, oak_island_data['locations'])
    
    # Load and ingest episodes
    logger.info("\n=== EPISODES ===")
    episodes_json_data = load_json(source_dir / 'episodes.json') or {}
    # Handle both dict and list formats
    if isinstance(episodes_json_data, dict):
        episodes_json = episodes_json_data.get('episodes', [])
    else:
        episodes_json = episodes_json_data if isinstance(episodes_json_data, list) else []
    
    if oak_island_data.get('seasons'):
        # Flatten seasons into episodes list
        for season in oak_island_data['seasons']:
            if 'episodes' in season:
                episodes_json.extend(season['episodes'])
    ingest_episodes(conn, episodes_json)
    
    # Load and ingest events
    logger.info("\n=== EVENTS ===")
    events = load_json(source_dir / 'events.json') or []
    ingest_events(conn, events)
    
    # Load and ingest artifacts
    logger.info("\n=== ARTIFACTS ===")
    artifacts = load_jsonl(extracted_dir / 'artifacts.jsonl')
    ingest_artifacts(conn, artifacts)
    
    # Load and ingest measurements
    logger.info("\n=== MEASUREMENTS ===")
    measurements = load_json(source_dir / 'measurements.json') or []
    ingest_measurements(conn, measurements)
    
    # Load and ingest boreholes
    logger.info("\n=== BOREHOLES ===")
    boreholes = load_jsonl(extracted_dir / 'boreholes.jsonl')
    ingest_boreholes(conn, boreholes)
    
    # Summary statistics
    logger.info("\n=== INGESTION SUMMARY ===")
    cursor.execute("SELECT COUNT(*) FROM locations")
    logger.info(f"Locations: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM episodes")
    logger.info(f"Episodes: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM events")
    logger.info(f"Events: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM artifacts")
    logger.info(f"Artifacts: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM measurements")
    logger.info(f"Measurements: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM boreholes")
    logger.info(f"Boreholes: {cursor.fetchone()[0]}")
    
    conn.close()
    logger.info("\n✓ Ingestion complete")
    return 0

if __name__ == '__main__':
    sys.exit(main())
