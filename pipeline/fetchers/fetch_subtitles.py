#!/usr/bin/env python3
import requests
import yaml
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "pipeline" / "config" / "sources.yaml"
TMDB_RAW = ROOT / "data_raw" / "tmdb"
OUT_DIR = ROOT / "data_raw" / "subtitles"

OUT_DIR.mkdir(parents=True, exist_ok=True)

FAIL_CACHE = OUT_DIR / "failures.json"


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def load_config():
    with CONFIG.open() as f:
        return yaml.safe_load(f)


def load_latest_tmdb_snapshot():
    snapshots = sorted(TMDB_RAW.glob("*.json"))
    if not snapshots:
        raise RuntimeError("No TMDB snapshots found in data_raw/tmdb/")
    return json.loads(snapshots[-1].read_text())


def subtitle_filename(season, episode):
    return f"s{int(season):02d}e{int(episode):02d}.en.srt"


def subtitle_path(season, episode):
    return OUT_DIR / subtitle_filename(season, episode)


def load_fail_cache():
    if FAIL_CACHE.exists():
        return json.loads(FAIL_CACHE.read_text())
    return {}


def save_fail_cache(cache):
    FAIL_CACHE.write_text(json.dumps(cache, indent=2))


# -------------------------------------------------
# OpenSubtitles API
# -------------------------------------------------

def fetch_subtitle_from_opensubtitles(api_key, user_agent, season, episode):
    url = "https://api.opensubtitles.com/api/v1/subtitles"
    headers = {
        "Api-Key": api_key,
        "User-Agent": user_agent,
        "Content-Type": "application/json",
    }

    params = {
        "query": "The Curse of Oak Island",
        "languages": "en",
        "season_number": season,
        "episode_number": episode,
    }

    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code != 200:
        print(f"OpenSubtitles API error {resp.status_code}")
        return None

    data = resp.json()
    if "data" not in data or not data["data"]:
        print(f"No subtitles found for S{season}E{episode}")
        return None

    try:
        file_id = data["data"][0]["attributes"]["files"][0]["file_id"]
    except Exception:
        print(f"No downloadable file for S{season}E{episode}")
        return None

    download_url = "https://api.opensubtitles.com/api/v1/download"
    dl_resp = requests.post(download_url, headers=headers, json={"file_id": file_id})

    if dl_resp.status_code != 200:
        print(f"Subtitle download failed for S{season}E{episode}")
        return None

    dl_data = dl_resp.json()
    subtitle_text = requests.get(dl_data["link"]).text
    return subtitle_text


# -------------------------------------------------
# Main logic
# -------------------------------------------------

def main():
    cfg = load_config()
    api_key = cfg["opensubtitles"]["api_key"]
    user_agent = cfg["opensubtitles"].get("user_agent", "Oak Island")

    tmdb = load_latest_tmdb_snapshot()
    seasons = tmdb.get("seasons", [])

    fail_cache = load_fail_cache()
    consecutive_failures = 0

    # TMDB seasons come as a LIST
    for season in seasons:
        season_number = season.get("season_number")
        if season_number is None:
            continue

        # Skip Season 0 (specials)
        if int(season_number) == 0:
            print("Skipping Season 0 (specials)")
            continue

        episodes = season.get("episodes", [])
        for ep in episodes:
            ep_num = ep.get("episode_number")
            if ep_num is None:
                continue

            key = f"s{int(season_number):02d}e{int(ep_num):02d}"
            out_path = subtitle_path(season_number, ep_num)

            # Skip known failures
            if key in fail_cache:
                print(f"Skipping {key} (known missing)")
                continue

            # Skip existing files
            if out_path.exists():
                print(f"Subtitle exists ? {out_path.name}")
                continue

            print(f"Fetching subtitles for S{season_number}E{ep_num}…")

            text = fetch_subtitle_from_opensubtitles(api_key, user_agent, season_number, ep_num)

            if not text:
                print(f"Failed to fetch {key}")
                fail_cache[key] = True
                save_fail_cache(fail_cache)

                consecutive_failures += 1
                if consecutive_failures >= 5:
                    print("Too many failures in a row — stopping early to protect API limits.")
                    save_fail_cache(fail_cache)
                    return
                continue

            # Success
            consecutive_failures = 0
            out_path.write_text(text, encoding="utf-8")
            print(f"Saved ? {out_path.name}")

    print("Subtitle fetch complete.")
    save_fail_cache(fail_cache)


if __name__ == "__main__":
    main()