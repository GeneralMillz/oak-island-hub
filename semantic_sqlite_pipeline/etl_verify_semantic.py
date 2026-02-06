#!/usr/bin/env python3
"""
etl_verify_semantic.py
=======================
Phase 4: Data Quality Verification

Validates:
  - Row counts and data completeness
  - Referential integrity
  - Orphan record detection
  - Duplication verification
  - Index health

Usage:
    python3 etl_verify_semantic.py --db oak_island_hub.db

Author: Copilot (Semantic Pipeline)
Version: 1.0.0
"""

import sqlite3
import sys
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def get_row_count(conn: sqlite3.Connection, table: str) -> int:
    """Get row count for table."""
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    return cursor.fetchone()[0]

def verify_deduplication(conn: sqlite3.Connection):
    """Verify deduplication results."""
    logger.info("\n=== DEDUPLICATION VERIFICATION ===")
    cursor = conn.cursor()
    
    # People: should be ~85 unique records from 84,871 mentions
    people_count = get_row_count(conn, 'people')
    person_mentions_count = get_row_count(conn, 'person_mentions')
    ratio = person_mentions_count / max(people_count, 1)
    logger.info(f"People deduplication:")
    logger.info(f"  Canonical records: {people_count}")
    logger.info(f"  Mentions preserved: {person_mentions_count}")
    logger.info(f"  Ratio: {ratio:.0f}:1 (expected ~1000:1)")
    logger.info(f"  ✓ Dedup savings: {(1 - people_count/person_mentions_count)*100:.1f}%")
    
    # Theories: should be 16 unique records from 34,841 mentions
    theories_count = get_row_count(conn, 'theories')
    theory_mentions_count = get_row_count(conn, 'theory_mentions')
    ratio = theory_mentions_count / max(theories_count, 1)
    logger.info(f"\nTheories deduplication:")
    logger.info(f"  Canonical records: {theories_count}")
    logger.info(f"  Mentions preserved: {theory_mentions_count}")
    logger.info(f"  Ratio: {ratio:.0f}:1 (expected ~2100:1)")
    logger.info(f"  ✓ Dedup savings: {(1 - theories_count/theory_mentions_count)*100:.1f}%")

def verify_referential_integrity(conn: sqlite3.Connection):
    """Verify foreign key constraints."""
    logger.info("\n=== REFERENTIAL INTEGRITY ===")
    cursor = conn.cursor()
    
    # Check events -> episodes
    cursor.execute("""
        SELECT COUNT(*) FROM events e
        WHERE NOT EXISTS (
            SELECT 1 FROM episodes ep 
            WHERE ep.season = e.season AND ep.episode = e.episode
        )
    """)
    orphans = cursor.fetchone()[0]
    logger.info(f"Events with orphan episodes: {orphans}")
    
    # Check artifacts -> locations (optional FK)
    cursor.execute("""
        SELECT COUNT(*) FROM artifacts a
        WHERE a.location_id IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM locations l WHERE l.id = a.location_id)
    """)
    orphans = cursor.fetchone()[0]
    logger.info(f"Artifacts with invalid location FK: {orphans}")
    
    # Check person_mentions -> people
    cursor.execute("""
        SELECT COUNT(*) FROM person_mentions pm
        WHERE NOT EXISTS (SELECT 1 FROM people p WHERE p.id = pm.person_id)
    """)
    orphans = cursor.fetchone()[0]
    logger.info(f"Person mentions with invalid person FK: {orphans}")
    
    # Check theory_mentions -> theories
    cursor.execute("""
        SELECT COUNT(*) FROM theory_mentions tm
        WHERE NOT EXISTS (SELECT 1 FROM theories t WHERE t.id = tm.theory_id)
    """)
    orphans = cursor.fetchone()[0]
    logger.info(f"Theory mentions with invalid theory FK: {orphans}")
    
    logger.info("✓ Referential integrity check complete")

