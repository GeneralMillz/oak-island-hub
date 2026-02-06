#!/usr/bin/env python3
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FACTS = ROOT / "data_extracted" / "facts" / "geometry_manual.jsonl"
CSV_PATH = ROOT / "data_canonical" / "locations.csv"

FIELDS = [
    "location_id","name","type","lat","lng","elevation_m",
    "first_documented_year","era_primary","related_seasons",
    "source_priority","source_refs","geom_source","geom_confidence"
]

def load_existing():
    rows = {}
    if CSV_PATH.exists():
        with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows[r["location_id"]] = r
    return rows

def merge(existing, fact):
    if fact.get("fact_type") != "location":
        return

    lid = fact.get("location_id")
    if not lid:
        return

    row = existing.get(lid, {k: "" for k in FIELDS})
    row["location_id"] = lid

    # Basic fields
    row["name"] = fact.get("name", row["name"])
    row["type"] = fact.get("type", row["type"])

    lat = fact.get("lat")
    lng = fact.get("lng")
    if lat is not None:
        row["lat"] = str(lat)
    if lng is not None:
        row["lng"] = str(lng)

    # Geometry provenance
    geom_source = fact.get("geom_source")
    if geom_source:
        row["geom_source"] = geom_source

    new_conf = fact.get("geom_confidence")
    try:
        new_conf_val = float(new_conf) if new_conf is not None else None
    except (TypeError, ValueError):
        new_conf_val = None

    prev_conf = None
    if row.get("geom_confidence"):
        try:
            prev_conf = float(row["geom_confidence"])
        except ValueError:
            prev_conf = None

    # Prefer higher confidence geometry
    if new_conf_val is not None:
        if prev_conf is None or new_conf_val > prev_conf:
            row["geom_confidence"] = str(new_conf_val)

    # Source refs
    ref = fact.get("source_refs")
    if ref:
        if row["source_refs"]:
            if ref not in row["source_refs"]:
                row["source_refs"] += f";{ref}"
        else:
            row["source_refs"] = ref

    existing[lid] = row

def main():
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = load_existing()

    if FACTS.exists():
        with FACTS.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                fact = json.loads(line)
                merge(existing, fact)

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for lid in sorted(existing.keys()):
            writer.writerow(existing[lid])

    print(f"[ingest_geometry_manual] Wrote {CSV_PATH}")

if __name__ == "__main__":
    main()
