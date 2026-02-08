import json
from typing import Any
from sqlalchemy import text
from .config import EPISODES_PATH, LOCATIONS_PATH, ARTIFACTS_PATH, BOREHOLES_PATH, INTERVALS_PATH, MEASUREMENTS_PATH, THEORIES_PATH, PEOPLE_PATH
from .db import get_session
from .logging_utils import log_info
from .id_maps import EPISODE_MAP, LOCATION_MAP, ARTIFACT_MAP, BOREHOLE_MAP, PEOPLE_MAP


def ingest_episodes():
    session = get_session()
    processed = inserted = updated = skipped = 0
    with open(EPISODES_PATH) as f:
        data = json.load(f)
        for ep in data.get('episodes', []):
            season = ep.get('season')
            episode = ep.get('episode')
            title = ep.get('title') or f"Unknown S{season}E{episode}"
            air_date = ep.get('airDate')
            summary = ep.get('shortSummary')
            # Upsert by (season, episode)
            row = session.execute(
                text("SELECT id FROM episodes WHERE season = :season AND episode = :episode"),
                {"season": season, "episode": episode}
            ).fetchone()
            if row:
                # Optionally update title/summary if changed
                session.execute(
                    text("UPDATE episodes SET title=:title, air_date=:air_date, summary=:summary WHERE id=:id"),
                    {"title": title, "air_date": air_date, "summary": summary, "id": row[0]}
                )
                updated += 1
            else:
                session.execute(
                    text("INSERT INTO episodes (season, episode, title, air_date, summary) VALUES (:season, :episode, :title, :air_date, :summary)"),
                    {"season": season, "episode": episode, "title": title, "air_date": air_date, "summary": summary}
                )
                inserted += 1
            processed += 1
    session.commit()
    log_info('ingest_episodes', processed=processed, inserted=inserted, updated=updated, skipped=skipped)
    session.close()


def ingest_locations():
    session = get_session()
    processed = inserted = updated = skipped = 0
    with open(LOCATIONS_PATH) as f:
        data = json.load(f)
        for loc in data:
            legacy_id = loc.get('id')
            name = loc.get('name')
            type_ = loc.get('type')
            lat = loc.get('lat')
            lng = loc.get('lng')
            desc = loc.get('description')
            first_year = loc.get('firstDocumentedYear')
            row = session.execute(
                text("SELECT id FROM locations WHERE location_id = :legacy_id"),
                {"legacy_id": legacy_id}
            ).fetchone()
            if row:
                session.execute(
                    text("UPDATE locations SET name=:name, type=:type, lat=:lat, lng=:lng, description=:desc, first_documented_year=:first_year WHERE id=:id"),
                    {"name": name, "type": type_, "lat": lat, "lng": lng, "desc": desc, "first_year": first_year, "id": row[0]}
                )
                updated += 1
            else:
                session.execute(
                    text("INSERT INTO locations (location_id, name, type, lat, lng, description, first_documented_year) VALUES (:legacy_id, :name, :type, :lat, :lng, :desc, :first_year)"),
                    {"legacy_id": legacy_id, "name": name, "type": type_, "lat": lat, "lng": lng, "desc": desc, "first_year": first_year}
                )
                inserted += 1
            processed += 1
    session.commit()
    log_info('ingest_locations', processed=processed, inserted=inserted, updated=updated, skipped=skipped)
    session.close()


def ingest_artifacts():
    session = get_session()
    processed = inserted = updated = skipped = 0
    with open(ARTIFACTS_PATH) as f:
        data = json.load(f)
        for art in data:
            legacy_id = art.get('id')
            name = art.get('name')
            type_ = art.get('type')
            location = art.get('location')
            season = art.get('season')
            episode = art.get('episode')
            confidence = art.get('confidence')
            desc = art.get('description') if 'description' in art else None
            location_id = None
            if location:
                # Try to resolve location FK
                from .id_maps import get_or_create_location
                location_id = get_or_create_location(location, session)
            row = session.execute(
                text("SELECT id FROM artifacts WHERE artifact_id = :legacy_id"),
                {"legacy_id": legacy_id}
            ).fetchone()
            if row:
                session.execute(
                    text("UPDATE artifacts SET name=:name, type=:type, location_id=:location_id, season=:season, episode=:episode, confidence=:confidence, description=:desc WHERE id=:id"),
                    {"name": name, "type": type_, "location_id": location_id, "season": season, "episode": episode, "confidence": confidence, "desc": desc, "id": row[0]}
                )
                updated += 1
            else:
                session.execute(
                    text("INSERT INTO artifacts (artifact_id, name, type, location_id, season, episode, confidence, description) VALUES (:legacy_id, :name, :type, :location_id, :season, :episode, :confidence, :desc)"),
                    {"legacy_id": legacy_id, "name": name, "type": type_, "location_id": location_id, "season": season, "episode": episode, "confidence": confidence, "desc": desc}
                )
                inserted += 1
            processed += 1
    session.commit()
    log_info('ingest_artifacts', processed=processed, inserted=inserted, updated=updated, skipped=skipped)
    session.close()


