# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import os
import re
import json
from pathlib import Path
from difflib import SequenceMatcher

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRANSCRIPTS_PATH = PROJECT_ROOT / "data_extracted" / "facts" / "transcripts.jsonl"
CURATED_LOCATIONS_PATH = PROJECT_ROOT / "data_raw" / "locations_curated.json"
FACTS_DIR = PROJECT_ROOT / "data_extracted" / "facts"
OUTPUT_PATH = FACTS_DIR / "locations_from_subtitles.jsonl"


def load_transcripts():
    if not TRANSCRIPTS_PATH.exists():
        print("[locations] ERROR: transcripts.jsonl not found")
        return []

    segments = []
    with TRANSCRIPTS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                segments.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return segments


def load_curated_locations():
    """
    Supports both formats:
    1. ["Money Pit", "Smith's Cove", ...]
    2. [{"name": "Money Pit", "location_id": "money_pit"}, ...]
    """
    if not CURATED_LOCATIONS_PATH.exists():
        print("[locations] ERROR: curated locations file missing")
        return []

    with CURATED_LOCATIONS_PATH.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    curated = []

    for item in raw:
        # Case 1: string
        if isinstance(item, str):
            name = item.strip()
            loc_id = (
                name.lower()
                .replace(" ", "_")
                .replace("'", "")
                .replace("`", "")
            )
            curated.append({"name": name, "location_id": loc_id})
            continue

        # Case 2: dict
        if isinstance(item, dict):
            name = item.get("name")
            if not name:
                continue
            loc_id = item.get("location_id") or name.lower().replace(" ", "_")
            curated.append({"name": name, "location_id": loc_id})
            continue

    return curated


def fuzzy_ratio(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_locations_in_text(text, curated_locations):
    found = []
    text_lower = text.lower()

    for loc in curated_locations:
        name = loc["name"]
        loc_id = loc["location_id"]
        name_lower = name.lower()

        # Exact substring match
        if name_lower in text_lower:
            found.append((loc_id, name, 1.0))
            continue

        # Fuzzy fallback
        ratio = fuzzy_ratio(text_lower, name_lower)
        if ratio >= 0.80:
            found.append((loc_id, name, ratio))

    return found


def ensure_dirs():
    FACTS_DIR.mkdir(parents=True, exist_ok=True)


def build_location_facts():
    transcripts = load_transcripts()
    curated_locations = load_curated_locations()

    if not transcripts:
        print("[locations] No transcripts loaded.")
        return

    if not curated_locations:
        print("[locations] No curated locations loaded.")
        return

    print("[locations] Loaded %d transcript segments." % len(transcripts))
    print("[locations] Loaded %d curated locations." % len(curated_locations))

    for seg in transcripts:
        text = seg.get("text", "")
        if not text:
            continue

        matches = find_locations_in_text(text, curated_locations)
        if not matches:
            continue

        for loc_id, name, conf in matches:
            yield {
                "season": seg["season"],
                "episode": seg["episode"],
                "timestamp": seg["start"],
                "location_id": loc_id,
                "location_name": name,
                "text": text,
                "confidence": float(conf),
                "source_file": seg.get("source_file"),
                "source": {
                    "type": "subtitle_location",
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
    print("[locations] Project root:", PROJECT_ROOT)
    print("[locations] Output:", OUTPUT_PATH)

    ensure_dirs()

    facts = list(build_location_facts())
    print("[locations] Extracted %d location mentions." % len(facts))

    write_jsonl(OUTPUT_PATH, facts)
    print("[locations] Wrote", OUTPUT_PATH)


if __name__ == "__main__":
    main()
