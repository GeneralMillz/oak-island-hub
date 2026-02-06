#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPEN_DATA = ROOT / "data_raw" / "open_data"
OPEN_DATA.mkdir(parents=True, exist_ok=True)

def main():
    print(f"[fetch_open_data] Stub - no open data fetched. Directory: {OPEN_DATA}")

if __name__ == "__main__":
    main()
