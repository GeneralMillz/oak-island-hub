#!/usr/bin/env python3
import requests
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "pipeline" / "config" / "sources.yaml"
OUT_DIR = ROOT / "data_raw" / "lidar"

OUT_DIR.mkdir(parents=True, exist_ok=True)

def load_config():
    if CONFIG.exists():
        return yaml.safe_load(CONFIG.read_text())
    return {}

def main():
    cfg = load_config()
    lidar_cfg = cfg.get("lidar", {})
    url = lidar_cfg.get("url")
    if not url:
        print("[fetch_lidar] No LIDAR URL configured in sources.yaml under 'lidar.url'")
        return

    out_path = OUT_DIR / "oak_island_lidar.tif"
    print(f"[fetch_lidar] Downloading LIDAR from {url} → {out_path}")
    resp = requests.get(url, stream=True)
    resp.raise_for_status()
    with out_path.open("wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print(f"[fetch_lidar] Saved {out_path}")

if __name__ == "__main__":
    main()
