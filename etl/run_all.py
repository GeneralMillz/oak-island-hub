from .db import init_db
from .ingest_core import (
    ingest_episodes, ingest_locations, ingest_artifacts, ingest_boreholes,
    ingest_borehole_intervals, ingest_measurements, ingest_theories, ingest_people
)
from .ingest_events import ingest_events
from .ingest_links import (
    build_event_people_links, build_event_location_links, build_artifact_episode_links
)
from .ingest_transcripts import ingest_transcripts
from .ingest_geo import ingest_geometries, register_lidar_files
from .views import refresh_materialized_views
from .logging_utils import log_info


def main():
    log_info('etl_orchestrator_start')
    steps = [
        ("init_db", init_db),
        ("ingest_episodes", ingest_episodes),
        ("ingest_locations", ingest_locations),
        ("ingest_artifacts", ingest_artifacts),
        ("ingest_boreholes", ingest_boreholes),
        ("ingest_borehole_intervals", ingest_borehole_intervals),
        ("ingest_measurements", ingest_measurements),
        ("ingest_theories", ingest_theories),
        ("ingest_people", ingest_people),
        ("ingest_events", ingest_events),
        ("build_event_people_links", build_event_people_links),
        ("build_event_location_links", build_event_location_links),
        ("build_artifact_episode_links", build_artifact_episode_links),
        ("ingest_transcripts", ingest_transcripts),
        ("ingest_geometries", ingest_geometries),
        ("register_lidar_files", register_lidar_files),
        ("refresh_materialized_views", refresh_materialized_views),
    ]
    summary = {}
    for name, func in steps:
        try:
            log_info(f'start_{name}')
            func()
            log_info(f'end_{name}', status='success')
            summary[name] = 'success'
        except Exception as e:
            log_info(f'end_{name}', status='error', error=str(e))
            summary[name] = f'error: {e}'
    log_info('etl_orchestrator_complete', summary=summary)

if __name__ == '__main__':
    main()
