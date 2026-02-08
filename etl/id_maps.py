

from typing import Dict, Tuple, Optional
from sqlalchemy import text
from sqlalchemy.engine import Connection
from .logging_utils import log_info

# In-memory ID maps
EPISODE_MAP: Dict[Tuple[int, int], int] = {}
LOCATION_MAP: Dict[str, int] = {}
ARTIFACT_MAP: Dict[str, int] = {}
BOREHOLE_MAP: Dict[str, int] = {}
PEOPLE_MAP: Dict[str, int] = {}

def get_or_create_episode(season: int, episode: int, session) -> int:
    key = (season, episode)
    if key in EPISODE_MAP:
        eid = EPISODE_MAP[key]
        log_info("episode_lookup", season=season, episode=episode, id=eid)
        return eid
    row = session.execute(
        text("SELECT id FROM episodes WHERE season = :season AND episode = :episode"),
        {"season": season, "episode": episode}
    ).fetchone()
    if row:
        eid = row[0]
        EPISODE_MAP[key] = eid
        log_info("episode_lookup", season=season, episode=episode, id=eid)
        return eid
    log_info("episode_lookup_miss", season=season, episode=episode)
    session.execute(
        text("INSERT INTO episodes (season, episode, title) VALUES (:season, :episode, :title) ON CONFLICT(season, episode) DO NOTHING"),
        {"season": season, "episode": episode, "title": f"Unknown S{season}E{episode}"}
    )
    session.commit()
    row = session.execute(
        text("SELECT id FROM episodes WHERE season = :season AND episode = :episode"),
        {"season": season, "episode": episode}
    ).fetchone()
    eid = row[0]
    EPISODE_MAP[key] = eid
    log_info("episode_insert", season=season, episode=episode, id=eid)
    return eid

def get_or_create_location(legacy_id: str, session) -> int:
    if legacy_id in LOCATION_MAP:
        lid = LOCATION_MAP[legacy_id]
        log_info("location_lookup", legacy_id=legacy_id, id=lid)
        return lid
    row = session.execute(
        text("SELECT id FROM locations WHERE location_id = :legacy_id"),
        {"legacy_id": legacy_id}
    ).fetchone()
    if row:
        lid = row[0]
        LOCATION_MAP[legacy_id] = lid
        log_info("location_lookup", legacy_id=legacy_id, id=lid)
        return lid
    log_info("location_lookup_miss", legacy_id=legacy_id)
    session.execute(
        text("INSERT INTO locations (location_id, name, type) VALUES (:legacy_id, :name, :type) ON CONFLICT(location_id) DO NOTHING"),
        {"legacy_id": legacy_id, "name": legacy_id, "type": "unknown"}
    )
    session.commit()
    row = session.execute(
        text("SELECT id FROM locations WHERE location_id = :legacy_id"),
        {"legacy_id": legacy_id}
    ).fetchone()
    lid = row[0]
    LOCATION_MAP[legacy_id] = lid
    log_info("location_insert", legacy_id=legacy_id, id=lid)
    return lid

def get_or_create_artifact(legacy_id: str, session) -> int:
    if legacy_id in ARTIFACT_MAP:
        aid = ARTIFACT_MAP[legacy_id]
        log_info("artifact_lookup", legacy_id=legacy_id, id=aid)
        return aid
    row = session.execute(
        text("SELECT id FROM artifacts WHERE artifact_id = :legacy_id"),
        {"legacy_id": legacy_id}
    ).fetchone()
    if row:
        aid = row[0]
        ARTIFACT_MAP[legacy_id] = aid
        log_info("artifact_lookup", legacy_id=legacy_id, id=aid)
        return aid
    log_info("artifact_lookup_miss", legacy_id=legacy_id)
    session.execute(
        text("INSERT INTO artifacts (artifact_id, name) VALUES (:legacy_id, :name) ON CONFLICT(artifact_id) DO NOTHING"),
        {"legacy_id": legacy_id, "name": legacy_id}
    )
    session.commit()
    row = session.execute(
        text("SELECT id FROM artifacts WHERE artifact_id = :legacy_id"),
        {"legacy_id": legacy_id}
    ).fetchone()
    aid = row[0]
    ARTIFACT_MAP[legacy_id] = aid
    log_info("artifact_insert", legacy_id=legacy_id, id=aid)
    return aid

def get_or_create_borehole(legacy_id: str, session) -> int:
    if legacy_id in BOREHOLE_MAP:
        bid = BOREHOLE_MAP[legacy_id]
        log_info("borehole_lookup", legacy_id=legacy_id, id=bid)
        return bid
    row = session.execute(
        text("SELECT id FROM boreholes WHERE borehole_id = :legacy_id"),
        {"legacy_id": legacy_id}
    ).fetchone()
    if row:
        bid = row[0]
        BOREHOLE_MAP[legacy_id] = bid
        log_info("borehole_lookup", legacy_id=legacy_id, id=bid)
        return bid
    log_info("borehole_lookup_miss", legacy_id=legacy_id)
    session.execute(
        text("INSERT INTO boreholes (borehole_id, name) VALUES (:legacy_id, :name) ON CONFLICT(borehole_id) DO NOTHING"),
        {"legacy_id": legacy_id, "name": legacy_id}
    )
    session.commit()
    row = session.execute(
        text("SELECT id FROM boreholes WHERE borehole_id = :legacy_id"),
        {"legacy_id": legacy_id}
    ).fetchone()
    bid = row[0]
    BOREHOLE_MAP[legacy_id] = bid
    log_info("borehole_insert", legacy_id=legacy_id, id=bid)
    return bid

def get_or_create_person(name: str, session) -> int:
    if name in PEOPLE_MAP:
        pid = PEOPLE_MAP[name]
        log_info("person_lookup", name=name, id=pid)
        return pid
    row = session.execute(
        text("SELECT id FROM people WHERE name = :name"),
        {"name": name}
    ).fetchone()
    if row:
        pid = row[0]
        PEOPLE_MAP[name] = pid
        log_info("person_lookup", name=name, id=pid)
        return pid
    log_info("person_lookup_miss", name=name)
    session.execute(
        text("INSERT INTO people (name) VALUES (:name) ON CONFLICT(name) DO NOTHING"),
        {"name": name}
    )
    session.commit()
    row = session.execute(
        text("SELECT id FROM people WHERE name = :name"),
        {"name": name}
    ).fetchone()
    pid = row[0]
    PEOPLE_MAP[name] = pid
    log_info("person_insert", name=name, id=pid)
    return pid
