import json
from sqlalchemy import text
from .config import EVENTS_PATH
from .db import get_session
from .logging_utils import log_info
from .id_maps import EPISODE_MAP


def ingest_events():
    session = get_session()
    processed = inserted = updated = skipped = 0
    with open(EVENTS_PATH) as f:
        data = json.load(f)
        for event in data:
            season = event.get('season')
            episode = event.get('episode')
            timestamp = event.get('timestamp')
            event_type = event.get('event_type')
            text_ = event.get('text')
            confidence = event.get('confidence')
            source_refs = event.get('source_refs')
            from .id_maps import get_or_create_episode
            episode_id = get_or_create_episode(season, episode, session)
            row = session.execute(
                text("SELECT id FROM events WHERE episode_id = :episode_id AND timestamp = :timestamp AND event_type = :event_type AND text = :text_"),
                {"episode_id": episode_id, "timestamp": timestamp, "event_type": event_type, "text_": text_}
            ).fetchone()
            if row:
                session.execute(
                    text("UPDATE events SET confidence=:confidence, source_refs=:source_refs WHERE id=:id"),
                    {"confidence": confidence, "source_refs": source_refs, "id": row[0]}
                )
                updated += 1
            else:
                session.execute(
                    text("INSERT INTO events (episode_id, timestamp, event_type, text, confidence, source_refs) VALUES (:episode_id, :timestamp, :event_type, :text_, :confidence, :source_refs)"),
                    {"episode_id": episode_id, "timestamp": timestamp, "event_type": event_type, "text_": text_, "confidence": confidence, "source_refs": source_refs}
                )
                inserted += 1
            processed += 1
    session.commit()
    log_info('ingest_events', processed=processed, inserted=inserted, updated=updated, skipped=skipped)
    session.close()
