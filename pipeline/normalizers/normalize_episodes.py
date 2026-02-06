#!/usr/bin/env python3
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FACTS_PATH = ROOT / "data_extracted" / "facts" / "episodes.jsonl"
CSV_PATH = ROOT / "data_canonical" / "episodes.csv"

CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

FIELDS = [
    "season",
    "episode",
    "title",
    "air_date",
    "summary",
    "runtime",
    "tmdb_episode_id",
    "tmdb_show_id",
    "confidence",
    "source_refs",
]


def load_existing():
    """Load existing canonical CSV so we can merge updates."""
    rows = {}
    if CSV_PATH.exists():
        with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                # Ensure missing fields are initialized
                for field in FIELDS:
                    if field not in r:
                        r[field] = ""
                key = (int(r["season"]), int(r["episode"]))
                rows[key] = r
    return rows


def merge(existing, fact):
    """Merge a single episode fact into the canonical dataset."""
    season = fact.get("season")
    episode = fact.get("episode")

    if season is None or episode is None:
        return

    key = (int(season), int(episode))

    # Initialize row with all fields
    row = existing.get(key, {k: "" for k in FIELDS})

    # Basic fields
    row["season"] = season
    row["episode"] = episode
    row["title"] = fact.get("title") or row["title"]
    row["air_date"] = fact.get("air_date") or row["air_date"]
    row["summary"] = fact.get("summary") or row["summary"]
    row["runtime"] = fact.get("runtime") or row["runtime"]
    row["tmdb_episode_id"] = fact.get("tmdb_episode_id") or row["tmdb_episode_id"]
    row["tmdb_show_id"] = fact.get("tmdb_show_id") or row["tmdb_show_id"]

    # Confidence merging (safe)
    new_conf = float(fact.get("confidence", 0) or 0)
    old_conf = float(row.get("confidence", 0) or 0)
    if new_conf > old_conf:
        row["confidence"] = new_conf

    # Source refs merging (safe)
    src = fact.get("source", {})
    ref = src.get("season_file")

    if ref:
        existing_refs = row.get("source_refs", "") or ""
        if existing_refs:
            # Avoid duplicates
            parts = existing_refs.split(";")
            if ref not in parts:
                row["source_refs"] = existing_refs + ";" + ref
        else:
            row["source_refs"] = ref

    existing[key] = row


def main():
    existing = load_existing()

    if FACTS_PATH.exists():
        with FACTS_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                fact = json.loads(line)
                merge(existing, fact)

    # Write canonical CSV
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()

        for key in sorted(existing.keys()):
            writer.writerow(existing[key])

    print(f"[normalize_episodes] Wrote {CSV_PATH}")


if __name__ == "__main__":
    main()