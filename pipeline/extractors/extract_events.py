# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import os
import re
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRANSCRIPTS_PATH = PROJECT_ROOT / "data_extracted" / "facts" / "transcripts.jsonl"
FACTS_DIR = PROJECT_ROOT / "data_extracted" / "facts"
OUTPUT_PATH = FACTS_DIR / "events.jsonl"


EVENT_PATTERNS = [
    ("digging", r"\bdig\b|\bdigging\b|\bexcavate\b|\bexcavation\b"),
    ("scanning", r"\bscan\b|\bscanning\b|\bground penetrating radar\b|\bgpr\b"),
    ("metal_detecting", r"\bmetal detector\b|\bmetal detecting\b|\bdetector\b"),
    ("discovery", r"\bfound\b|\bdiscovered\b|\bdiscovery\b|\buncovered\b"),
    ("anomaly", r"\banomaly\b|\banomalies\b|\binteresting signal\b"),
    ("research", r"\bresearch\b|\bdocuments\b|\barchives\b|\bhistorical\b"),
    ("interview", r"\binterview\b|\btalked to\b|\bspoke with\b"),
    ("wood_find", r"\bwood\b|\btimber\b|\bbeam\b"),
    ("artifact_find", r"\bartifact\b|\bitem\b|\bobject\b"),
    ("water_issue", r"\bwater\b|\bflood\b|\bdrain\b"),
]


def load_transcripts():
    if not TRANSCRIPTS_PATH.exists():
        print("[events] ERROR: transcripts.jsonl not found")
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


def detect_events(text):
    """Return list of (event_type, confidence)."""
    found = []
    for event_type, pattern in EVENT_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.append((event_type, 1.0))
    return found


def build_event_facts():
    transcripts = load_transcripts()

    if not transcripts:
        print("[events] No transcripts loaded.")
        return

    print("[events] Loaded %d transcript segments." % len(transcripts))

    for seg in transcripts:
        text = seg.get("text", "")
        if not text:
            continue

        matches = detect_events(text)
        if not matches:
            continue

        for event_type, conf in matches:
            yield {
                "season": seg["season"],
                "episode": seg["episode"],
                "timestamp": seg["start"],
                "event_type": event_type,
                "text": text,
                "confidence": float(conf),
                "source_file": seg.get("source_file"),
                "source": {
                    "type": "subtitle_event",
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
    print("[events] Project root:", PROJECT_ROOT)
    print("[events] Output:", OUTPUT_PATH)

    ensure_dirs()

    facts = list(build_event_facts())
    print("[events] Extracted %d event mentions." % len(facts))

    write_jsonl(OUTPUT_PATH, facts)
    print("[events] Wrote", OUTPUT_PATH)


if __name__ == "__main__":
    main()
