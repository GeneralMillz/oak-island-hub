#!/usr/bin/env python3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def run(cmd):
    print(f"[RUN] {' '.join(cmd)}")
    subprocess.run(cmd, check=False)

def main():
    run(["python", "pipeline/geometry/fetch_lidar.py"])
    run(["python", "pipeline/geometry/fetch_historical_maps.py"])
    run(["python", "pipeline/geometry/fetch_satellite_tiles.py"])

    run(["python", "pipeline/geometry/process_rasters.py"])

    run(["python", "pipeline/geometry/ingest_geometry_manual.py"])

    print("[geometry_ingest] Geometry ingest complete.")

if __name__ == "__main__":
    main()
