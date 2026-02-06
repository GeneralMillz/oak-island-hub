#!/usr/bin/env python3
"""
etl_dedupe_semantic.py
======================
Phase 2: Intelligent Deduplication

Deduplicates mentions data and creates canonical entities:
  - People: Fuzzy match 84,871 mentions → ~85 unique people
  - Theories: Cluster 34,841 mentions → 16 unique theories
  - Creates junction tables (person_mentions, theory_mentions) for preserved relationships

Uses string similarity matching and semantic clustering.

Usage:
    python3 etl_dedupe_semantic.py --db oak_island_hub.db --extracted-dir ../data_extracted

Author: Copilot (Semantic Pipeline)
Version: 1.0.0
"""

import json
import sqlite3
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
import difflib

# ============================================================================
# CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Fuzzy matching threshold for person names
PERSON_MATCH_THRESHOLD = 0.85

# Known person mappings (canonical deduplication)
KNOWN_PEOPLE = {
    'Rick': 'rick_lagina',
    'Rick Lagina': 'rick_lagina',
    'Marty': 'marty_lagina',
    'Marty Lagina': 'marty_lagina',
    'Gary': 'gary_drayton',
    'Gary Drayton': 'gary_drayton',
    'Craig': 'craig_tester',
    'Jack': 'jack_begley',
    'Dave': 'dave_blond',
    'Dan': 'dan_blankenship',
    'Craig Tester': 'craig_tester',
    'Jack Begley': 'jack_begley',
    'Dave Blond': 'dave_blond',
    'Alex': 'alex_lagina',
    'Laird': 'laird_niven',
    'Charles': 'charles_barkhouse',
    'Doug': 'doug_crowell',
    'Matty': 'matty_blake',
}

