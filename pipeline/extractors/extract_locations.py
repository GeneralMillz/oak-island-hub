#!/usr/bin/env python3
import json
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CURATED_JSON = ROOT / "data_raw" / "locations_curated.json"
CSV_OVERRIDE = ROOT / "data_raw" / "locations_master.csv"
JSON_OVERRIDE = ROOT / "data_raw" / "locations_extra.json"

ARTIFACT_FACTS = ROOT / "data_extracted" / "facts" / "artifacts.jsonl"
BOREHOLE_FACTS = ROOT / "data_extracted" / "facts" / "boreholes.jsonl"

OUT = ROOT / "data_extracted" / "facts" / "locations.jsonl"
OUT.parent.mkdir(parents=True, exist_ok=True)


def load_json(path):
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_csv(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_jsonl(path):
    if not path.exists():
        return []
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


def merge_dict(base, override):
    for k, v in override.items():
        if v not in (None, "", [], {}):
            base[k] = v
    return base


def main():
    curated = load_json(CURATED_JSON)
    csv_rows = load_csv(CSV_OVERRIDE)
    json_extra = load_json(JSON_OVERRIDE)
    artifacts = load_jsonl(ARTIFACT_FACTS)
    boreholes = load_jsonl(BOREHOLE_FACTS)

    merged = {}

    # 1. Start with curated JSON
    for loc_id, data in curated.items():
        merged[loc_id] = data.copy()

    # 2. Merge CSV overrides
    for row in csv_rows:
        loc_id = row.get("id")
        if not loc_id:
            continue
        merged.setdefault(loc_id, {})
        merged[loc_id] = merge_dict(merged[loc_id], row)

    # 3. Merge JSON overrides
    for loc_id, data in json_extra.items():
        merged.setdefault(loc_id, {})
        merged[loc_id] = merge_dict(merged[loc_id], data)

    # 4. Auto-add artifact findspots
    for art in artifacts:
        loc_id = art.get("location_id")
        if not loc_id:
            continue
        merged.setdefault(loc_id, {
            "id": loc_id,
            "name": loc_id.replace("_", " ").title(),
            "type": "findspot"
        })

    # 5. Auto-add borehole clusters
    for bh in boreholes:
        loc_id = bh.get("location_id")
        if not loc_id:
            continue
        merged.setdefault(loc_id, {
            "id": loc_id,
            "name": loc_id.replace("_", " ").title(),
            "type": "borehole_cluster"
        })

    # 6. Emit JSONL facts
    with OUT.open("w", encoding="utf-8") as f:
        for loc_id, data in merged.items():
            fact = {
                "fact_type": "location",
                "location_id": loc_id,
                "name": data.get("name"),
                "type": data.get("type"),
                "lat": float(data["lat"]) if "lat" in data else None,
                "lng": float(data["lng"]) if "lng" in data else None,
                "firstDocumentedYear": data.get("firstDocumentedYear"),
                "relatedSeasons": data.get("relatedSeasons", []),
                "description": data.get("description", ""),
                "confidence": 1.0,
                "source_refs": "curated"
            }
            f.write(json.dumps(fact) + "\n")

    print(f"[extract_locations] Wrote {OUT}")


if __name__ == "__main__":
    main()
