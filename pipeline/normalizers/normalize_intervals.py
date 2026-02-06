#!/usr/bin/env python3
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FACTS = ROOT / "data_extracted" / "facts" / "intervals.jsonl"
CSV_PATH = ROOT / "data_canonical" / "borehole_intervals.csv"

FIELDS = [
    "interval_id",
    "borehole_id",
    "depth_from_m",
    "depth_to_m",
    "material",
    "water_intrusion",
    "sample_taken",
    "sample_type",
    "lab_result_ref",
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
                rows[r["interval_id"]] = r
    return rows


def make_interval_id(borehole_id, d1, d2):
    """Stable interval ID format."""
    return f"{borehole_id}_{str(d1).replace('.', 'p')}_{str(d2).replace('.', 'p')}"


def merge(existing, fact):
    """Merge a single interval fact into the canonical dataset."""
    attrs = fact.get("attributes", {})
    borehole_id = attrs.get("borehole_id")
    d1 = attrs.get("depth_from_m")
    d2 = attrs.get("depth_to_m")

    if borehole_id is None or d1 is None or d2 is None:
        return

    interval_id = make_interval_id(borehole_id, d1, d2)
    src = fact.get("source", {})

    # Initialize row with all fields
    row = existing.get(interval_id, {k: "" for k in FIELDS})

    # Basic identifiers
    row["interval_id"] = interval_id
    row["borehole_id"] = borehole_id
    row["depth_from_m"] = str(d1)
    row["depth_to_m"] = str(d2)

    # Material
    row["material"] = attrs.get("material", row.get("material", "")) or ""

    # Optional fields
    row["water_intrusion"] = attrs.get("water_intrusion", row.get("water_intrusion", "")) or ""
    row["sample_taken"] = attrs.get("sample_taken", row.get("sample_taken", "")) or ""
    row["sample_type"] = attrs.get("sample_type", row.get("sample_type", "")) or ""
    row["lab_result_ref"] = attrs.get("lab_result_ref", row.get("lab_result_ref", "")) or ""

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

    existing[interval_id] = row


def main():
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = load_existing()

    if FACTS.exists():
        with FACTS.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                fact = json.loads(line)
                if fact.get("fact_type") != "interval":
                    continue
                merge(existing, fact)

    # Write canonical CSV
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for iid in sorted(existing.keys()):
            writer.writerow(existing[iid])

    print(f"[normalize_intervals] Wrote {CSV_PATH}")


if __name__ == "__main__":
    main()