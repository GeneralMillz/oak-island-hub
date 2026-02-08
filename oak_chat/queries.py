# oak_chat/queries.py


from typing import List, Dict, Any, Optional
from sqlalchemy import text
from etl.db import get_session
import logging

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# ---------- helpers ----------


def _rows_to_dicts(result, rows) -> List[Dict[str, Any]]:
    """
    Convert SQLAlchemy result rows into list-of-dicts.
    Args:
        result: SQLAlchemy result object (provides .keys()).
        rows: Iterable of row tuples.
    Returns:
        List of dictionaries mapping column names to values.
    """
    cols = result.keys()
    if not rows:
        return []
    return [dict(zip(cols, row)) for row in rows]


# Context manager for session handling
from contextlib import contextmanager

@contextmanager
def session_scope():
    """
    Provide a transactional scope around a series of operations.
    Ensures session is closed and logs errors.
    """
    session = get_session()
    try:
        yield session
    except Exception as exc:
        logger.exception("Database session error: %s", exc)
        raise
    finally:
        session.close()


# ---------- core episode queries ----------

def get_episode_by_season_episode(season: int, episode: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a single episode by season and episode number.
    Returns None if not found.
    """
    logger.debug("Querying episode for season=%s, episode=%s", season, episode)
    with session_scope() as session:
        result = session.execute(
            text("""
                SELECT *
                FROM episodes
                WHERE season = :season AND episode = :episode
                LIMIT 1
            """),
            {"season": season, "episode": episode}
        )
        row = result.fetchone()
        if not row:
            return None
        return _rows_to_dicts(result, [row])[0]


def find_episodes_mentioning_person(name: str) -> List[Dict[str, Any]]:
    """
    Find episodes mentioning a given person's name in events, theories, or transcripts.
    """
    logger.debug("Searching for episodes mentioning person: %s", name)
    with session_scope() as session:
        pattern = f"%{name.lower()}%"
        result = session.execute(
            text("""
                SELECT DISTINCT ep.id,
                       ep.season,
                       ep.episode,
                       ep.title
                FROM episodes ep
                LEFT JOIN events e ON e.episode_id = ep.id
                LEFT JOIN theories t ON t.episode_id = ep.id
                LEFT JOIN transcripts tr ON tr.episode_id = ep.id
                WHERE LOWER(COALESCE(e.text, '')) LIKE :pattern
                   OR LOWER(COALESCE(t.text, '')) LIKE :pattern
                   OR LOWER(COALESCE(tr.text, '')) LIKE :pattern
                ORDER BY ep.season, ep.episode
            """),
            {"pattern": pattern}
        )
        rows = result.fetchall()
        return _rows_to_dicts(result, rows)


def find_episodes_mentioning_term(term: str) -> List[Dict[str, Any]]:
    """
    Alias for find_episodes_mentioning_person; for clarity in code using 'term'.
    """
    return find_episodes_mentioning_person(term)


# ---------- text search queries ----------

def search_events_text(query: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Search for events whose text matches the query string.
    """
    logger.debug("Searching events text for query: '%s' (limit %d)", query, limit)
    with session_scope() as session:
        pattern = f"%{query.lower()}%"
        result = session.execute(
            text("""
                SELECT e.id,
                       e.episode_id,
                       ep.season,
                       ep.episode,
                       ep.title,
                       e.timestamp,
                       e.event_type,
                       e.text
                FROM events e
                JOIN episodes ep ON ep.id = e.episode_id
                WHERE LOWER(e.text) LIKE :pattern
                ORDER BY ep.season, ep.episode, e.timestamp
                LIMIT :limit
            """),
            {"pattern": pattern, "limit": limit}
        )
        rows = result.fetchall()
        return _rows_to_dicts(result, rows)


def search_theories_text(query: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Search for theories whose text matches the query string.
    """
    logger.debug("Searching theories text for query: '%s' (limit %d)", query, limit)
    with session_scope() as session:
        pattern = f"%{query.lower()}%"
        result = session.execute(
            text("""
                SELECT t.id,
                       t.episode_id,
                       ep.season,
                       ep.episode,
                       ep.title,
                       t.text
                FROM theories t
                JOIN episodes ep ON ep.id = t.episode_id
                WHERE LOWER(t.text) LIKE :pattern
                ORDER BY ep.season, ep.episode, t.id
                LIMIT :limit
            """),
            {"pattern": pattern, "limit": limit}
        )
        rows = result.fetchall()
        return _rows_to_dicts(result, rows)


def search_transcripts_text(query: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Search for transcripts whose text matches the query string.
    """
    logger.debug("Searching transcripts text for query: '%s' (limit %d)", query, limit)
    with session_scope() as session:
        pattern = f"%{query.lower()}%"
        result = session.execute(
            text("""
                SELECT tr.id,
                       tr.episode_id,
                       ep.season,
                       ep.episode,
                       ep.title,
                       tr.text
                FROM transcripts tr
                JOIN episodes ep ON ep.id = tr.episode_id
                WHERE LOWER(tr.text) LIKE :pattern
                ORDER BY ep.season, ep.episode, tr.id
                LIMIT :limit
            """),
            {"pattern": pattern, "limit": limit}
        )
        rows = result.fetchall()
        return _rows_to_dicts(result, rows)


# ---------- location / timeline helpers ----------

def episodes_for_location_name(name: str) -> List[Dict[str, Any]]:
    """
    Alias for find_episodes_mentioning_term; for clarity in code using 'location name'.
    """
    return find_episodes_mentioning_term(name)


def timeline_for_term(term: str, limit_per_source: int = 50) -> List[Dict[str, Any]]:
    """
    Get a timeline of events and theories mentioning a term, ordered by episode and timestamp.
    """
    logger.debug("Building timeline for term: '%s' (limit per source: %d)", term, limit_per_source)
    with session_scope() as session:
        pattern = f"%{term.lower()}%"
        result = session.execute(
            text("""
                SELECT 'event' AS source,
                       e.id AS source_id,
                       e.episode_id,
                       ep.season,
                       ep.episode,
                       ep.title,
                       e.timestamp,
                       e.event_type AS subtype,
                       e.text
                FROM events e
                JOIN episodes ep ON ep.id = e.episode_id
                WHERE LOWER(e.text) LIKE :pattern

                UNION ALL

                SELECT 'theory' AS source,
                       t.id AS source_id,
                       t.episode_id,
                       ep.season,
                       ep.episode,
                       ep.title,
                       NULL AS timestamp,
                       NULL AS subtype,
                       t.text
                FROM theories t
                JOIN episodes ep ON ep.id = t.episode_id
                WHERE LOWER(t.text) LIKE :pattern

                ORDER BY season, episode, COALESCE(timestamp, '99:99:99.999')
                LIMIT :limit
            """),
            {"pattern": pattern, "limit": limit_per_source}
        )
        rows = result.fetchall()
        return _rows_to_dicts(result, rows)


def summarize_location_seed(name: str, limit: int = 20) -> Dict[str, List[Dict[str, Any]]]:
    """
    Summarize a location by collecting related events, theories, and episodes.
    """
    logger.debug("Summarizing location seed for: '%s' (limit %d)", name, limit)
    events = search_events_text(name, limit=limit)
    theories = search_theories_text(name, limit=limit)
    episodes = episodes_for_location_name(name)
    return {
        "events": events,
        "theories": theories,
        "episodes": episodes,
    }


# ---------- theories mentioning X ----------

def theories_mentioning_term(term: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Alias for search_theories_text; for clarity in code using 'term'.
    """
    return search_theories_text(term, limit=limit)
