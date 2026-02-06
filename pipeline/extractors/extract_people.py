# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import os
import re
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRANSCRIPTS_PATH = PROJECT_ROOT / "data_extracted" / "facts" / "transcripts.jsonl"
FACTS_DIR = PROJECT_ROOT / "data_extracted" / "facts"
OUTPUT_PATH = FACTS_DIR / "people.jsonl"

# Core cast + common experts
PEOPLE = [
    "Rick", "Marty", "Gary", "Charles", "Jack", "Alex", "Craig",
    "Doug", "Billy", "Scott", "David", "Paul", "Peter",
    "Drayton", "Nolan", "Zena", "Samuel Ball", "Dan Blankenship",
    "Laird", "Miriam", "Emma", "Carmen Legge", "Terry Matheson",
    "Tom Nolan", "Steve Guptill", "Mike Huntley"
]

def load_transcripts():
    if not TRANSCRIPTS_PATH.exists():
        print("[people] ERROR: transcripts.jsonl not found")
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


def find_people(text):
    found = []
    text_lower = text.lower()

    for person in PEOPLE:
        name_lower = person.lower()
        if name_lower in text_lower:
            found.append(person)
    return found


def build_people_facts():
    transcripts = load_transcripts()

    if not transcripts:
        print("[people] No transcripts loaded.")
        return

    print("[people] Loaded %d transcript segments." % len(transcripts))

    for seg in transcripts:
        text = seg.get("text", "")
        if not text:
            continue

        matches = find_people(text)
        if not matches:
            continue

        for person in matches:
            yield {
                "season": seg["season"],
                "episode": seg["episode"],
                "timestamp": seg["start"],
                "person": person,
                "text": text,
                "confidence": 1.0,
                "source_file": seg.get("source_file"),
                "source": {
                    "type": "subtitle_person",
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
    print("[people] Project root:", PROJECT_ROOT)
    print("[people] Output:", OUTPUT_PATH)

    ensure_dirs()

    facts = list(build_people_facts())
    print("[people] Extracted %d person mentions." % len(facts))

    write_jsonl(OUTPUT_PATH, facts)
    print("[people] Wrote", OUTPUT_PATH)


if __name__ == "__main__":
    main()
