#!/usr/bin/env python3
import subprocess
import sys
import time
import json
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPS_HEALTH = ROOT / "ops" / "health"
OPS_HEALTH.mkdir(parents=True, exist_ok=True)

STAGES = [
    ("fetchers", [
        "pipeline/fetchers/fetch_tmdb.py",
        "pipeline/fetchers/fetch_subtitles.py",
        "pipeline/fetchers/fetch_frames.py",
        "pipeline/fetchers/fetch_satellite.py",
        "pipeline/fetchers/fetch_open_data.py",
        "pipeline/fetchers/fetch_forums.py",
    ]),
    ("extractors", [
        "pipeline/extractors/extract_episode_metadata.py",
        "pipeline/extractors/extract_boreholes_from_subtitles.py",
        "pipeline/extractors/extract_artifacts_from_subtitles.py",
        "pipeline/extractors/extract_depths_from_ocr.py",
        "pipeline/extractors/extract_locations_from_satellite.py",
    ]),
    ("normalizers", [
        "pipeline/normalizers/normalize_episodes.py",
        "pipeline/normalizers/normalize_locations.py",
        "pipeline/normalizers/normalize_boreholes.py",
        "pipeline/normalizers/normalize_artifacts.py",
        "pipeline/normalizers/normalize_intervals.py",
    ]),
    ("validators", [
        "pipeline/validators/validate_canonical.py",
    ]),
    ("builders", [
        "pipeline/builders/build_json.py",
    ]),
]

def run_script(script_path: str, allow_fail: bool) -> bool:
    print(f"[RUN] {script_path}")
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        if result.returncode != 0:
            print(f"[ERROR] {script_path} exited with {result.returncode}")
            return allow_fail
        return True
    except Exception as e:
        print(f"[EXCEPTION] {script_path}: {e}", file=sys.stderr)
        return allow_fail

def main():
    run_id = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    metrics = {
        "last_run": run_id,
        "status": "ok",
        "stages": {},
        "counts": {},
        "new_since_last_run": {},
        "conflicts": {"total": 0, "by_type": {}},
        "alerts": [],
    }

    for stage_name, scripts in STAGES:
        print(f"\n=== STAGE: {stage_name} ===")
        start = time.time()
        stage_ok = True

        for script in scripts:
            # Fetchers/extractors can be soft-fail; normalizers/validators/builders are hard-fail
            allow_fail = stage_name in ("fetchers", "extractors")
            ok = run_script(script, allow_fail=allow_fail)
            if not ok:
                stage_ok = False
                if not allow_fail:
                    metrics["status"] = "error"
                    break

        duration = time.time() - start
        metrics["stages"][stage_name] = {
            "status": "ok" if stage_ok else "error",
            "duration_sec": round(duration, 2),
        }
        if not stage_ok and stage_name not in ("fetchers", "extractors"):
            break

    # Write health files
    last_run_path = OPS_HEALTH / "last_run.json"
    metrics_path = OPS_HEALTH / "metrics.json"

    with last_run_path.open("w", encoding="utf-8") as f:
        json.dump({"last_run": run_id, "status": metrics["status"]}, f, indent=2)

    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n[HEALTH] Wrote {last_run_path} and {metrics_path}")
    if metrics["status"] != "ok":
        sys.exit(1)

if __name__ == "__main__":
    main()
