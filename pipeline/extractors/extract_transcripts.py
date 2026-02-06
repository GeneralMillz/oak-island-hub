#!/usr/bin/env python3
import os
import re
import json
from pathlib import Path
from datetime import timedelta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SUBTITLES_DIR = PROJECT_ROOT / "data_raw" / "subtitles"
FACTS_DIR = PROJECT_ROOT / "data_extracted" / "facts"
OUTPUT_PATH = FACTS_DIR / "transcripts.jsonl"


def parse_season_episode_from_filename(filename: str):
    """
    Expect filenames like: s07e03.en.srt or s1e2.en.srt
    Returns (season:int, episode:int) or (None, None) if not matched.
    """
    m = re.match(r"s(\d{1,2})e(\d{1,2})", filename, re.IGNORECASE)
    if not m:
        return None, None
    season = int(m.group(1))
    episode = int(m.group(2))
    return season, episode


def parse_srt_timecode(tc: str) -> str:
    """
    Normalize SRT timecode 'HH:MM:SS,mmm' to 'HH:MM:SS.mmm'
    """
    tc = tc.strip()
    return tc.replace(",", ".")


def parse_srt_file(path: Path):
    """
    Very simple SRT parser:
    - Blocks separated by blank lines
    - Each block:
        index
        start --> end
        text (one or more lines)
    Yields dicts with start, end, text.
    """
    with path.open("r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Normalize newlines
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n\s*\n", content)

    for block in blocks:
        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        if len(lines) < 2:
            continue

        # First line is index (we ignore)
        # Second line is timecode
        idx_line = lines[0]
        time_line = lines[1]

        # Time format: 00:00:01,000 --> 00:00:03,000
        m = re.match(r"(.+?)\s*-->\s*(.+)", time_line)
        if not m:
            # Sometimes index is omitted; try treating first line as time
            m2 = re.match(r"(.+?)\s*-->\s*(.+)", idx_line)
            if not m2:
                continue
            start_raw = m2.group(1).strip()
            end_raw = m2.group(2).strip()
            text_lines = lines[1:]
        else:
            start_raw = m.group(1).strip()
            end_raw = m.group(2).strip()
            text_lines = lines[2:]

        if not text_lines:
            continue

        start = parse_srt_timecode(start_raw)
        end = parse_srt_timecode(end_raw)
        text = " ".join(text_lines).strip()

        if not text:
            continue

        yield {
            "start": start,
            "end": end,
            "text": text,
        }


def ensure_dirs():
    FACTS_DIR.mkdir(parents=True, exist_ok=True)


def build_transcript_facts():
    """
    Scan all .srt files in SUBTITLES_DIR and yield transcript facts.
    """
    for path in sorted(SUBTITLES_DIR.glob("*.srt")):
        filename = path.name
        season, episode = parse_season_episode_from_filename(filename)
        if season is None or episode is None:
            # Skip files that don't match expected pattern
            continue

        for seg in parse_srt_file(path):
            fact = {
                "season": season,
                "episode": episode,
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
                "source_file": filename,
                "confidence": 1.0,
                "source": {
                    "type": "subtitle",
                    "file": filename,
                },
            }
            yield fact


def write_jsonl(output_path: Path, facts):
    """
    Overwrite transcripts.jsonl with a fresh pass.
    Idempotent: running again regenerates the same content for the same inputs.
    """
    tmp_path = output_path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        for fact in facts:
            f.write(json.dumps(fact, ensure_ascii=False) + "\n")
    tmp_path.replace(output_path)


def main():
    print(f"[transcripts] Project root: {PROJECT_ROOT}")
    print(f"[transcripts] Subtitles dir: {SUBTITLES_DIR}")
    print(f"[transcripts] Output: {OUTPUT_PATH}")

    ensure_dirs()

    facts = list(build_transcript_facts())
    print(f"[transcripts] Parsed {len(facts)} transcript segments from subtitles.")

    write_jsonl(OUTPUT_PATH, facts)
    print(f"[transcripts] Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
