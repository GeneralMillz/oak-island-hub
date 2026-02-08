import os

# Default DB URL (SQLite for dev)
DB_URL = os.getenv('OAK_ISLAND_DB_URL', 'sqlite:///oak_island_research.db')

# Data file paths (override via env if needed)
DATA_DIR = os.getenv('OAK_ISLAND_DATA_DIR', './docs/data')
FACTS_DIR = os.getenv('OAK_ISLAND_FACTS_DIR', './data_extracted/facts')
SRT_DIR = os.getenv('OAK_ISLAND_SRT_DIR', './data_raw/subtitles')

EPISODES_PATH = os.getenv('OAK_ISLAND_EPISODES_PATH', f'{DATA_DIR}/episodes.json')
EVENTS_PATH = os.getenv('OAK_ISLAND_EVENTS_PATH', f'{DATA_DIR}/events.json')
LOCATIONS_PATH = os.getenv('OAK_ISLAND_LOCATIONS_PATH', f'{DATA_DIR}/locations.json')
ARTIFACTS_PATH = os.getenv('OAK_ISLAND_ARTIFACTS_PATH', f'{DATA_DIR}/artifacts_summary.json')
BOREHOLES_PATH = os.getenv('OAK_ISLAND_BOREHOLES_PATH', f'{DATA_DIR}/boreholes.json')
INTERVALS_PATH = os.getenv('OAK_ISLAND_INTERVALS_PATH', f'{FACTS_DIR}/intervals.jsonl')
MEASUREMENTS_PATH = os.getenv('OAK_ISLAND_MEASUREMENTS_PATH', f'{DATA_DIR}/measurements.json')
THEORIES_PATH = os.getenv('OAK_ISLAND_THEORIES_PATH', f'{DATA_DIR}/theories.json')
PEOPLE_PATH = os.getenv('OAK_ISLAND_PEOPLE_PATH', f'{DATA_DIR}/people.json')

# For future extensibility
LIDAR_DIR = os.getenv('OAK_ISLAND_LIDAR_DIR', './data_raw/lidar')
GEOMETRY_DIR = os.getenv('OAK_ISLAND_GEOMETRY_DIR', './data_extracted/facts')
SCHEMA_PATH = os.getenv('OAK_ISLAND_SCHEMA_PATH', './schema.sql')
