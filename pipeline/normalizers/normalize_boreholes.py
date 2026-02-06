#!/usr/bin/env python3
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FACTS = ROOT / "data_extracted" / "facts" / "boreholes.jsonl"
CSV_PATH = ROOT / "data_canonical" / "boreholes.csv"

FIELDS = [
    "borehole_id",
    "name",
    "location_id",
    "lat",
    "lng",
    "collar_elevation_m",
    "max_depth_m",
    "drill_method",
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
                # Ensure all fields exist
                for field in FIELDS:
                    if field not in r:
                        r[field] = ""
                rows[r["borehole_id"]] = r
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
                if fact.get("fact_type") != "borehole":
                    continue

                borehole_id = fact["borehole_id"]
                attrs = fact.get("attributes", {})

                # Initialize row with all fields
                row = existing.get(borehole_id, {k: "" for k in FIELDS})

                # Basic identifiers
                row["borehole_id"] = borehole_id
                row["name"] = attrs.get("name", row.get("name", ""))
                row["location_id"] = attrs.get("location_hint", row.get("location_id", ""))

                # Coordinates (string for CSV)
                row["lat"] = str(attrs.get("lat", row.get("lat", "")) or "")
                row["lng"] = str(attrs.get("lng", row.get("lng", "")) or "")

                # Elevation + depth
                row["collar_elevation_m"] = str(
                    attrs.get("collar_elevation_m", row.get("collar_elevation_m", "")) or ""
                )
                row["max_depth_m"] = str(
                    attrs.get("max_depth_m", row.get("max_depth_m", "")) or ""
                )

                # Drill method + era
                row["drill_method"] = attrs.get("drill_method", row.get("drill_method", "")) or ""
                row["era_primary"] = attrs.get("era_primary", row.get("era_primary", "")) or ""

                # Related seasons
                row["related_seasons"] = normalize_related_seasons(
                    attrs.get("related_seasons", row.get("related_seasons", ""))
                )

                # Source priority + refs
                row["source_priority"] = attrs.get("source_priority", row.get("source_priority", "")) or ""
                row["source_refs"] = attrs.get("source_refs", row.get("source_refs", "")) or ""

                existing[borehole_id] = row

    # Write canonical CSV
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()

        for bid in sorted(existing.keys()):
            writer.writerow(existing[bid])

    print(f"[normalize_boreholes] Wrote {CSV_PATH}")


if __name__ == "__main__":
    main()