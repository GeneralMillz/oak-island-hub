#!/usr/bin/env python3
import csv
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
CANON = ROOT / "data_canonical"
DERIVED = ROOT / "data_derived"
DERIVED.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def load_csv(path):
    rows = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def safe_int(v):
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    try:
        return int(float(s))
    except Exception:
        return None


def safe_float(v):
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def parse_bool(v):
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in ("true", "t", "yes", "y", "1"):
        return True
    if s in ("false", "f", "no", "n", "0"):
        return False
    return None


def parse_season_list(v):
    """
    Parse strings like:
      "1-3"
      "1,2,4-6"
      "9-10"
    into [1,2,3] etc.
    """
    if not v:
        return []
    s = str(v).strip()
    if not s:
        return []
    out = set()
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            try:
                start_s, end_s = part.split("-", 1)
                start = int(start_s)
                end = int(end_s)
                if start <= end:
                    for x in range(start, end + 1):
                        out.add(x)
                else:
                    for x in range(end, start + 1):
                        out.add(x)
            except Exception:
                continue
        else:
            try:
                out.add(int(part))
            except Exception:
                continue
    return sorted(out)


# ------------------------------------------------------------
# Builders
# ------------------------------------------------------------

def build_oak_island_data():
    locations = load_csv(CANON / "locations.csv")
    artifacts = load_csv(CANON / "artifacts.csv")
    episodes = load_csv(CANON / "episodes.csv")
    boreholes = load_csv(CANON / "boreholes.csv")
    intervals = load_csv(CANON / "borehole_intervals.csv")

    # Index artifacts by location
    artifacts_by_loc = {}
    for a in artifacts:
        loc_id = (a.get("location_id") or "").strip()
        artifacts_by_loc.setdefault(loc_id, []).append({
            "id": a.get("artifact_id"),
            "location_id": loc_id or None,
            "name": a.get("name"),
            "category": a.get("category"),
            "description": a.get("description"),
            "depth_m": safe_float(a.get("depth_m")),
            "depthReference": a.get("depth_reference"),
            "foundDate": a.get("found_date_iso"),
            "episodeSeason": safe_int(a.get("episode_season")),
            "episodeNumber": safe_int(a.get("episode_number")),
            "episodeTitle": a.get("episode_title"),
            "era": a.get("era_primary"),
            "confidence": safe_float(a.get("confidence_level")),
            "sourceRefs": a.get("source_refs"),
        })

    # Index intervals by borehole
    intervals_by_bh = {}
    for iv in intervals:
        bid = (iv.get("borehole_id") or "").strip()
        if not bid:
            continue
        intervals_by_bh.setdefault(bid, []).append({
            "id": iv.get("interval_id"),
            "borehole_id": bid,
            "depthFrom_m": safe_float(iv.get("depth_from_m")),
            "depthTo_m": safe_float(iv.get("depth_to_m")),
            "material": iv.get("material"),
            "waterIntrusion": parse_bool(iv.get("water_intrusion")),
            "sampleTaken": parse_bool(iv.get("sample_taken")),
            "sampleType": iv.get("sample_type"),
            "labResultRef": iv.get("lab_result_ref"),
            "confidence": safe_float(iv.get("confidence_level")),
            "sourceRefs": iv.get("source_refs"),
        })

    # Map locations by id for lookup
    loc_by_id = {}
    for loc in locations:
        loc_id = (loc.get("location_id") or "").strip()
        if not loc_id:
            continue
        loc_by_id[loc_id] = loc

    # Build borehole objects (top-level and nested-able)
    borehole_objs = {}
    boreholes_by_loc = {}

    for bh in boreholes:
        bid = (bh.get("borehole_id") or "").strip()
        if not bid:
            continue

        loc_id = (bh.get("location_id") or "").strip()
        lat = safe_float(bh.get("lat"))
        lng = safe_float(bh.get("lng"))
        bh_intervals = intervals_by_bh.get(bid, [])

        # Filter out obvious junk rows: require either intervals, lat/lng, or a real location_id
        if not bh_intervals and lat is None and (not loc_id or loc_id not in loc_by_id):
            continue

        bh_obj = {
            "id": bid,
            "name": bh.get("name"),
            "location_id": loc_id or None,
            "lat": lat,
            "lng": lng,
            "collarElevation_m": safe_float(bh.get("collar_elevation_m")),
            "maxDepth_m": safe_float(bh.get("max_depth_m")),
            "drillMethod": bh.get("drill_method"),
            "era": bh.get("era_primary"),
            "relatedSeasons": parse_season_list(bh.get("related_seasons")),
            "sourcePriority": bh.get("source_priority"),
            "sourceRefs": bh.get("source_refs"),
            "intervals": bh_intervals,
        }

        borehole_objs[bid] = bh_obj
        if loc_id:
            boreholes_by_loc.setdefault(loc_id, []).append(bh_obj)

    # Episodes grouped by season
    episodes_by_season = {}
    for e in episodes:
        s = safe_int(e.get("season"))
        ep = safe_int(e.get("episode"))
        if s is None or ep is None:
            continue
        episodes_by_season.setdefault(s, []).append(e)

    seasons_out = []
    for s, eps in sorted(episodes_by_season.items()):
        seasons_out.append({
            "season": s,
            "episodes": [
                {
                    "season": s,
                    "episode": safe_int(e.get("episode")),
                    "title": e.get("title"),
                    "airDate": e.get("air_date_iso"),
                    "shortSummary": e.get("short_summary"),
                }
                for e in sorted(eps, key=lambda x: safe_int(x.get("episode")) or 0)
            ],
        })

    # Build locations with nested boreholes + artifacts
    loc_out = []
    category_set = set()

    for loc in locations:
        loc_id = (loc.get("location_id") or "").strip()
        if not loc_id:
            continue

        loc_type = (loc.get("type") or "").strip() or None
        if loc_type:
            category_set.add(loc_type)

        loc_artifacts = artifacts_by_loc.get(loc_id, [])
        loc_boreholes = boreholes_by_loc.get(loc_id, [])

        loc_obj = {
            "id": loc_id,
            "name": loc.get("name"),
            "type": loc_type,
            "lat": safe_float(loc.get("lat")),
            "lng": safe_float(loc.get("lng")),
            "elevation_m": safe_float(loc.get("elevation_m")),
            "firstDocumentedYear": safe_int(loc.get("first_documented_year")),
            "era": loc.get("era_primary"),
            "relatedSeasons": parse_season_list(loc.get("related_seasons")),
            "sourcePriority": loc.get("source_priority"),
            "sourceRefs": loc.get("source_refs"),
            "geomSource": loc.get("geom_source"),
            "geomConfidence": safe_float(loc.get("geom_confidence")),
            "artifacts": loc_artifacts,
            "boreholes": loc_boreholes,
        }

        loc_out.append(loc_obj)

    categories_out = sorted(category_set)

    # Top-level boreholes list (Option 3: BOTH top-level + nested)
    boreholes_out = list(borehole_objs.values())

    data = {
        "meta": {
            "islandName": "Oak Island",
            "version": "1.0.0",
            "generatedAt": datetime.utcnow().isoformat() + "Z",
        },
        "categories": categories_out,
        "seasons": seasons_out,
        "locations": loc_out,
        "boreholes": boreholes_out,
    }

    out_path = DERIVED / "oak_island_data.json"
    out_path.write_text(json.dumps(data, indent=2))
    print(f"[build_json] Wrote {out_path}")


