#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRAMES = ROOT / "data_raw" / "frames"
FRAMES.mkdir(parents=True, exist_ok=True)

def main():
    print(f"[fetch_frames] Stub - no frames fetched. Directory: {FRAMES}")

if __name__ == "__main__":
    main()
