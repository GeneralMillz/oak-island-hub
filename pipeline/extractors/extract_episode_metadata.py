#!/usr/bin/env python3
import json
import csv
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]

TMDB_DIR = ROOT / "data_raw" / "tmdb"
FACTS_DIR = ROOT / "data_extracted" / "facts"
CANON_DIR = ROOT / "data_canonical"

FACTS_DIR.mkdir(parents=True, exist_ok=True)
CANON_DIR.mkdir(parents=True, exist_ok=True)

FACTS_OUT = FACTS_DIR / "episodes.jsonl"
CSV_OUT = CANON_DIR / "episodes.csv"


def load_show():
    show_path = TMDB_DIR / "show.json"
    if not show_path.exists():
        raise RuntimeError("Missing show.json — run fetch_tmdb.py first")
    return json.loads(show_path.read_text())


def load_seasons():
    seasons = []
    for path in sorted(TMDB_DIR.glob("season_*.json")):
        seasons.append(json.loads(path.read_text()))
    return seasons


def normalize_episode(season_number, ep):
    """Convert TMDB episode JSON into a canonical fact dict."""
    ep_num = ep.get("episode_number")
    air_date = ep.get("air_date")

    # Skip phantom episodes
    if ep_num is None or not air_date:
        return None

    return {
        "season": int(season_number),
        "episode": int(ep_num),
        "title": ep.get("name") or "",
        "air_date": air_date,
        "summary": ep.get("overview") or "",
        "runtime": ep.get("runtime") or None,
        "tmdb_episode_id": ep.get("id"),
        "tmdb_show_id": 60603,
        "confidence": 1.0,
        "source": {
            "type": "tmdb",
            "season_file": f"season_{int(season_number):02d}.json"
        }
    }


def write_facts(facts):
    with FACTS_OUT.open("w", encoding="utf-8") as f:
        for fact in facts:
            f.write(json.dumps(fact) + "\n")


def write_csv(facts):
    fields = [
        "season",
        "episode",
        "title",
        "air_date",
        "summary",
        "runtime",
        "tmdb_episode_id",
        "tmdb_show_id",
    ]

    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for fact in facts:
            row = {k: fact.get(k) for k in fields}
            writer.writerow(row)


def main():
    show = load_show()
    seasons = load_seasons()

    all_facts = []

    for season in seasons:
        season_number = season.get("season_number")
        if season_number is None:
            continue

        # Skip Season 0 (specials)
        if int(season_number) == 0:
            continue

        episodes = season.get("episodes", [])
        for ep in episodes:
            fact = normalize_episode(season_number, ep)
            if fact:
                all_facts.append(fact)

    # Sort deterministically
    all_facts.sort(key=lambda x: (x["season"], x["episode"]))

    write_facts(all_facts)
    write_csv(all_facts)

    print(f"Wrote {len(all_facts)} episode facts → {FACTS_OUT}")
    print(f"Wrote canonical CSV → {CSV_OUT}")


if __name__ == "__main__":
    main()