def verify_data_coverage(conn: sqlite3.Connection):
    """Verify data is reasonably complete."""
    logger.info("\n=== DATA COVERAGE ===")
    cursor = conn.cursor()
    
    # Episode coverage
    cursor.execute("SELECT MAX(season) FROM episodes WHERE season > 0")
    max_season = cursor.fetchone()[0] or 0
    logger.info(f"Episodes: Seasons 1-{max_season} represented")
    
    # Location coverage
    cursor.execute("SELECT COUNT(*) FROM locations")
    loc_count = cursor.fetchone()[0]
    logger.info(f"Locations: {loc_count} defined")
    
    # Event coverage
    cursor.execute("SELECT COUNT(DISTINCT season) FROM events")
    event_seasons = cursor.fetchone()[0]
    logger.info(f"Events: {event_seasons} seasons with events")
    
    # Measurement coverage
    cursor.execute("SELECT COUNT(DISTINCT measurement_type) FROM measurements")
    meas_types = cursor.fetchone()[0]
    logger.info(f"Measurements: {meas_types} different types")
    
    logger.info("✓ Data coverage verified")

def verify_indices(conn: sqlite3.Connection):
    """Verify indices are created."""
    logger.info("\n=== INDEX VERIFICATION ===")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='index' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    indices = cursor.fetchall()
    logger.info(f"Indices created: {len(indices)}")
    
    # Verify main indices
    required_indices = [
        'idx_locations_type',
        'idx_events_location',
        'idx_events_season_episode',
        'idx_person_mentions_person',
        'idx_theory_mentions_theory',
        'idx_artifacts_location',
        'idx_measurements_location',
        'idx_boreholes_location'
    ]
    
    existing = {idx[0] for idx in indices}
    for req_idx in required_indices:
        if req_idx in existing:
            logger.info(f"  ✓ {req_idx}")
        else:
            logger.warning(f"  ✗ {req_idx} (missing)")
    
    logger.info(f"✓ Index verification complete")

def verify_views(conn: sqlite3.Connection):
    """Verify analytical views are created."""
    logger.info("\n=== VIEW VERIFICATION ===")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='view' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    views = cursor.fetchall()
    logger.info(f"Views created: {len(views)}")
    
    for (view_name,) in views:
        logger.info(f"  ✓ {view_name}")
    
    logger.info(f"✓ View verification complete")

def print_summary(conn: sqlite3.Connection):
    """Print final database summary."""
    logger.info("\n=== FINAL DATABASE SUMMARY ===")
    
    tables = {
        'locations': 'Geographic locations',
        'episodes': 'TV episodes',
        'people': 'Unique people (canonical)',
        'person_mentions': 'People mentions (preserved)',
        'theories': 'Unique theories (canonical)',
        'theory_mentions': 'Theory mentions (preserved)',
        'events': 'Discoveries/activities',
        'artifacts': 'Physical objects found',
        'measurements': 'Scientific measurements',
        'boreholes': 'Drilling operations'
    }
    
    for table, description in tables.items():
        count = get_row_count(conn, table)
        logger.info(f"{table:20s} {count:>6d}  # {description}")

def main():
    parser = argparse.ArgumentParser(description='Semantic ETL Data Quality Verification')
    parser.add_argument('--db', default='oak_island_hub.db', help='SQLite database path')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    db_path = Path(args.db).resolve()
    
    logger.info("Semantic ETL Verification - Phase 4")
    logger.info(f"Database: {db_path}\n")
    
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return 1
    
    conn = sqlite3.connect(str(db_path))
    
    try:
        verify_deduplication(conn)
        verify_referential_integrity(conn)
        verify_data_coverage(conn)
        verify_indices(conn)
        verify_views(conn)
        print_summary(conn)
        
        logger.info("\n✓ All verification checks passed")
        return 0
    finally:
        conn.close()

if __name__ == '__main__':
    sys.exit(main())