def ingest_boreholes():
    session = get_session()
    processed = inserted = updated = skipped = 0
    with open(BOREHOLES_PATH) as f:
        data = json.load(f)
        for bh in data.get('boreholes', []):
            legacy_id = bh.get('id')
            name = bh.get('name')
            location_id = bh.get('location_id')
            lat = bh.get('lat')
            lng = bh.get('lng')
            collar_elev = bh.get('collarElevation_m')
            max_depth = bh.get('maxDepth_m')
            drill_method = bh.get('drillMethod')
            era = bh.get('era')
            source_priority = bh.get('sourcePriority')
            source_refs = bh.get('sourceRefs')
            # Try to resolve location FK if present
            resolved_location_id = None
            if location_id:
                from .id_maps import get_or_create_location
                resolved_location_id = get_or_create_location(location_id, session)
            row = session.execute(
                text("SELECT id FROM boreholes WHERE borehole_id = :legacy_id"),
                {"legacy_id": legacy_id}
            ).fetchone()
            if row:
                session.execute(
                    text("UPDATE boreholes SET name=:name, location_id=:location_id, lat=:lat, lng=:lng, collar_elevation_m=:collar_elev, max_depth_m=:max_depth, drill_method=:drill_method, era=:era, source_priority=:source_priority, source_refs=:source_refs WHERE id=:id"),
                    {"name": name, "location_id": resolved_location_id, "lat": lat, "lng": lng, "collar_elev": collar_elev, "max_depth": max_depth, "drill_method": drill_method, "era": era, "source_priority": source_priority, "source_refs": source_refs, "id": row[0]}
                )
                updated += 1
            else:
                session.execute(
                    text("INSERT INTO boreholes (borehole_id, name, location_id, lat, lng, collar_elevation_m, max_depth_m, drill_method, era, source_priority, source_refs) VALUES (:legacy_id, :name, :location_id, :lat, :lng, :collar_elev, :max_depth, :drill_method, :era, :source_priority, :source_refs)"),
                    {"legacy_id": legacy_id, "name": name, "location_id": resolved_location_id, "lat": lat, "lng": lng, "collar_elev": collar_elev, "max_depth": max_depth, "drill_method": drill_method, "era": era, "source_priority": source_priority, "source_refs": source_refs}
                )
                inserted += 1
            processed += 1
    session.commit()
    log_info('ingest_boreholes', processed=processed, inserted=inserted, updated=updated, skipped=skipped)
    session.close()


def ingest_borehole_intervals():
    session = get_session()
    processed = inserted = updated = skipped = 0
    with open(INTERVALS_PATH) as f:
        for line in f:
            interval = json.loads(line)
            legacy_id = interval.get('id')
            borehole_legacy_id = interval.get('borehole_id')
            depth_from = interval.get('depthFrom_m')
            depth_to = interval.get('depthTo_m')
            material = interval.get('material')
            water_intrusion = interval.get('waterIntrusion')
            sample_taken = interval.get('sampleTaken')
            sample_type = interval.get('sampleType')
            lab_result_ref = interval.get('labResultRef')
            confidence = interval.get('confidence')
            source_refs = interval.get('sourceRefs')
            from .id_maps import get_or_create_borehole
            borehole_id = get_or_create_borehole(borehole_legacy_id, session)
            row = session.execute(
                text("SELECT id FROM borehole_intervals WHERE borehole_id = :borehole_id AND depth_from_m = :depth_from AND depth_to_m = :depth_to"),
                {"borehole_id": borehole_id, "depth_from": depth_from, "depth_to": depth_to}
            ).fetchone()
            if row:
                session.execute(
                    text("UPDATE borehole_intervals SET material=:material, water_intrusion=:water_intrusion, sample_taken=:sample_taken, sample_type=:sample_type, lab_result_ref=:lab_result_ref, confidence=:confidence, source_refs=:source_refs WHERE id=:id"),
                    {"material": material, "water_intrusion": water_intrusion, "sample_taken": sample_taken, "sample_type": sample_type, "lab_result_ref": lab_result_ref, "confidence": confidence, "source_refs": source_refs, "id": row[0]}
                )
                updated += 1
            else:
                session.execute(
                    text("INSERT INTO borehole_intervals (borehole_id, depth_from_m, depth_to_m, material, water_intrusion, sample_taken, sample_type, lab_result_ref, confidence, source_refs) VALUES (:borehole_id, :depth_from, :depth_to, :material, :water_intrusion, :sample_taken, :sample_type, :lab_result_ref, :confidence, :source_refs)"),
                    {"borehole_id": borehole_id, "depth_from": depth_from, "depth_to": depth_to, "material": material, "water_intrusion": water_intrusion, "sample_taken": sample_taken, "sample_type": sample_type, "lab_result_ref": lab_result_ref, "confidence": confidence, "source_refs": source_refs}
                )
                inserted += 1
            processed += 1
    session.commit()
    log_info('ingest_borehole_intervals', processed=processed, inserted=inserted, updated=updated, skipped=skipped)
    session.close()


