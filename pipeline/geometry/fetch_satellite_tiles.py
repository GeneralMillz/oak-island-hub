#!/usr/bin/env python3
import requests
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "pipeline" / "config" / "sources.yaml"
OUT_DIR = ROOT / "data_raw" / "satellite"

OUT_DIR.mkdir(parents=True, exist_ok=True)

def load_config():
    if CONFIG.exists():
        return yaml.safe_load(CONFIG.read_text())
    return {}

def main():
    cfg = load_config()
    sat_cfg = cfg.get("satellite", {})
    tiles = sat_cfg.get("tiles", [])
    if not tiles:
        print("[fetch_satellite_tiles] No satellite tiles configured in sources.yaml under 'satellite.tiles'")
        return

    base_url = sat_cfg.get("base_url", "")
    if not base_url:
        print("[fetch_satellite_tiles] No base_url configured under 'satellite.base_url'")
        return

    for tile in tiles:
        url = base_url.format(**tile)
        out_name = tile.get("name", f"tile_{tile.get('x','')}_{tile.get('y','')}.jpg")
        out_path = OUT_DIR / out_name
        print(f"[fetch_satellite_tiles] Downloading {url} → {out_path}")
        resp = requests.get(url, stream=True)
        resp.raise_for_status()
        with out_path.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"[fetch_satellite_tiles] Saved {out_path}")

if __name__ == "__main__":
    main()
