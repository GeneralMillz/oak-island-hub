#!/usr/bin/env python3
import csv
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
FACTS = ROOT / "data_extracted" / "facts" / "artifacts.jsonl"
CSV_PATH = ROOT / "data_canonical" / "artifacts.csv"

FIELDS = [
    "artifact_id",
    "location_id",
    "name",
    "category",
    "description",
    "depth_m",
    "depth_reference",
    "found_date_iso",
    "episode_season",
    "episode_number",
    "episode_title",
    "era_primary",
    "confidence_level",
    "source_refs",
]


def load_existing():
    """Load existing canonical CSV and ensure all fields exist."""
    rows = {}
    if CSV_PATH.exists():
        with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                # Ensure missing fields are initialized
                for field in FIELDS:
                    if field not in r:
                        r[field] = ""
                rows[r["artifact_id"]] = r
    return rows


def merge(existing, fact):
    """Merge a single artifact fact into the canonical dataset."""
    aid = fact["artifact_id"]
    attrs = fact.get("attributes", {})
    ep = fact.get("episode", {})
    src = fact.get("source", {})

    # Initialize row with all fields
    row = existing.get(aid, {k: "" for k in FIELDS})
    row["artifact_id"] = aid

    # Basic fields
    row["name"] = attrs.get("name", row.get("name", ""))
    row["category"] = attrs.get("category", row.get("category", ""))
    row["description"] = attrs.get("description", row.get("description", ""))

    # Depth fields
    row["depth_m"] = str(attrs.get("depth_m", row.get("depth_m", "")) or "")
    row["depth_reference"] = attrs.get("depth_reference", row.get("depth_reference", "")) or ""

    # Location linkage
    row["location_id"] = attrs.get("location_hint", row.get("location_id", "")) or ""

    # Episode linkage
    row["episode_season"] = ep.get("season", row.get("episode_season", "")) or ""
    row["episode_number"] = ep.get("episode", row.get("episode_number", "")) or ""
    row["episode_title"] = ep.get("title", row.get("episode_title", "")) or ""

    # Found date
    row["found_date_iso"] = attrs.get("found_date_iso", row.get("found_date_iso", "")) or ""

    # Era
    row["era_primary"] = attrs.get("era_primary", row.get("era_primary", "")) or ""

    # Confidence merging
    new_conf = float(fact.get("confidence", 0) or 0)
    old_conf = float(row.get("confidence_level", 0) or 0)
    if new_conf > old_conf:
        row["confidence_level"] = new_conf

    # Source refs merging
    ref = src.get("ref")
    if ref:
        existing_refs = row.get("source_refs", "") or ""
        if existing_refs:
            parts = existing_refs.split(";")
            if ref not in parts:
                row["source_refs"] = existing_refs + ";" + ref
        else:
            row["source_refs"] = ref

    existing[aid] = row


def main():
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = load_existing()

    if FACTS.exists():
        with FACTS.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                fact = json.loads(line)
                if fact.get("fact_type") != "artifact":
                    continue
                merge(existing, fact)

    # Write canonical CSV
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for aid in sorted(existing.keys()):
            writer.writerow(existing[aid])

    print(f"[normalize_artifacts] Wrote {CSV_PATH}")


if __name__ == "__main__":
    main()