#!/usr/bin/env python3
import csv
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]

CANON = ROOT / "data_canonical"
OUT = ROOT / "app_public" / "data"
OUT.mkdir(parents=True, exist_ok=True)

EPISODES_CSV = CANON / "episodes.csv"
LOCATIONS_CSV = CANON / "locations.csv"
BOREHOLES_CSV = CANON / "boreholes.csv"
INTERVALS_CSV = CANON / "borehole_intervals.csv"
ARTIFACTS_CSV = CANON / "artifacts.csv"  # if you have it
LOTS_CSV = CANON / "lots.csv"            # optional future support


def load_csv(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_seasons(episodes):
    seasons = {}
    for ep in episodes:
        s = int(ep["season"])
        seasons.setdefault(s, [])
        seasons[s].append({
            "season": s,
            "episode": int(ep["episode"]),
            "title": ep["title"],
            "airDate": ep["air_date"],
            "shortSummary": ep["summary"],
            "runtime": ep["runtime"],
            "tmdbId": ep["tmdb_episode_id"],
        })

    out = []
    for s in sorted(seasons.keys()):
        eps = sorted(seasons[s], key=lambda x: x["episode"])
        out.append({"season": s, "episodes": eps})
    return out


def build_locations(locations, artifacts):
    art_by_loc = {}
    for a in artifacts:
        loc = a.get("location_id")
        if not loc:
            continue
        art_by_loc.setdefault(loc, [])
        art_by_loc[loc].append({
            "artifact_id": a["artifact_id"],
            "name": a["name"],
            "category": a["category"],
            "description": a["description"],
            "depth_m": a["depth_m"],
            "found_date_iso": a["found_date_iso"],
            "episode_season": a["episode_season"],
            "episode_number": a["episode_number"],
            "episode_title": a["episode_title"],
            "era_primary": a["era_primary"],
            "confidence_level": a["confidence_level"],
            "source_refs": a["source_refs"],
        })

    out = []
    for loc in locations:
        loc_id = loc["location_id"]
        out.append({
            "id": loc_id,
            "name": loc["name"],
            "type": loc["type"],
            "lat": float(loc["lat"]) if loc["lat"] else None,
            "lng": float(loc["lng"]) if loc["lng"] else None,
            "elevation_m": loc["elevation_m"],
            "era_primary": loc["era_primary"],
            "related_seasons": loc["related_seasons"],
            "artifacts": art_by_loc.get(loc_id, []),
        })
    return out


def build_boreholes(boreholes, intervals):
    int_by_bh = {}
    for iv in intervals:
        bh = iv["borehole_id"]
        int_by_bh.setdefault(bh, [])
        int_by_bh[bh].append({
            "interval_id": iv["interval_id"],
            "depth_from_m": iv["depth_from_m"],
            "depth_to_m": iv["depth_to_m"],
            "material": iv["material"],
            "confidence_level": iv["confidence_level"],
            "source_refs": iv["source_refs"],
        })

    out = []
    for bh in boreholes:
        bh_id = bh["borehole_id"]
        out.append({
            "borehole_id": bh_id,
            "name": bh["name"],
            "location_id": bh["location_id"],
            "intervals": int_by_bh.get(bh_id, []),
        })
    return out


def main():
    episodes = load_csv(EPISODES_CSV)
    locations = load_csv(LOCATIONS_CSV)
    boreholes = load_csv(BOREHOLES_CSV)
    intervals = load_csv(INTERVALS_CSV)
    artifacts = load_csv(ARTIFACTS_CSV) if ARTIFACTS_CSV.exists() else []
    lots = load_csv(LOTS_CSV) if LOTS_CSV.exists() else []

    data = {
        "meta": {
            "islandName": "Oak Island",
            "version": "1.0.0",
            "generatedAt": datetime.utcnow().isoformat() + "Z",
        },
        "seasons": build_seasons(episodes),
        "locations": build_locations(locations, artifacts),
        "boreholes": build_boreholes(boreholes, intervals),
        "artifacts": artifacts,   # NEW
        "lots": lots              # NEW
    }

    out_path = OUT / "oak_island_data.json"
    out_path.write_text(json.dumps(data, indent=2))
    print(f"[build_map_json] Wrote {out_path}")


if __name__ == "__main__":
    main()