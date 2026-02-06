#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORUMS = ROOT / "data_raw" / "forums"
FORUMS.mkdir(parents=True, exist_ok=True)

def main():
    print(f"[fetch_forums] Stub - no forum data fetched. Directory: {FORUMS}")

if __name__ == "__main__":
    main()
