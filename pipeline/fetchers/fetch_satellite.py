#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SAT = ROOT / "data_raw" / "satellite"
SAT.mkdir(parents=True, exist_ok=True)

def main():
    print(f"[fetch_satellite] Stub - no satellite tiles fetched. Directory: {SAT}")

if __name__ == "__main__":
    main()
