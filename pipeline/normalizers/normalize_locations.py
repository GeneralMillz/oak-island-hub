#!/usr/bin/env python3
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FACTS = ROOT / "data_extracted" / "facts" / "locations.jsonl"
CSV_PATH = ROOT / "data_canonical" / "locations.csv"

FIELDS = [
    "location_id",
    "name",
    "type",
    "lat",
    "lng",
    "elevation_m",
    "first_documented_year",
    "era_primary",
    "related_seasons",
    "source_priority",
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
                rows[r["location_id"]] = r
    return rows


def normalize_related_seasons(value):
    """Ensure related_seasons is stored as a semicolon-separated string."""
    if isinstance(value, list):
        return ";".join(str(x) for x in value)
    if value is None:
        return ""
    return str(value)


def main():
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = load_existing()

    if FACTS.exists():
        with FACTS.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                fact = json.loads(line)
                if fact.get("fact_type") != "location":
                    continue

                loc_id = fact["location_id"]

                # Initialize row with all fields
                row = existing.get(loc_id, {k: "" for k in FIELDS})

                # Basic fields
                row["location_id"] = loc_id
                row["name"] = fact.get("name", row["name"])
                row["type"] = fact.get("type", row["type"])

                # Coordinates (always stored as strings in CSV)
                row["lat"] = str(fact.get("lat", row.get("lat", "")) or "")
                row["lng"] = str(fact.get("lng", row.get("lng", "")) or "")

                # Elevation + year
                row["elevation_m"] = str(fact.get("elevation_m", row.get("elevation_m", "")) or "")
                row["first_documented_year"] = str(
                    fact.get("first_documented_year", row.get("first_documented_year", "")) or ""
                )

                # Era
                row["era_primary"] = fact.get("era_primary", row.get("era_primary", "")) or ""

                # Related seasons (list ? string)
                row["related_seasons"] = normalize_related_seasons(
                    fact.get("related_seasons", row.get("related_seasons", ""))
                )

                # Source priority
                row["source_priority"] = fact.get("source_priority", row.get("source_priority", "")) or ""

                # Source refs
                row["source_refs"] = fact.get("source_refs", row.get("source_refs", "")) or ""

                existing[loc_id] = row

    # Write canonical CSV
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()

        for loc_id in sorted(existing.keys()):
            writer.writerow(existing[loc_id])

    print(f"[normalize_locations] Wrote {CSV_PATH}")


if __name__ == "__main__":
    main()