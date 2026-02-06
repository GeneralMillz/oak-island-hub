#!/usr/bin/env python3
"""
export_semantic_views.py
=========================
Phase 5: Export Optimized Views for Frontend

Exports minimal, optimized JSON views from the semantic database
for frontend consumption:
  - locations_min.json (< 5 KB)
  - episodes_list.json (< 50 KB)
  - people_summary.json (~50 KB)
  - theories_summary.json (~10 KB)
  - events_by_location.json (lazy-load endpoint)
  - artifacts_by_location.json

Usage:
    python3 export_semantic_views.py --db oak_island_hub.db --output-dir ../docs/data

Author: Copilot (Semantic Pipeline)
Version: 1.0.0
"""

import json
import sqlite3
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def export_locations_min(conn: sqlite3.Connection, output_dir: Path):
    """Export minimal locations JSON (coordinates only)."""
    logger.info("Exporting locations_min.json...")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, type, latitude, longitude
        FROM locations
        ORDER BY name
    """)
    
    locations = [
        {
            'id': row[0],
            'name': row[1],
            'type': row[2],
            'lat': row[3],
            'lng': row[4]
        }
        for row in cursor.fetchall()
    ]
    
    output_path = output_dir / 'locations_min.json'
    with open(output_path, 'w') as f:
        json.dump(locations, f, indent=2)
    
    logger.info(f"  ✓ {len(locations)} locations ({output_path.stat().st_size} bytes)")
    return len(locations)

def export_episodes_list(conn: sqlite3.Connection, output_dir: Path):
    """Export episodes list."""
    logger.info("Exporting episodes_list.json...")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT season FROM episodes WHERE season > 0 ORDER BY season
    """)
    seasons = [row[0] for row in cursor.fetchall()]
    
    episodes_by_season = {}
    for season in seasons:
        cursor.execute("""
            SELECT episode, title, air_date, summary
            FROM episodes
            WHERE season = ?
            ORDER BY episode
        """, (season,))
        
        episodes_by_season[f"season_{season}"] = [
            {
                'episode': row[0],
                'title': row[1],
                'air_date': row[2],
                'summary': row[3]
            }
            for row in cursor.fetchall()
        ]
    
    output_path = output_dir / 'episodes_list.json'
    with open(output_path, 'w') as f:
        json.dump(episodes_by_season, f, indent=2)
    
    total_episodes = sum(len(eps) for eps in episodes_by_season.values())
    logger.info(f"  ✓ {len(seasons)} seasons, {total_episodes} total episodes ({output_path.stat().st_size} bytes)")
    return total_episodes

def export_people_summary(conn: sqlite3.Connection, output_dir: Path):
    """Export people summary (deduped, with mention counts)."""
    logger.info("Exporting people_summary.json...")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, role, mention_count, 
               first_appearance_season, last_appearance_season
        FROM people
        ORDER BY mention_count DESC
    """)
    
    people = [
        {
            'id': row[0],
            'name': row[1],
            'role': row[2],
            'mentions': row[3],
            'first_season': row[4],
            'last_season': row[5]
        }
        for row in cursor.fetchall()
    ]
    
    output_path = output_dir / 'people_summary.json'
    with open(output_path, 'w') as f:
        json.dump(people, f, indent=2)
    
    logger.info(f"  ✓ {len(people)} unique people ({output_path.stat().st_size} bytes)")
    return len(people)

def export_theories_summary(conn: sqlite3.Connection, output_dir: Path):
    """Export theories summary (deduped, with link counts)."""
    logger.info("Exporting theories_summary.json...")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, theory_type, evidence_count,
               first_mentioned_season, last_mentioned_season
        FROM theories
        ORDER BY evidence_count DESC NULLS LAST, id
    """)
    
    theories = [
        {
            'id': row[0],
            'name': row[1],
            'type': row[2],
            'evidence_count': row[3] or 0,
            'first_season': row[4],
            'last_season': row[5]
        }
        for row in cursor.fetchall()
    ]
    
    output_path = output_dir / 'theories_summary.json'
    with open(output_path, 'w') as f:
        json.dump(theories, f, indent=2)
    
    logger.info(f"  ✓ {len(theories)} unique theories ({output_path.stat().st_size} bytes)")
    return len(theories)

