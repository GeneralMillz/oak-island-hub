#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_CANONICAL = ROOT / "data_canonical"

REQUIRED = [
    "episodes.csv",
    "locations.csv",
    "boreholes.csv",
    "borehole_intervals.csv",
    "artifacts.csv",
]

def main():
    missing = []
    for name in REQUIRED:
        path = DATA_CANONICAL / name
        if not path.exists():
            missing.append(name)
    if missing:
        print(f"[validate_canonical] Missing canonical files: {', '.join(missing)}")
        raise SystemExit(1)
    print("[validate_canonical] All canonical CSVs present.")

if __name__ == "__main__":
    main()
