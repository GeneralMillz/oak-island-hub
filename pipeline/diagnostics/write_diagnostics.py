#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
OPS = ROOT / "ops" / "health"
OPS.mkdir(parents=True, exist_ok=True)

def count_lines(path):
    if not path.exists():
        return 0
    return sum(1 for _ in path.open())

def load_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text())

def main():
    diagnostics = {}

    # --- TIMESTAMPS ---
    diagnostics["generatedAt"] = datetime.utcnow().isoformat() + "Z"

    # --- RAW DATA ---
    diagnostics["raw"] = {
        "tmdb_snapshots": len(list((ROOT / "data_raw" / "tmdb").glob("*.json"))),
        "subtitle_files": len(list((ROOT / "data_raw" / "subtitles").glob("*.srt"))),
        "frames_count": len(list((ROOT / "data_raw" / "frames").glob("*"))),
    }

    # --- FACT COUNTS ---
    diagnostics["facts"] = {
        "locations": count_lines(ROOT / "data_extracted" / "facts" / "locations.jsonl"),
        "boreholes": count_lines(ROOT / "data_extracted" / "facts" / "boreholes.jsonl"),
        "artifacts": count_lines(ROOT / "data_extracted" / "facts" / "artifacts.jsonl"),
        "intervals": count_lines(ROOT / "data_extracted" / "facts" / "intervals.jsonl"),
        "episodes": count_lines(ROOT / "data_extracted" / "facts" / "episodes.jsonl"),
    }

    # --- CANONICAL CSV COUNTS ---
    diagnostics["canonical"] = {
        "locations": count_lines(ROOT / "data_canonical" / "locations.csv") - 1,
        "boreholes": count_lines(ROOT / "data_canonical" / "boreholes.csv") - 1,
        "artifacts": count_lines(ROOT / "data_canonical" / "artifacts.csv") - 1,
        "intervals": count_lines(ROOT / "data_canonical" / "borehole_intervals.csv") - 1,
        "episodes": count_lines(ROOT / "data_canonical" / "episodes.csv") - 1,
    }

    # --- VALIDATION FLAGS ---
    validation = load_json(OPS / "last_run.json") or {}
    diagnostics["validation"] = {
        "canonical_ok": validation.get("canonical_ok", True),
        "json_ok": validation.get("json_ok", True),
        "map_ok": validation.get("map_ok", True),
    }

    # --- SUBTITLE HEALTH ---
    fail_cache = load_json(ROOT / "data_raw" / "subtitles" / "failures.json") or {}
    diagnostics["subtitles"] = {
        "fetched": diagnostics["raw"]["subtitle_files"],
        "missing": len(fail_cache),
        "failures": fail_cache,
    }

    # --- OUTPUT JSON HEALTH ---
    diagnostics["output"] = {
        "oak_island_data_json": (ROOT / "app_public" / "data" / "oak_island_data.json").exists(),
        "boreholes_json": (ROOT / "app_public" / "data" / "boreholes.json").exists(),
        "episodes_json": (ROOT / "app_public" / "data" / "episodes.json").exists(),
    }

    # --- WRITE ---
    (OPS / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2)
    )

    print("[diagnostics] Wrote diagnostics.json")

if __name__ == "__main__":
    main()
