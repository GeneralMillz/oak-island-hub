#!/usr/bin/env python3
import subprocess
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "pipeline" / "config" / "sources.yaml"

# Oak Island bounding box (matches your existing overlays)
BBOX = {
    "min_lon": -64.3025,
    "min_lat": 44.5155,
    "max_lon": -64.2985,
    "max_lat": 44.5175,
}

TILES_DIR = ROOT / "app_public" / "tiles"
TEMP_DIR = ROOT / "data_raw" / "lidar" / "_clipped"


def run(cmd):
    print("[RUN]", " ".join(cmd))
    subprocess.run(cmd, check=True)


def load_config():
    with CONFIG.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dirs():
    TILES_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)


def clip_raster(src, dst):
    run([
        "gdalwarp",
        "-t_srs", "EPSG:4326",
        "-te",
        str(BBOX["min_lon"]),
        str(BBOX["min_lat"]),
        str(BBOX["max_lon"]),
        str(BBOX["max_lat"]),
        "-overwrite",
        str(src),
        str(dst),
    ])


def build_hillshade(dem_clipped, hillshade_clipped):
    run([
        "gdaldem", "hillshade",
        "-z", "1.0",
        "-s", "1.0",
        "-az", "315",
        "-alt", "45",
        str(dem_clipped),
        str(hillshade_clipped),
    ])


def to_byte(src, dst):
    """
    Convert a raster to 8-bit Byte using scaling.
    This is required for gdal2tiles on DEM.
    """
    run([
        "gdal_translate",
        "-of", "VRT",
        "-ot", "Byte",
        "-scale",
        str(src),
        str(dst),
    ])


def tiles_from_raster(src, out_dir, zoom_min=15, zoom_max=19):
    out_dir.mkdir(parents=True, exist_ok=True)
    run([
        "gdal2tiles.py",
        "-z", f"{zoom_min}-{zoom_max}",
        "-w", "none",
        str(src),
        str(out_dir),
    ])


def main():
    cfg = load_config()
    lidar_cfg = cfg.get("lidar", {})

    dem_path = ROOT / lidar_cfg["dem"]
    ortho_path = ROOT / lidar_cfg["orthophoto"]

    if not dem_path.exists():
        print(f"[process_rasters] DEM not found: {dem_path}")
        return
    if not ortho_path.exists():
        print(f"[process_rasters] Orthophoto not found: {ortho_path}")
        return

    ensure_dirs()

    dem_clipped = TEMP_DIR / "dem_clipped.tif"
    dem_byte = TEMP_DIR / "dem_byte.vrt"
    ortho_clipped = TEMP_DIR / "ortho_clipped.tif"
    hillshade_clipped = TEMP_DIR / "hillshade_clipped.tif"

    print("[process_rasters] Clipping DEM...")
    clip_raster(dem_path, dem_clipped)

    print("[process_rasters] Converting DEM to 8-bit Byte...")
    to_byte(dem_clipped, dem_byte)

    print("[process_rasters] Clipping orthophoto...")
    clip_raster(ortho_path, ortho_clipped)

    print("[process_rasters] Building hillshade...")
    build_hillshade(dem_clipped, hillshade_clipped)

    print("[process_rasters] Generating DEM tiles...")
    tiles_from_raster(dem_byte, TILES_DIR / "dem")

    print("[process_rasters] Generating hillshade tiles...")
    tiles_from_raster(hillshade_clipped, TILES_DIR / "hillshade")

    print("[process_rasters] Generating orthophoto tiles...")
    tiles_from_raster(ortho_clipped, TILES_DIR / "orthophoto")

    print("[process_rasters] Done. Tiles written under app_public/tiles/.")

if __name__ == "__main__":
    main()
