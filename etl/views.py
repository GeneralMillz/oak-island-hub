from sqlalchemy import text
from .db import get_session
from .logging_utils import log_info


def refresh_materialized_views():
    session = get_session()
    # SQLite: drop and recreate tables for materialized views
    # episodes_list
    session.execute(text("DROP TABLE IF EXISTS episodes_list"))
    session.execute(text("CREATE TABLE episodes_list AS SELECT id, season, episode, title, air_date FROM episodes"))
    # locations_min
    session.execute(text("DROP TABLE IF EXISTS locations_min"))
    session.execute(text("CREATE TABLE locations_min AS SELECT id, name, type, lat, lng FROM locations"))
    # theories_summary
    session.execute(text("DROP TABLE IF EXISTS theories_summary"))
    session.execute(text("CREATE TABLE theories_summary AS SELECT theory, COUNT(*) as count, MIN(timestamp) as first_mention, MAX(timestamp) as last_mention FROM theories GROUP BY theory"))
    # people_summary
    session.execute(text("DROP TABLE IF EXISTS people_summary"))
    session.execute(text("CREATE TABLE people_summary AS SELECT name, COUNT(*) as mention_count FROM people GROUP BY name"))
    # artifacts_summary
    session.execute(text("DROP TABLE IF EXISTS artifacts_summary"))
    session.execute(text("CREATE TABLE artifacts_summary AS SELECT a.id, a.name, a.type, l.name as location, a.season, a.episode, a.confidence FROM artifacts a LEFT JOIN locations l ON a.location_id = l.id"))
    # boreholes_summary
    session.execute(text("DROP TABLE IF EXISTS boreholes_summary"))
    session.execute(text("CREATE TABLE boreholes_summary AS SELECT b.id, b.name, l.name as location, b.max_depth_m, b.drill_method, b.era FROM boreholes b LEFT JOIN locations l ON b.location_id = l.id"))
    # database_metadata
    session.execute(text("DROP TABLE IF EXISTS database_metadata"))
    session.execute(text("CREATE TABLE database_metadata AS SELECT (SELECT COUNT(*) FROM episodes) as episode_count, (SELECT COUNT(*) FROM events) as event_count, (SELECT COUNT(*) FROM locations) as location_count, (SELECT COUNT(*) FROM artifacts) as artifact_count, (SELECT COUNT(*) FROM boreholes) as borehole_count, (SELECT COUNT(*) FROM measurements) as measurement_count, (SELECT COUNT(*) FROM theories) as theory_count, (SELECT COUNT(*) FROM people) as people_count"))
    session.commit()
    log_info('refresh_materialized_views', status='complete')
    session.close()

# For Postgres: use REFRESH MATERIALIZED VIEW view_name; for each view.
