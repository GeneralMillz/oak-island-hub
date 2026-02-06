# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import csv
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FACTS_PATH = PROJECT_ROOT / "data_extracted" / "facts" / "measurements.jsonl"
CANONICAL_PATH = PROJECT_ROOT / "data_canonical" / "measurements.csv"


def load_existing():
    """Load existing canonical CSV if present."""
    if not CANONICAL_PATH.exists():
        return {}

    rows = {}
    with CANONICAL_PATH.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            key = (
                int(r["season"]),
                int(r["episode"]),
                r["timestamp"],
                r["measurement_type"],
                r["value"],
                r["unit"],
                r.get("direction", "")
            )
            rows[key] = r
    return rows


def load_facts():
    """Load JSONL measurement facts."""
    if not FACTS_PATH.exists():
        print("[measurements] No measurements.jsonl found.")
        return []

    facts = []
    with FACTS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                facts.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return facts


def merge(existing, facts):
    """Merge new facts into existing canonical rows."""
    for fact in facts:
        season = int(fact["season"])
        episode = int(fact["episode"])
        timestamp = fact["timestamp"]
        mtype = fact["measurement_type"]
        value = str(fact["value"])
        unit = fact["unit"]
        direction = fact.get("direction", "")
        context = fact.get("context", "")
        confidence = float(fact.get("confidence", 1.0))
        source_file = fact.get("source_file", "")

        key = (season, episode, timestamp, mtype, value, unit, direction)

        if key not in existing:
            existing[key] = {
                "season": season,
                "episode": episode,
                "timestamp": timestamp,
                "measurement_type": mtype,
                "value": value,
                "unit": unit,
                "direction": direction,
                "context": context,
                "confidence": confidence,
                "source_refs": source_file,
            }
            continue

        row = existing[key]

        # Highest confidence wins
        if confidence > float(row["confidence"]):
            row["confidence"] = confidence
            row["context"] = context

        # Append source refs
        refs = set(row["source_refs"].split(";")) if row["source_refs"] else set()
        if source_file:
            refs.add(source_file)
        row["source_refs"] = ";".join(sorted(refs))

    return existing


def write_csv(rows):
    CANONICAL_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
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

    sorted_rows = sorted(
        rows.values(),
        key=lambda r: (
            int(r["season"]),
            int(r["episode"]),
            r["timestamp"],
            r["measurement_type"],
            r["value"]
        )
    )

    tmp = CANONICAL_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in sorted_rows:
            writer.writerow(r)

    tmp.replace(CANONICAL_PATH)


def main():
    print("[normalize_measurements] Loading existing canonical CSV...")
    existing = load_existing()

    print("[normalize_measurements] Loading measurement facts...")
    facts = load_facts()

    print("[normalize_measurements] Merging...")
    merged = merge(existing, facts)

    print("[normalize_measurements] Writing canonical CSV...")
    write_csv(merged)

    print("[normalize_measurements] Done. Wrote:", CANONICAL_PATH)


if __name__ == "__main__":
    main()