def ingest_measurements():
    session = get_session()
    processed = inserted = updated = skipped = 0
    with open(MEASUREMENTS_PATH) as f:
        data = json.load(f)
        for m in data:
            season = m.get('season')
            episode = m.get('episode')
            timestamp = m.get('timestamp')
            measurement_type = m.get('measurement_type')
            value = m.get('value')
            unit = m.get('unit')
            direction = m.get('direction')
            context = m.get('context')
            confidence = m.get('confidence')
            source_refs = m.get('source_refs')
            from .id_maps import get_or_create_episode
            episode_id = get_or_create_episode(season, episode, session)
            row = session.execute(
                text("SELECT id FROM measurements WHERE episode_id = :episode_id AND timestamp = :timestamp AND measurement_type = :measurement_type AND value = :value"),
                {"episode_id": episode_id, "timestamp": timestamp, "measurement_type": measurement_type, "value": value}
            ).fetchone()
            if row:
                session.execute(
                    text("UPDATE measurements SET unit=:unit, direction=:direction, context=:context, confidence=:confidence, source_refs=:source_refs WHERE id=:id"),
                    {"unit": unit, "direction": direction, "context": context, "confidence": confidence, "source_refs": source_refs, "id": row[0]}
                )
                updated += 1
            else:
                session.execute(
                    text("INSERT INTO measurements (episode_id, timestamp, measurement_type, value, unit, direction, context, confidence, source_refs) VALUES (:episode_id, :timestamp, :measurement_type, :value, :unit, :direction, :context, :confidence, :source_refs)"),
                    {"episode_id": episode_id, "timestamp": timestamp, "measurement_type": measurement_type, "value": value, "unit": unit, "direction": direction, "context": context, "confidence": confidence, "source_refs": source_refs}
                )
                inserted += 1
            processed += 1
    session.commit()
    log_info('ingest_measurements', processed=processed, inserted=inserted, updated=updated, skipped=skipped)
    session.close()


def ingest_theories():
    session = get_session()
    processed = inserted = updated = skipped = 0
    with open(THEORIES_PATH) as f:
        data = json.load(f)
        for t in data:
            season = t.get('season')
            episode = t.get('episode')
            timestamp = t.get('timestamp')
            theory = t.get('theory')
            text_ = t.get('text')
            confidence = t.get('confidence')
            source_refs = t.get('source_refs')
            from .id_maps import get_or_create_episode
            episode_id = get_or_create_episode(season, episode, session)
            row = session.execute(
                text("SELECT id FROM theories WHERE episode_id = :episode_id AND timestamp = :timestamp AND theory = :theory AND text = :text_"),
                {"episode_id": episode_id, "timestamp": timestamp, "theory": theory, "text_": text_}
            ).fetchone()
            if row:
                session.execute(
                    text("UPDATE theories SET confidence=:confidence, source_refs=:source_refs WHERE id=:id"),
                    {"confidence": confidence, "source_refs": source_refs, "id": row[0]}
                )
                updated += 1
            else:
                session.execute(
                    text("INSERT INTO theories (episode_id, timestamp, theory, text, confidence, source_refs) VALUES (:episode_id, :timestamp, :theory, :text_, :confidence, :source_refs)"),
                    {"episode_id": episode_id, "timestamp": timestamp, "theory": theory, "text_": text_, "confidence": confidence, "source_refs": source_refs}
                )
                inserted += 1
            processed += 1
    session.commit()
    log_info('ingest_theories', processed=processed, inserted=inserted, updated=updated, skipped=skipped)
    session.close()


def ingest_people():
    session = get_session()
    processed = inserted = updated = skipped = 0
    with open(PEOPLE_PATH) as f:
        data = json.load(f)
        for p in data:
            name = p.get('person') or p.get('name')
            role = p.get('role')
            person_id = p.get('person_id')
            row = session.execute(
                text("SELECT id FROM people WHERE name = :name"),
                {"name": name}
            ).fetchone()
            if row:
                session.execute(
                    text("UPDATE people SET role=:role WHERE id=:id"),
                    {"role": role, "id": row[0]}
                )
                updated += 1
            else:
                session.execute(
                    text("INSERT INTO people (name, role, person_id) VALUES (:name, :role, :person_id)"),
                    {"name": name, "role": role, "person_id": person_id}
                )
                inserted += 1
            processed += 1
    session.commit()
    log_info('ingest_people', processed=processed, inserted=inserted, updated=updated, skipped=skipped)
    session.close()
