# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import os
import re
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRANSCRIPTS_PATH = PROJECT_ROOT / "data_extracted" / "facts" / "transcripts.jsonl"
FACTS_DIR = PROJECT_ROOT / "data_extracted" / "facts"
OUTPUT_PATH = FACTS_DIR / "measurements.jsonl"


# Regex patterns for measurement extraction
DEPTH_PATTERN = re.compile(
    r"(\b\d{1,4})\s*(feet|foot|ft|meters|meter|m)\b",
    flags=re.IGNORECASE
)

DISTANCE_PATTERN = re.compile(
    r"(\b\d{1,4})\s*(meters|meter|m|feet|foot|ft)\s*(east|west|north|south)?",
    flags=re.IGNORECASE
)

YEAR_PATTERN = re.compile(
    r"\b(1[4-9][0-9]{2}|20[0-2][0-9])\b"
)


def load_transcripts():
    if not TRANSCRIPTS_PATH.exists():
        print("[measurements] ERROR: transcripts.jsonl not found")
        return []

    segments = []
    with TRANSCRIPTS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                segments.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return segments


def ensure_dirs():
    FACTS_DIR.mkdir(parents=True, exist_ok=True)


def extract_depths(text):
    """Return list of (value, unit)."""
    results = []
    for match in DEPTH_PATTERN.findall(text):
        value = int(match[0])
        unit = match[1].lower()
        results.append((value, unit))
    return results


def extract_distances(text):
    """Return list of (value, unit, direction)."""
    results = []
    for match in DISTANCE_PATTERN.findall(text):
        value = int(match[0])
        unit = match[1].lower()
        direction = match[2].lower() if match[2] else ""
        results.append((value, unit, direction))
    return results


def extract_years(text):
    """Return list of years."""
    return [int(y) for y in YEAR_PATTERN.findall(text)]


def build_measurement_facts():
    transcripts = load_transcripts()

    if not transcripts:
        print("[measurements] No transcripts loaded.")
        return

    print("[measurements] Loaded %d transcript segments." % len(transcripts))

    for seg in transcripts:
        text = seg.get("text", "")
        if not text:
            continue

        # Depths
        for value, unit in extract_depths(text):
            yield {
                "season": seg["season"],
                "episode": seg["episode"],
                "timestamp": seg["start"],
                "measurement_type": "depth",
                "value": value,
                "unit": unit,
                "context": text,
                "confidence": 1.0,
                "source_file": seg.get("source_file"),
                "source": {
                    "type": "subtitle_measurement",
                    "file": seg.get("source_file"),
                },
            }

        # Distances
        for value, unit, direction in extract_distances(text):
            yield {
                "season": seg["season"],
                "episode": seg["episode"],
                "timestamp": seg["start"],
                "measurement_type": "distance",
                "value": value,
                "unit": unit,
                "direction": direction,
                "context": text,
                "confidence": 1.0,
                "source_file": seg.get("source_file"),
                "source": {
                    "type": "subtitle_measurement",
                    "file": seg.get("source_file"),
                },
            }

        # Years
        for year in extract_years(text):
            yield {
                "season": seg["season"],
                "episode": seg["episode"],
                "timestamp": seg["start"],
                "measurement_type": "year",
                "value": year,
                "unit": "year",
                "context": text,
                "confidence": 1.0,
                "source_file": seg.get("source_file"),
                "source": {
                    "type": "subtitle_measurement",
                    "file": seg.get("source_file"),
                },
            }


def write_jsonl(output_path, facts):
    tmp = output_path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for fact in facts:
            f.write(json.dumps(fact, ensure_ascii=False) + "\n")
    tmp.replace(output_path)


def main():
    print("[measurements] Project root:", PROJECT_ROOT)
    print("[measurements] Output:", OUTPUT_PATH)

    ensure_dirs()

    facts = list(build_measurement_facts())
    print("[measurements] Extracted %d measurement facts." % len(facts))

    write_jsonl(OUTPUT_PATH, facts)
    print("[measurements] Wrote", OUTPUT_PATH)


if __name__ == "__main__":
    main()