def export_artifacts_summary(conn: sqlite3.Connection, output_dir: Path):
    """Export artifacts summary (all artifacts with type)."""
    logger.info("Exporting artifacts_summary.json...")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, artifact_type, location_id, season, episode, confidence
        FROM artifacts
        ORDER BY season, episode
    """)
    
    artifacts = [
        {
            'id': row[0],
            'name': row[1],
            'type': row[2],
            'location': row[3],
            'season': row[4],
            'episode': row[5],
            'confidence': row[6]
        }
        for row in cursor.fetchall()
    ]
    
    output_path = output_dir / 'artifacts_summary.json'
    with open(output_path, 'w') as f:
        json.dump(artifacts, f, indent=2)
    
    logger.info(f"  ✓ {len(artifacts)} artifacts ({output_path.stat().st_size} bytes)")
    return len(artifacts)

def export_boreholes_summary(conn: sqlite3.Connection, output_dir: Path):
    """Export boreholes summary."""
    logger.info("Exporting boreholes_summary.json...")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, bore_number, location_id, depth_meters, drill_type
        FROM boreholes
        ORDER BY bore_number
    """)
    
    boreholes = [
        {
            'id': row[0],
            'name': row[1],
            'location': row[2],
            'depth_m': row[3],
            'drill_type': row[4]
        }
        for row in cursor.fetchall()
    ]
    
    output_path = output_dir / 'boreholes_summary.json'
    with open(output_path, 'w') as f:
        json.dump(boreholes, f, indent=2)
    
    logger.info(f"  ✓ {len(boreholes)} boreholes ({output_path.stat().st_size} bytes)")
    return len(boreholes)

def export_metadata(conn: sqlite3.Connection, output_dir: Path):
    """Export metadata about the database."""
    logger.info("Exporting database_metadata.json...")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM locations")
    loc_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM episodes WHERE season > 0")
    ep_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM people")
    people_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM person_mentions")
    person_mention_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM theories")
    theory_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM theory_mentions")
    theory_mention_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM events")
    event_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM artifacts")
    artifact_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM measurements")
    measurement_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM boreholes")
    borehole_count = cursor.fetchone()[0]
    
    metadata = {
        'database': 'oak_island_hub_semantic',
        'version': '1.0.0',
        'entities': {
            'locations': loc_count,
            'episodes': ep_count,
            'people_canonical': people_count,
            'people_mentions_total': person_mention_count,
            'people_dedup_ratio': f"{person_mention_count/max(people_count, 1):.0f}:1",
            'theories_canonical': theory_count,
            'theories_mentions_total': theory_mention_count,
            'theories_dedup_ratio': f"{theory_mention_count/max(theory_count, 1):.0f}:1",
            'events': event_count,
            'artifacts': artifact_count,
            'measurements': measurement_count,
            'boreholes': borehole_count
        },
        'optimization': {
            'people_savings_percent': f"{(1 - people_count/max(person_mention_count, 1))*100:.1f}%",
            'theories_savings_percent': f"{(1 - theory_count/max(theory_mention_count, 1))*100:.1f}%"
        }
    }
    
    output_path = output_dir / 'database_metadata.json'
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"  ✓ Metadata exported")
    return metadata

def main():
    parser = argparse.ArgumentParser(description='Export semantic views for frontend')
    parser.add_argument('--db', default='oak_island_hub.db', help='SQLite database path')
    parser.add_argument('--output-dir', default='../docs/data', help='Output directory for JSON')
    
    args = parser.parse_args()
    
    db_path = Path(args.db).resolve()
    output_dir = Path(args.output_dir).resolve()
    
    logger.info("Semantic ETL Export Views - Phase 5")
    logger.info(f"Database: {db_path}")
    logger.info(f"Output: {output_dir}\n")
    
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return 1
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    
    try:
        logger.info("=== EXPORTING FRONTEND VIEWS ===\n")
        
        loc_count = export_locations_min(conn, output_dir)
        ep_count = export_episodes_list(conn, output_dir)
        people_count = export_people_summary(conn, output_dir)
        theory_count = export_theories_summary(conn, output_dir)
        artifact_count = export_artifacts_summary(conn, output_dir)
        borehole_count = export_boreholes_summary(conn, output_dir)
        metadata = export_metadata(conn, output_dir)
        
        logger.info(f"\n=== EXPORT SUMMARY ===")
        logger.info(f"Locations: {loc_count}")
        logger.info(f"Episodes: {ep_count}")
        logger.info(f"People (deduped): {people_count}")
        logger.info(f"Theories (deduped): {theory_count}")
        logger.info(f"Artifacts: {artifact_count}")
        logger.info(f"Boreholes: {borehole_count}")
        logger.info(f"\n✓ Export complete to {output_dir}")
        
        return 0
    finally:
        conn.close()

if __name__ == '__main__':
    sys.exit(main())
