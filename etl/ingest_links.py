from sqlalchemy import text
from .db import get_session
from .logging_utils import log_info
from .id_maps import EPISODE_MAP, LOCATION_MAP, ARTIFACT_MAP, PEOPLE_MAP


def build_event_people_links():
    session = get_session()
    processed = inserted = skipped = 0
    # Example: For each event, link to people by name (if available)
    events = session.execute(text("SELECT id, episode_id, text FROM events")).fetchall()
    for event in events:
        event_id = event[0]
        # Dummy: extract people names from text (placeholder, real logic should parse people mentions)
        # For demo, skip if no people
        continue  # TODO: Implement real extraction logic
    log_info('build_event_people_links', processed=processed, inserted=inserted, skipped=skipped)
    session.close()


def build_event_location_links():
    session = get_session()
    processed = inserted = skipped = 0
    # Example: For each event, link to locations by name/id (if available)
    events = session.execute(text("SELECT id, episode_id, text FROM events")).fetchall()
    for event in events:
        event_id = event[0]
        # Dummy: extract location names from text (placeholder, real logic should parse location mentions)
        continue  # TODO: Implement real extraction logic
    log_info('build_event_location_links', processed=processed, inserted=inserted, skipped=skipped)
    session.close()


def build_artifact_episode_links():
    session = get_session()
    processed = inserted = skipped = 0
    # For each artifact, link to episode by season/episode
    artifacts = session.execute(text("SELECT id, season, episode FROM artifacts")).fetchall()
    for artifact in artifacts:
        artifact_id = artifact[0]
        season = artifact[1]
        episode = artifact[2]
        if season is not None and episode is not None:
            from .id_maps import get_or_create_episode
            episode_id = get_or_create_episode(season, episode, session)
            # Check if link exists
            row = session.execute(
                text("SELECT 1 FROM artifact_episodes WHERE artifact_id = :artifact_id AND episode_id = :episode_id"),
                {"artifact_id": artifact_id, "episode_id": episode_id}
            ).fetchone()
            if not row:
                session.execute(
                    text("INSERT INTO artifact_episodes (artifact_id, episode_id) VALUES (:artifact_id, :episode_id)"),
                    {"artifact_id": artifact_id, "episode_id": episode_id}
                )
                inserted += 1
            else:
                skipped += 1
            processed += 1
    session.commit()
    log_info('build_artifact_episode_links', processed=processed, inserted=inserted, skipped=skipped)
    session.close()
