#!/usr/bin/env python3
import requests
import yaml
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "pipeline" / "config" / "sources.yaml"
OUT_DIR = ROOT / "data_raw" / "tmdb"

OUT_DIR.mkdir(parents=True, exist_ok=True)

TMDB_SHOW_ID = 60603  # The Curse of Oak Island (correct ID)
FAIL_CACHE = OUT_DIR / "failures.json"


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def load_config():
    with CONFIG.open() as f:
        return yaml.safe_load(f)


def load_fail_cache():
    if FAIL_CACHE.exists():
        return json.loads(FAIL_CACHE.read_text())
    return {}


def save_fail_cache(cache):
    FAIL_CACHE.write_text(json.dumps(cache, indent=2))


def season_snapshot_path(season_number):
    return OUT_DIR / f"season_{int(season_number):02d}.json"


# -------------------------------------------------
# TMDB API
# -------------------------------------------------

def fetch_tmdb_show(api_key):
    base_url = "https://api.themoviedb.org/3"
    headers = {"Authorization": f"Bearer {api_key}"}

    url = f"{base_url}/tv/{TMDB_SHOW_ID}"
    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        raise RuntimeError(f"TMDB show fetch failed: {resp.status_code}")

    return resp.json()


def fetch_tmdb_season(api_key, season_number):
    base_url = "https://api.themoviedb.org/3"
    headers = {"Authorization": f"Bearer {api_key}"}

    url = f"{base_url}/tv/{TMDB_SHOW_ID}/season/{season_number}"
    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        print(f"TMDB season {season_number} error {resp.status_code}")
        return None

    return resp.json()


# -------------------------------------------------
# Main logic
# -------------------------------------------------

def main():
    cfg = load_config()
    api_key = cfg["tmdb"]["api_key"]

    fail_cache = load_fail_cache()
    consecutive_failures = 0

    # Fetch show metadata
    print("Fetching show metadata…")
    show_data = fetch_tmdb_show(api_key)
    seasons = show_data.get("seasons", [])

    # Save show metadata separately
    show_path = OUT_DIR / "show.json"
    show_path.write_text(json.dumps(show_data, indent=2))
    print(f"Saved → {show_path.name}")

    # Fetch each season
    for season in seasons:
        season_number = season.get("season_number")
        if season_number is None:
            continue

        # Skip Season 0 (specials) if desired
        if int(season_number) == 0:
            print("Skipping Season 0 (specials)")
            continue

        key = f"season_{int(season_number):02d}"

        # Skip known failures
        if key in fail_cache:
            print(f"Skipping {key} (known missing)")
            continue

        out_path = season_snapshot_path(season_number)

        # Skip if already downloaded
        if out_path.exists():
            print(f"Season exists → {out_path.name}")
            continue

        print(f"Fetching Season {season_number}…")

        season_data = fetch_tmdb_season(api_key, season_number)

        if not season_data:
            print(f"Failed to fetch {key}")
            fail_cache[key] = True
            save_fail_cache(fail_cache)

            consecutive_failures += 1
            if consecutive_failures >= 3:
                print("Too many failures — stopping early to protect API limits.")
                return
            continue

        # Success
        consecutive_failures = 0
        out_path.write_text(json.dumps(season_data, indent=2))
        print(f"Saved → {out_path.name}")

    print("TMDB fetch complete.")
    save_fail_cache(fail_cache)


if __name__ == "__main__":
    main()
