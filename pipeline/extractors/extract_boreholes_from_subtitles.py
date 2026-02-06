#!/usr/bin/env python3
import re
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
SUBTITLES = ROOT / "data_raw" / "subtitles"
FACTS_OUT = ROOT / "data_extracted" / "facts" / "boreholes.jsonl"

FACTS_OUT.parent.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Regex patterns
# -----------------------------
BOREHOLE_PATTERNS = [
    re.compile(r"\b[A-Z]{1,2}-?\d{1,3}\b"),        # C1, DH-82, OC1
    re.compile(r"\b(?:borehole|hole)\s+([A-Z0-9\-]+)\b", re.IGNORECASE),
    re.compile(r"\b10[- ]?X\b", re.IGNORECASE),    # 10X, 10-X
]

LOCATION_HINTS = {
    "money pit": "money_pit",
    "garden shaft": "garden_shaft",
    "smith": "smiths_cove",
    "smith's cove": "smiths_cove",
    "lot ": "lot_area",
    "swamp": "swamp",
}

# -----------------------------
# Helpers
# -----------------------------
def normalize_borehole_id(name: str) -> str:
    """Normalize borehole names to lowercase slugs."""
    name = name.upper().replace(" ", "").replace("--", "-")
    name = name.replace("BOREHOLE", "")
    return name.lower()

def extract_episode_from_filename(fname: str):
    """Extract SxxEyy from filename like s10e03.en.srt."""
    m = re.search(r"s(\d+)e(\d+)", fname, re.IGNORECASE)
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))

def compute_confidence(name: str, context: str, repeats: int) -> float:
    base = 0.85
    bonus = 0.0

    # Pattern match bonus
    if re.match(r"^[A-Z]{1,2}-?\d{1,3}$", name.upper()):
        bonus += 0.05

    # Repeated mentions
    bonus += min(repeats * 0.02, 0.10)

    # Location hints
    for hint in LOCATION_HINTS:
        if hint in context.lower():
            bonus += 0.05

    return min(base + bonus, 0.99)

# -----------------------------
# Main extraction logic
# -----------------------------
def extract_from_srt(path: Path):
    """Yield borehole facts from a single SRT file."""
    text = path.read_text(errors="ignore")
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    season, episode = extract_episode_from_filename(path.name)

    # Sliding window context
    for i, line in enumerate(lines):
        context_window = " ".join(lines[max(0, i-2): min(len(lines), i+3)])

        found = set()
        for pattern in BOREHOLE_PATTERNS:
            for match in pattern.findall(line):
                name = match if isinstance(match, str) else match[0]
                found.add(name)

        for raw_name in found:
            borehole_id = normalize_borehole_id(raw_name)

            # Count repeats in whole file
            repeats = sum(1 for l in lines if raw_name.lower() in l.lower())

            # Infer location from context
            location_hint = None
            for hint, loc_id in LOCATION_HINTS.items():
                if hint in context_window.lower():
                    location_hint = loc_id
                    break

            confidence = compute_confidence(raw_name, context_window, repeats)

            yield {
                "fact_type": "borehole",
                "borehole_id": borehole_id,
                "attributes": {
                    "name": raw_name,
                    "location_hint": location_hint,
                },
                "episode": {
                    "season": season,
                    "episode": episode,
                },
                "source": {
                    "origin": "subtitles",
                    "file": path.name,
                    "line_number": i + 1,
                    "priority": "ShowFrame",
                    "ref": f"{path.name}:{i+1}",
                },
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat(),
            }

# -----------------------------
# Orchestrate extraction
# -----------------------------
def main():
    with FACTS_OUT.open("w", encoding="utf-8") as out:
        for srt in sorted(SUBTITLES.glob("*.srt")):
            for fact in extract_from_srt(srt):
                out.write(json.dumps(fact) + "\n")

if __name__ == "__main__":
    main()
