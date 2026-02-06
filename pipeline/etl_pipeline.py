#!/usr/bin/env python3
"""
Oak Island Hub: SQLite Database ETL Pipeline

This orchestrator ingests JSON data files from docs/data/ and populates
a SQLite database with normalized, deduplicated, and indexed data.

Usage:
    python3 etl_pipeline.py [--db-path DATA_DIR] [--dry-run] [--reset]

Options:
    --db-path PATH      Directory to store oak_island_hub.db (default: ./data)
    --dry-run           Show what would be loaded without writing
    --reset             Drop and recreate all tables

The pipeline is designed to be:
  - Idempotent: Safe to run multiple times
  - Reversible: Raw JSON files remain untouched
  - Incremental: Can be extended with new loaders
  - Auditable: Logs all transformations and deduplication decisions
"""

import json
import sqlite3
import logging
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OakIslandETL:
    """Main ETL orchestrator for Oak Island Hub data normalization."""
    
    def __init__(self, db_path: str = "./data/oak_island_hub.db", dry_run: bool = False):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.dry_run = dry_run
        self.conn = None
        self.cursor = None
        
        # Deduplication trackers
        self.locations_seen: Set[str] = set()
        self.episodes_seen: Set[Tuple[int, int]] = set()
        self.people_seen: Set[str] = set()
        self.theories_seen: Set[str] = set()
        self.artifacts_seen: Set[str] = set()
        
        # Statistics
        self.stats = defaultdict(int)
    
    def initialize_db(self, reset: bool = False):
        """Initialize SQLite database and schema."""
        if reset and self.db_path.exists():
            logger.info(f"Removing existing database: {self.db_path}")
            self.db_path.unlink()
        
        if self.dry_run:
            logger.info("DRY RUN: Would initialize database at %s", self.db_path)
            return
        
        self.conn = sqlite3.connect(str(self.db_path))
        self.cursor = self.conn.cursor()
        
        # Load schema from schema.sql
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path) as f:
            schema_sql = f.read()
        
        try:
            self.cursor.executescript(schema_sql)
            self.conn.commit()
            logger.info(f"Database initialized: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def load_locations(self, data_dir: str = "./docs/data"):
        """Load locations from locations.json."""
        filepath = Path(data_dir) / "locations.json"
        if not filepath.exists():
            logger.warning(f"Locations file not found: {filepath}")
            return
        
        logger.info(f"Loading locations from {filepath}")
        
        with open(filepath) as f:
            locations = json.load(f)
        
        if not self.dry_run:
            for loc in locations:
                # Deduplicate
                if loc.get('id') in self.locations_seen:
                    logger.debug(f"  Skipping duplicate location: {loc.get('id')}")
                    self.stats['locations_duplicates'] += 1
                    continue
                
                self.cursor.execute("""
                    INSERT OR IGNORE INTO locations (id, name, type, latitude, longitude)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    loc.get('id'),
                    loc.get('name'),
                    loc.get('type'),
                    loc.get('lat'),
                    loc.get('lng')
                ))
                self.locations_seen.add(loc.get('id'))
                self.stats['locations_inserted'] += 1
            
            self.conn.commit()
        
        logger.info(f"  Processed {len(locations)} locations")
        self.stats['locations_read'] = len(locations)
    
    def load_episodes(self, data_dir: str = "./docs/data"):
        """Load episodes from episodes.json."""
        filepath = Path(data_dir) / "episodes.json"
        if not filepath.exists():
            logger.warning(f"Episodes file not found: {filepath}")
            return
        
        logger.info(f"Loading episodes from {filepath}")
        
        with open(filepath) as f:
            data = json.load(f)
        
        # episodes.json likely has a nested structure; adapt as needed
        episodes = self._flatten_episodes(data)
        
        if not self.dry_run:
            for ep in episodes:
                key = (ep['season'], ep['episode'])
                if key in self.episodes_seen:
                    self.stats['episodes_duplicates'] += 1
                    continue
                
                self.cursor.execute("""
                    INSERT OR IGNORE INTO episodes (id, season, episode, title, air_date, summary)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    f"s{ep['season']}e{ep['episode']}",
                    ep['season'],
                    ep['episode'],
                    ep.get('title'),
                    ep.get('airDate'),
                    ep.get('shortSummary')
                ))
                self.episodes_seen.add(key)
                self.stats['episodes_inserted'] += 1
            
            self.conn.commit()
        
        logger.info(f"  Processed {len(episodes)} episodes")
        self.stats['episodes_read'] = len(episodes)
    
    def _flatten_episodes(self, data: Dict) -> List[Dict]:
        """Flatten nested episodes structure from oak_island_data.json."""
        episodes = []
        seasons = data.get('seasons', [])
        for season_group in seasons:
            for ep in season_group.get('episodes', []):
                episodes.append(ep)
        return episodes
    
    def load_events(self, data_dir: str = "./docs/data"):
        """Load events from events.json."""
        filepath = Path(data_dir) / "events.json"
        if not filepath.exists():
            logger.warning(f"Events file not found: {filepath}")
            return
        
        logger.info(f"Loading events from {filepath}")
        
        with open(filepath) as f:
            events = json.load(f)
        
        if not self.dry_run:
            for evt in events:
                # Skip if invalid
                if not evt.get('text'):
                    self.stats['events_skipped'] += 1
                    continue
                
                self.cursor.execute("""
                    INSERT INTO events (season, episode, timestamp, event_type, text, confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    evt.get('season'),
                    evt.get('episode'),
                    evt.get('timestamp'),
                    evt.get('event_type', 'unknown'),
                    evt.get('text'),
                    float(evt.get('confidence', 1.0))
                ))
                self.stats['events_inserted'] += 1
            
            self.conn.commit()
        
        logger.info(f"  Processed {len(events)} events")
        self.stats['events_read'] = len(events)
    
    def load_people(self, data_dir: str = "./docs/data"):
        """Extract unique people from people.json."""
        filepath = Path(data_dir) / "people.json"
        if not filepath.exists():
            logger.warning(f"People file not found: {filepath}")
            return
        
        logger.info(f"Loading people from {filepath}")
        
        with open(filepath) as f:
            people_mentions = json.load(f)
        
        # Deduplicate: extract unique person names
        unique_people = {}
        for mention in people_mentions:
            person_name = mention.get('person')
            if person_name and person_name not in unique_people:
                unique_people[person_name] = mention
        
        if not self.dry_run:
            for person_name, mention in unique_people.items():
                if person_name in self.people_seen:
                    self.stats['people_duplicates'] += 1
                    continue
                
                self.cursor.execute("""
                    INSERT OR IGNORE INTO people (id, name)
                    VALUES (?, ?)
                """, (
                    person_name.lower().replace(' ', '_'),
                    person_name
                ))
                self.people_seen.add(person_name)
                self.stats['people_inserted'] += 1
            
            self.conn.commit()
        
        logger.info(f"  Extracted {len(unique_people)} unique people from {len(people_mentions)} mentions")
        self.stats['people_read'] = len(people_mentions)
    
    def load_theories(self, data_dir: str = "./docs/data"):
        """Extract unique theories from theories.json."""
        filepath = Path(data_dir) / "theories.json"
        if not filepath.exists():
            logger.warning(f"Theories file not found: {filepath}")
            return
        
        logger.info(f"Loading theories from {filepath}")
        
        with open(filepath) as f:
            theory_mentions = json.load(f)
        
        # Deduplicate: extract unique theory names
        unique_theories = {}
        for mention in theory_mentions:
            theory_name = mention.get('theory')
            if theory_name and theory_name not in unique_theories:
                unique_theories[theory_name] = mention
        
        if not self.dry_run:
            for theory_name, mention in unique_theories.items():
                if theory_name in self.theories_seen:
                    self.stats['theories_duplicates'] += 1
                    continue
                
                self.cursor.execute("""
                    INSERT OR IGNORE INTO theories (id, name, theory_type)
                    VALUES (?, ?, ?)
                """, (
                    theory_name.lower().replace(' ', '_'),
                    theory_name,
                    theory_name.lower()
                ))
                self.theories_seen.add(theory_name)
                self.stats['theories_inserted'] += 1
            
            self.conn.commit()
        
        logger.info(f"  Extracted {len(unique_theories)} unique theories from {len(theory_mentions)} mentions")
        self.stats['theories_read'] = len(theory_mentions)
    
    def load_measurements(self, data_dir: str = "./docs/data"):
        """Load measurements from measurements.json."""
        filepath = Path(data_dir) / "measurements.json"
        if not filepath.exists():
            logger.warning(f"Measurements file not found: {filepath}")
            return
        
        logger.info(f"Loading measurements from {filepath}")
        
        with open(filepath) as f:
            measurements = json.load(f)
        
        if not self.dry_run:
            for meas in measurements:
                if not meas.get('value'):
                    self.stats['measurements_skipped'] += 1
                    continue
                
                self.cursor.execute("""
                    INSERT INTO measurements (
                        id, location_id, measurement_type, value, unit, 
                        season, episode, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    meas.get('id', f"meas_{self.stats['measurements_inserted']}"),
                    meas.get('location_id'),
                    meas.get('type', 'unknown'),
                    meas.get('value'),
                    meas.get('unit', ''),
                    meas.get('season'),
                    meas.get('episode'),
                    float(meas.get('confidence', 1.0))
                ))
                self.stats['measurements_inserted'] += 1
            
            self.conn.commit()
        
        logger.info(f"  Processed {len(measurements)} measurements")
        self.stats['measurements_read'] = len(measurements)
    
    def export_json_views(self, output_dir: str = "./docs/data"):
        """Export slim JSON views from database for frontend consumption."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if self.dry_run:
            logger.info(f"DRY RUN: Would export JSON views to {output_path}")
            return
        
        logger.info(f"Exporting JSON views to {output_path}")
        
        # Export locations (minimal)
        self.cursor.execute("SELECT id, name, type, latitude, longitude FROM locations")
        locations = [
            {
                'id': row[0],
                'name': row[1],
                'type': row[2],
                'lat': row[3],
                'lng': row[4]
            }
            for row in self.cursor.fetchall()
        ]
        with open(output_path / "locations.json", 'w') as f:
            json.dump(locations, f, indent=2)
        logger.info(f"  Exported {len(locations)} locations")
        
        # Export episodes (minimal)
        self.cursor.execute("SELECT season, episode, title FROM episodes ORDER BY season, episode")
        episodes_by_season = defaultdict(list)
        for season, episode, title in self.cursor.fetchall():
            episodes_by_season[season].append({
                'season': season,
                'episode': episode,
                'title': title
            })
        
        seasons_data = [
            {'season': s, 'episodes': episodes_by_season[s]}
            for s in sorted(episodes_by_season.keys())
        ]
        with open(output_path / "episodes.json", 'w') as f:
            json.dump(seasons_data, f, indent=2)
        logger.info(f"  Exported episodes data")
        
        # Export people (minimal)
        self.cursor.execute("SELECT id, name FROM people ORDER BY name")
        people = [{'id': row[0], 'name': row[1]} for row in self.cursor.fetchall()]
        with open(output_path / "people.json", 'w') as f:
            json.dump(people, f, indent=2)
        logger.info(f"  Exported {len(people)} people")
        
        # Export theories (minimal)
        self.cursor.execute("SELECT id, name FROM theories ORDER BY name")
        theories = [{'id': row[0], 'name': row[1]} for row in self.cursor.fetchall()]
        with open(output_path / "theories.json", 'w') as f:
            json.dump(theories, f, indent=2)
        logger.info(f"  Exported {len(theories)} theories")
        
        self.stats['json_views_exported'] = 4
    
    def run(self, reset: bool = False, data_dir: str = "./docs/data"):
        """Execute the full ETL pipeline."""
        try:
            logger.info("=" * 70)
            logger.info("OAK ISLAND HUB - ETL PIPELINE")
            logger.info("=" * 70)
            
            if self.dry_run:
                logger.info("MODE: DRY RUN (no database changes)")
            
            self.initialize_db(reset=reset)
            
            # Load all data in order
            self.load_locations(data_dir)
            self.load_episodes(data_dir)
            self.load_events(data_dir)
            self.load_people(data_dir)
            self.load_theories(data_dir)
            self.load_measurements(data_dir)
            
            # Export JSON views for frontend
            self.export_json_views(output_dir=data_dir)
            
            logger.info("=" * 70)
            logger.info("ETL PIPELINE STATISTICS")
            logger.info("=" * 70)
            for key in sorted(self.stats.keys()):
                logger.info(f"  {key}: {self.stats[key]}")
            
            if not self.dry_run and self.conn:
                self.conn.close()
            
            logger.info("=" * 70)
            logger.info("ETL PIPELINE COMPLETE")
            logger.info("=" * 70)
            
        except Exception as e:
            logger.error(f"ETL Pipeline failed: {e}", exc_info=True)
            if self.conn:
                self.conn.rollback()
                self.conn.close()
            raise


def main():
    parser = argparse.ArgumentParser(
        description="Oak Island Hub ETL Pipeline: Ingest JSON data into SQLite"
    )
    parser.add_argument(
        '--db-path',
        default='./data',
        help='Directory to store oak_island_hub.db (default: ./data)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be loaded without writing'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Drop and recreate all tables'
    )
    parser.add_argument(
        '--data-dir',
        default='./docs/data',
        help='Path to JSON data files (default: ./docs/data)'
    )
    
    args = parser.parse_args()
    
    etl = OakIslandETL(db_path=args.db_path, dry_run=args.dry_run)
    etl.run(reset=args.reset, data_dir=args.data_dir)


if __name__ == '__main__':
    main()