def build_boreholes():
    """
    Keep a standalone boreholes.json for any existing consumers.
    Uses the same filtered/merged borehole_objs as in build_oak_island_data,
    but rebuilt here for simplicity.
    """
    boreholes = load_csv(CANON / "boreholes.csv")
    intervals = load_csv(CANON / "borehole_intervals.csv")
    locations = load_csv(CANON / "locations.csv")

    intervals_by_bh = {}
    for iv in intervals:
        bid = (iv.get("borehole_id") or "").strip()
        if not bid:
            continue
        intervals_by_bh.setdefault(bid, []).append({
            "id": iv.get("interval_id"),
            "borehole_id": bid,
            "depthFrom_m": safe_float(iv.get("depth_from_m")),
            "depthTo_m": safe_float(iv.get("depth_to_m")),
            "material": iv.get("material"),
            "waterIntrusion": parse_bool(iv.get("water_intrusion")),
            "sampleTaken": parse_bool(iv.get("sample_taken")),
            "sampleType": iv.get("sample_type"),
            "labResultRef": iv.get("lab_result_ref"),
            "confidence": safe_float(iv.get("confidence_level")),
            "sourceRefs": iv.get("source_refs"),
        })

    loc_ids = { (l.get("location_id") or "").strip() for l in locations }

    out = {
        "meta": {
            "version": "1.0.0",
            "generatedAt": datetime.utcnow().isoformat() + "Z",
        },
        "boreholes": [],
    }

    for bh in boreholes:
        bid = (bh.get("borehole_id") or "").strip()
        if not bid:
            continue

        loc_id = (bh.get("location_id") or "").strip()
        lat = safe_float(bh.get("lat"))
        lng = safe_float(bh.get("lng"))
        bh_intervals = intervals_by_bh.get(bid, [])

        # Same junk filter as above
        if not bh_intervals and lat is None and (not loc_id or loc_id not in loc_ids):
            continue

        out["boreholes"].append({
            "id": bid,
            "name": bh.get("name"),
            "location_id": loc_id or None,
            "lat": lat,
            "lng": lng,
            "collarElevation_m": safe_float(bh.get("collar_elevation_m")),
            "maxDepth_m": safe_float(bh.get("max_depth_m")),
            "drillMethod": bh.get("drill_method"),
            "era": bh.get("era_primary"),
            "relatedSeasons": parse_season_list(bh.get("related_seasons")),
            "sourcePriority": bh.get("source_priority"),
            "sourceRefs": bh.get("source_refs"),
            "intervals": bh_intervals,
        })

    out_path = DERIVED / "boreholes.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"[build_json] Wrote {out_path}")


def build_episodes():
    episodes = load_csv(CANON / "episodes.csv")
    out = {
        "meta": {
            "generatedAt": datetime.utcnow().isoformat() + "Z",
        },
        "episodes": [],
    }
    for e in episodes:
        s = safe_int(e.get("season"))
        ep = safe_int(e.get("episode"))
        if s is None or ep is None:
            continue
        out["episodes"].append({
            "season": s,
            "episode": ep,
            "title": e.get("title"),
            "airDate": e.get("air_date_iso"),
            "shortSummary": e.get("short_summary"),
        })

    out["episodes"].sort(key=lambda x: (x["season"], x["episode"]))
    out_path = DERIVED / "episodes.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"[build_json] Wrote {out_path}")


def main():
    build_oak_island_data()
    build_boreholes()
    build_episodes()


if __name__ == "__main__":
    main()