# Known theories
KNOWN_THEORIES = {
    'treasure': ('treasure', 'treasure'),
    'templar_cross': ('templar_cross', 'religious'),
    'templar': ('templar', 'religious'),
    'french': ('french', 'historical'),
    'nolan_cross': ('nolan_cross', 'historical'),
    'spanish': ('spanish', 'historical'),
    'british': ('british', 'historical'),
    'zena_map': ('zena_map', 'historical'),
    'pirates': ('pirates', 'historical'),
    'roman': ('roman', 'historical'),
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def string_similarity(s1: str, s2: str) -> float:
    """Calculate string similarity ratio."""
    return difflib.SequenceMatcher(None, s1.lower(), s2.lower()).ratio()

def fuzzy_match_person(name: str, known_people: Dict[str, str]) -> Optional[str]:
    """Fuzzy match person name to known people, returns canonical ID."""
    name_clean = name.strip()
    
    # Exact match
    if name_clean in known_people:
        return known_people[name_clean]
    
    # Fuzzy match
    best_match = None
    best_score = PERSON_MATCH_THRESHOLD
    
    for known_name, canon_id in known_people.items():
        score = string_similarity(name_clean, known_name)
        if score > best_score:
            best_score = score
            best_match = canon_id
    
    # Default: use lowercase name with underscores
    if best_match:
        return best_match
    else:
        return name_clean.lower().replace(' ', '_')

def load_jsonl(path: Path) -> List[Dict]:
    """Load JSONL file."""
    records = []
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return records
    try:
        with open(path) as f:
            for line in f:
                if line.strip():
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return records
    except Exception as e:
        logger.error(f"Error reading {path}: {e}")
        return records

# ============================================================================
# DEDUPLICATION FUNCTIONS
# ============================================================================

def dedupe_people(conn: sqlite3.Connection, people_jsonl: List[Dict]) -> Dict[str, int]:
    """Deduplicate people from 84,871 mentions to ~85 unique."""
    logger.info(f"Deduplicating {len(people_jsonl)} person mentions...\n")
    
    cursor = conn.cursor()
    
    # Build set of unique person names from mentions
    person_mentions = defaultdict(list)
    for mention in people_jsonl:
        name = mention.get('person', '').strip()
        if name:
            person_mentions[name].append(mention)
    
    # Map original names to canonical IDs
    name_to_canonical = {}
    canonical_to_mentions = defaultdict(int)
    
    logger.info(f"Found {len(person_mentions)} unique person names in mentions")
    
    for original_name in person_mentions.keys():
        canonical_id = fuzzy_match_person(original_name, KNOWN_PEOPLE)
        name_to_canonical[original_name] = canonical_id
        canonical_to_mentions[canonical_id] += len(person_mentions[original_name])
    
    # Insert canonical people
    for canonical_id, mention_count in canonical_to_mentions.items():
        # Try to find a good display name
        display_name = canonical_id.replace('_', ' ').title()
        
        cursor.execute("""
            INSERT OR REPLACE INTO people
            (id, name, mention_count)
            VALUES (?, ?, ?)
        """, (canonical_id, display_name, mention_count))
    
    conn.commit()
    logger.info(f"✓ Created {len(canonical_to_mentions)} canonical people records\n")
    logger.info(f"Top 10 most mentioned people:")
    
    sorted_people = sorted(canonical_to_mentions.items(), key=lambda x: x[1], reverse=True)
    for i, (person_id, count) in enumerate(sorted_people[:10], 1):
        logger.info(f"  {i}. {person_id}: {count} mentions")
    
    # Insert person mentions into junction table
    logger.info(f"\nInserting {len(people_jsonl)} person mentions into junction table...")
    for mention in people_jsonl:
        try:
            original_name = mention.get('person', '').strip()
            if not original_name:
                continue
            
            canonical_id = name_to_canonical[original_name]
            season = int(mention.get('season', 0))
            episode = int(mention.get('episode', 0))
            
            cursor.execute("""
                INSERT INTO person_mentions
                (person_id, season, episode, timestamp, text, confidence, mention_type, source_file)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                canonical_id,
                season,
                episode,
                mention.get('timestamp'),
                mention.get('text', ''),
                float(mention.get('confidence', 1.0)),
                'speaker',  # Default mention type
                mention.get('source_file') or mention.get('source_refs')
            ))
        except Exception as e:
            logger.warning(f"Error inserting person mention: {e}")
    
    conn.commit()
    logger.info(f"✓ Inserted person mentions")
    
    return name_to_canonical

def dedupe_theories(conn: sqlite3.Connection, theories_jsonl: List[Dict]) -> Dict[str, int]:
    """Deduplicate theories from 34,841 mentions to 16 unique."""
    logger.info(f"\nDeduplicating {len(theories_jsonl)} theory mentions...\n")
    
    cursor = conn.cursor()
    
    # Build set of unique theory IDs
    theory_mentions = defaultdict(list)
    for mention in theories_jsonl:
        theory_id = mention.get('theory', '').strip()
        if theory_id:
            theory_mentions[theory_id].append(mention)
    
    logger.info(f"Found {len(theory_mentions)} unique theory IDs in mentions")
    
    # Create canonical theories
    canonical_theories = KNOWN_THEORIES.copy()
    canonical_to_mentions = {}
    
    for original_id in theory_mentions.keys():
        theory_id_lower = original_id.lower().replace(' ', '_')
        
        if theory_id_lower not in canonical_theories:
            # New theory - add with defaults
            canonical_theories[theory_id_lower] = (theory_id_lower, 'other')
        
        canonical_id = canonical_theories[theory_id_lower][0]
        canonical_to_mentions[canonical_id] = canonical_to_mentions.get(canonical_id, 0) + len(theory_mentions[original_id])
    
    # Insert canonical theories
    for theory_id, (display_name, theory_type) in canonical_theories.items():
        mention_count = canonical_to_mentions.get(theory_id, 0)
        
        cursor.execute("""
            INSERT OR REPLACE INTO theories
            (id, name, theory_type, evidence_count)
            VALUES (?, ?, ?, ?)
        """, (
            theory_id,
            display_name.replace('_', ' ').title(),
            theory_type,
            mention_count
        ))
    
    conn.commit()
    logger.info(f"✓ Created {len(canonical_theories)} canonical theory records\n")
    logger.info("Core theories:")
    
    for i, (theory_id, mention_count) in enumerate(sorted(canonical_to_mentions.items(), key=lambda x: x[1], reverse=True), 1):
        logger.info(f"  {i}. {theory_id}: {mention_count} mentions")
    
    # Map original IDs to canonical IDs
    id_to_canonical = {}
    for original_id in theory_mentions.keys():
        theory_id_lower = original_id.lower().replace(' ', '_')
        canonical_id = canonical_theories[theory_id_lower][0]
        id_to_canonical[original_id] = canonical_id
    
    # Insert theory mentions
    logger.info(f"\nInserting {len(theories_jsonl)} theory mentions into junction table...")
    for mention in theories_jsonl:
        try:
            original_id = mention.get('theory', '').strip()
            if not original_id:
                continue
            
            canonical_id = id_to_canonical[original_id]
            season = int(mention.get('season', 0))
            episode = int(mention.get('episode', 0))
            
            cursor.execute("""
                INSERT INTO theory_mentions
                (theory_id, season, episode, timestamp, text, confidence, mention_type, source_file)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                canonical_id,
                season,
                episode,
                mention.get('timestamp'),
                mention.get('text', ''),
                float(mention.get('confidence', 1.0)),
                'discussed',  # Default mention type
                mention.get('source_file') or mention.get('source_refs')
            ))
        except Exception as e:
            logger.warning(f"Error inserting theory mention: {e}")
    
    conn.commit()
    logger.info(f"✓ Inserted theory mentions")
    
    return id_to_canonical

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Semantic ETL Phase 2: Deduplicate people and theories'
    )
    parser.add_argument('--db', default='oak_island_hub.db', help='SQLite database path')
    parser.add_argument('--extracted-dir', default='../data_extracted/facts', help='Extracted facts directory')
    
    args = parser.parse_args()
    
    extracted_dir = Path(args.extracted_dir).resolve()
    db_path = Path(args.db).resolve()
    
    if not extracted_dir.exists():
        extracted_dir = Path.cwd() / args.extracted_dir
    
    logger.info("Semantic ETL Deduplication - Phase 2")
    logger.info(f"Database: {db_path}")
    logger.info(f"Extracted Directory: {extracted_dir}\n")
    
    # Connect to database
    conn = sqlite3.connect(str(db_path))
    
    # Load and dedupe people
    logger.info("=== PEOPLE DEDUPLICATION ===")
    people_jsonl = load_jsonl(extracted_dir / 'people.jsonl')
    person_mapping = dedupe_people(conn, people_jsonl)
    
    # Load and dedupe theories
    logger.info("=== THEORIES DEDUPLICATION ===")
    theories_jsonl = load_jsonl(extracted_dir / 'theories.jsonl')
    theory_mapping = dedupe_theories(conn, theories_jsonl)
    
    # Summary
    logger.info("\n=== DEDUPLICATION SUMMARY ===")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM people")
    logger.info(f"Canonical people: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM person_mentions")
    logger.info(f"Person mentions preserved: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM theories")
    logger.info(f"Canonical theories: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM theory_mentions")
    logger.info(f"Theory mentions preserved: {cursor.fetchone()[0]}")
    
    conn.close()
    logger.info("\n✓ Deduplication complete")
    return 0

if __name__ == '__main__':
    sys.exit(main())
