#!/usr/bin/env python3
import re
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
SUBTITLES = ROOT / "data_raw" / "subtitles"
FACTS_OUT = ROOT / "data_extracted" / "facts" / "artifacts.jsonl"

FACTS_OUT.parent.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Keyword + pattern config
# -----------------------------

# Phrases that strongly suggest an artifact
ARTIFACT_KEYWORDS = [
    "we found",
    "we've found",
    "they found",
    "they've found",
    "discovered",
    "we discovered",
    "they discovered",
    "uncovered",
    "we uncovered",
    "they uncovered",
    "pulled out",
    "brought up",
    "recovered",
    "we recovered",
    "they recovered",
]

# Nouns that often describe artifacts
ARTIFACT_NOUNS = [
    "coin",
    "button",
    "spike",
    "nail",
    "wood",
    "timber",
    "plank",
    "metal",
    "artifact",
    "object",
    "pottery",
    "ceramic",
    "stone",
    "rock",
    "cross",
    "brooch",
    "ring",
    "chain",
    "hinge",
    "key",
    "plate",
    "token",
    "lead",
    "iron",
    "gold",
    "silver",
]

# Depth patterns
DEPTH_PATTERNS = [
    re.compile(r"\b(\d+(\.\d+)?)\s*(ft|feet|')\b", re.IGNORECASE),
    re.compile(r"\b(\d+(\.\d+)?)\s*(m|meters)\b", re.IGNORECASE),
    re.compile(r"\b(\d+)\s*(?:–|-|to)\s*(\d+)\s*(ft|feet|m|meters)?\b", re.IGNORECASE),
]

# Location hints (same idea as boreholes)
LOCATION_HINTS = {
    "money pit": "money_pit",
    "garden shaft": "garden_shaft",
    "smith's cove": "smiths_cove",
    "smiths cove": "smiths_cove",
    "swamp": "swamp",
    "lot ": "lot_area",
}

# -----------------------------
# Helpers
# -----------------------------

def extract_episode_from_filename(fname: str):
    m = re.search(r"s(\d+)e(\d+)", fname, re.IGNORECASE)
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))


def normalize_depth_to_meters(text: str):
    """
    Try to extract a single representative depth in meters from a line of text.
    Returns (depth_m, depth_reference) or (None, None).
    """
    for pattern in DEPTH_PATTERNS:
        m = pattern.search(text)
        if not m:
            continue

        # Range pattern
        if pattern.pattern.find("to") != -1 or "–" in pattern.pattern or "-" in pattern.pattern:
            try:
                d1 = float(m.group(1))
                d2 = float(m.group(3)) if m.lastindex and m.lastindex >= 3 else d1
            except Exception:
                continue
            unit = m.group(4) if m.lastindex and m.lastindex >= 4 else None
            avg = (d1 + d2) / 2.0
            if unit and unit.lower().startswith("m"):
                return avg, f"{d1}-{d2} {unit}"
            else:
                meters = avg * 0.3048
                return meters, f"{d1}-{d2} ft"

        # Single value pattern
        try:
            val = float(m.group(1))
        except Exception:
            continue
        unit = m.group(3) if m.lastindex and m.lastindex >= 3 else None
        if unit and unit.lower().startswith("m"):
            return val, f"{val} m"
        else:
            meters = val * 0.3048
            return meters, f"{val} ft"

    return None, None


def detect_location_hint(context: str):
    ctx = context.lower()
    for hint, loc_id in LOCATION_HINTS.items():
        if hint in ctx:
            return loc_id
    return None


def compute_confidence(line: str, context: str, has_depth: bool, noun_hit: bool) -> float:
    base = 0.80
    bonus = 0.0

    # Strong artifact phrase
    if any(k in line.lower() for k in ARTIFACT_KEYWORDS):
        bonus += 0.10

    # Artifact noun present
    if noun_hit:
        bonus += 0.05

    # Depth present
    if has_depth:
        bonus += 0.05

    # Location hint present
    if detect_location_hint(context):
        bonus += 0.05

    return min(base + bonus, 0.99)


def guess_artifact_name(line: str):
    """
    Very simple heuristic: find the first artifact noun and return a short phrase around it.
    """
    lower = line.lower()
    for noun in ARTIFACT_NOUNS:
        idx = lower.find(noun)
        if idx != -1:
            start = max(0, idx - 20)
            end = min(len(line), idx + len(noun) + 20)
            phrase = line[start:end].strip()
            phrase = re.sub(r"^[\s,.-]+", "", phrase)
            phrase = re.sub(r"[\s,.-]+$", "", phrase)
            if phrase:
                return phrase[0].upper() + phrase[1:]
    return None


def make_artifact_id(season, episode, idx, name: str):
    base = f"s{season:02d}e{episode:02d}_a{idx:03d}"
    if name:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower())
        slug = slug.strip("-")
        if slug:
            return f"{base}_{slug[:40]}"
    return base

# -----------------------------
# Main extraction logic
# -----------------------------

def extract_from_srt(path: Path):
    text = path.read_text(errors="ignore")
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    season, episode = extract_episode_from_filename(path.name)

    artifacts = []
    for i, line in enumerate(lines):
        lower = line.lower()

        if not any(k in lower for k in ARTIFACT_KEYWORDS):
            continue

        noun_hit = any(noun in lower for noun in ARTIFACT_NOUNS)
        if not noun_hit:
            if "we found something" not in lower and "they found something" not in lower:
                continue

        context_window = " ".join(lines[max(0, i-2): min(len(lines), i+3)])

        depth_m, depth_ref = normalize_depth_to_meters(context_window)
        has_depth = depth_m is not None

        location_hint = detect_location_hint(context_window)

        name = guess_artifact_name(line) or "Unspecified artifact"

        confidence = compute_confidence(line, context_window, has_depth, noun_hit)

        artifacts.append({
            "line_index": i,
            "line_text": line,
            "context": context_window,
            "name": name,
            "depth_m": depth_m,
            "depth_reference": depth_ref,
            "location_hint": location_hint,
            "confidence": confidence,
        })

    for idx, art in enumerate(artifacts, start=1):
        artifact_id = make_artifact_id(season or 0, episode or 0, idx, art["name"])

        yield {
            "fact_type": "artifact",
            "artifact_id": artifact_id,
            "attributes": {
                "name": art["name"],
                "description": art["line_text"],
                "depth_m": art["depth_m"],
                "depth_reference": art["depth_reference"],
                "location_hint": art["location_hint"],
            },
            "episode": {
                "season": season,
                "episode": episode,
            },
            "source": {
                "origin": "subtitles",
                "file": path.name,
                "line_number": art["line_index"] + 1,
                "priority": "ShowFrame",
                "ref": f"{path.name}:{art['line_index']+1}",
            },
            "confidence": art["confidence"],
            "timestamp": datetime.utcnow().isoformat(),
        }

def main():
    with FACTS_OUT.open("w", encoding="utf-8") as out:
        for srt in sorted(SUBTITLES.glob("*.srt")):
            for fact in extract_from_srt(srt):
                out.write(json.dumps(fact) + "\n")

if __name__ == "__main__":
    main()
