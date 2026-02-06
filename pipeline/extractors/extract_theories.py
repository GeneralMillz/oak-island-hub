# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import os
import re
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRANSCRIPTS_PATH = PROJECT_ROOT / "data_extracted" / "facts" / "transcripts.jsonl"
FACTS_DIR = PROJECT_ROOT / "data_extracted" / "facts"
OUTPUT_PATH = FACTS_DIR / "theories.jsonl"

THEORY_PATTERNS = [
    ("templar", r"\btemplar\b|\bknights templar\b"),
    ("pirates", r"\bpirate\b|\bpirates\b"),
    ("spanish", r"\bspanish\b|\bspain\b"),
    ("french", r"\bfrench\b|\bfrance\b"),
    ("british", r"\bbritish\b|\bengland\b"),
    ("mi'kmaq", r"\bmikmaq\b|\bmi'kmaq\b|\bmicmac\b"),
    ("shakespeare", r"\bshakespeare\b|\bwilliam shakespeare\b"),
    ("bacon", r"\bbacon\b|\bfrancis bacon\b"),
    ("treasure", r"\btreasure\b|\bhoard\b"),
    ("templar_cross", r"\bcross\b|\btemplar cross\b"),
    ("holy_grail", r"\bgrail\b|\bholy grail\b"),
    ("nolan_cross", r"\bnolan\b|\bnolan's cross\b"),
    ("zena_map", r"\bzena\b|\bzena halpern\b"),
    ("roman", r"\broman\b|\brome\b"),
    ("viking", r"\bviking\b|\bnorse\b"),
    ("portuguese", r"\bportuguese\b|\bportugal\b")
]


def load_transcripts():
    if not TRANSCRIPTS_PATH.exists():
        print("[theories] ERROR: transcripts.jsonl not found")
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


def detect_theories(text):
    found = []
    for theory_type, pattern in THEORY_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.append(theory_type)
    return found


def build_theory_facts():
    transcripts = load_transcripts()

    if not transcripts:
        print("[theories] No transcripts loaded.")
        return

    print("[theories] Loaded %d transcript segments." % len(transcripts))

    for seg in transcripts:
        text = seg.get("text", "")
        if not text:
            continue

        matches = detect_theories(text)
        if not matches:
            continue

        for theory in matches:
            yield {
                "season": seg["season"],
                "episode": seg["episode"],
                "timestamp": seg["start"],
                "theory": theory,
                "text": text,
                "confidence": 1.0,
                "source_file": seg.get("source_file"),
                "source": {
                    "type": "subtitle_theory",
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
    print("[theories] Project root:", PROJECT_ROOT)
    print("[theories] Output:", OUTPUT_PATH)

    ensure_dirs()

    facts = list(build_theory_facts())
    print("[theories] Extracted %d theory mentions." % len(facts))

    write_jsonl(OUTPUT_PATH, facts)
    print("[theories] Wrote", OUTPUT_PATH)


if __name__ == "__main__":
    main()
