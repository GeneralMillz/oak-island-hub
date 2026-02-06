# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import csv
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_DIR = PROJECT_ROOT / "data_canonical"
APP_DATA_DIR = PROJECT_ROOT / "app_public" / "data"


def load_csv(path, fieldnames=None):
    if not path.exists():
        print("[semantic_builder] WARNING: missing", path)
        return []

    rows = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if fieldnames:
                # Ensure only expected fields
                rows.append({k: r.get(k, "") for k in fieldnames})
            else:
                rows.append(r)
    return rows


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def build_events():
    src = CANONICAL_DIR / "events.csv"
    dst = APP_DATA_DIR / "events.json"
    fields = [
        "season",
        "episode",
        "timestamp",
        "event_type",
        "text",
        "confidence",
        "source_refs",
    ]
    rows = load_csv(src, fields)
    write_json(dst, rows)
    print("[semantic_builder] Wrote", dst)


def build_measurements():
    src = CANONICAL_DIR / "measurements.csv"
    dst = APP_DATA_DIR / "measurements.json"
    fields = [
        "season",
        "episode",
        "timestamp",
        "measurement_type",
        "value",
        "unit",
        "direction",
        "context",
        "confidence",
        "source_refs",
    ]
    rows = load_csv(src, fields)
    write_json(dst, rows)
    print("[semantic_builder] Wrote", dst)


def build_people():
    src = CANONICAL_DIR / "people.csv"
    dst = APP_DATA_DIR / "people.json"
    fields = [
        "season",
        "episode",
        "timestamp",
        "person",
        "text",
        "confidence",
        "source_refs",
    ]
    rows = load_csv(src, fields)
    write_json(dst, rows)
    print("[semantic_builder] Wrote", dst)


def build_theories():
    src = CANONICAL_DIR / "theories.csv"
    dst = APP_DATA_DIR / "theories.json"
    fields = [
        "season",
        "episode",
        "timestamp",
        "theory",
        "text",
        "confidence",
        "source_refs",
    ]
    rows = load_csv(src, fields)
    write_json(dst, rows)
    print("[semantic_builder] Wrote", dst)


def build_location_mentions():
    src = CANONICAL_DIR / "location_mentions.csv"
    dst = APP_DATA_DIR / "location_mentions.json"
    fields = [
        "season",
        "episode",
        "timestamp",
        "location_id",
        "location_name",
        "text",
        "confidence",
        "source_refs",
    ]
    rows = load_csv(src, fields)
    write_json(dst, rows)
    print("[semantic_builder] Wrote", dst)


def main():
    print("[semantic_builder] Project root:", PROJECT_ROOT)
    build_events()
    build_measurements()
    build_people()
    build_theories()
    build_location_mentions()
    print("[semantic_builder] Done.")


if __name__ == "__main__":
    main()
