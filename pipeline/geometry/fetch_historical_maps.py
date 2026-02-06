#!/usr/bin/env python3
import requests
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "pipeline" / "config" / "sources.yaml"
OUT_DIR = ROOT / "data_raw" / "historical_maps"

OUT_DIR.mkdir(parents=True, exist_ok=True)

def load_config():
    if CONFIG.exists():
        return yaml.safe_load(CONFIG.read_text())
    return {}

def main():
    cfg = load_config()
    maps_cfg = cfg.get("historical_maps", {})
    urls = maps_cfg.get("urls", [])
    if not urls:
        print("[fetch_historical_maps] No historical map URLs configured in sources.yaml under 'historical_maps.urls'")
        return

    for i, url in enumerate(urls, start=1):
        ext = url.split("?")[0].split(".")[-1] or "bin"
        out_path = OUT_DIR / f"historical_map_{i}.{ext}"
        print(f"[fetch_historical_maps] Downloading {url} → {out_path}")
        resp = requests.get(url, stream=True)
        resp.raise_for_status()
        with out_path.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"[fetch_historical_maps] Saved {out_path}")

if __name__ == "__main__":
    main()
