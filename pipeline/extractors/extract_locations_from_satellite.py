#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FACTS_OUT = ROOT / "data_extracted" / "facts" / "locations.jsonl"
FACTS_OUT.parent.mkdir(parents=True, exist_ok=True)

def main():
    # Stub: no satellite-based location extraction yet
    if not FACTS_OUT.exists():
        FACTS_OUT.write_text("")
    print(f"[extract_locations_from_satellite] Stub - no locations extracted yet. File: {FACTS_OUT}")

if __name__ == "__main__":
    main()
