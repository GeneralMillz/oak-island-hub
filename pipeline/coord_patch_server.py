#!/usr/bin/env python3
from flask import Flask, request, jsonify
from pathlib import Path
import json

app = Flask(__name__)

ROOT = Path(__file__).resolve().parents[1]
PATCH_FILE = ROOT / "data_extracted" / "facts" / "coord_patches.jsonl"
PATCH_FILE.parent.mkdir(parents=True, exist_ok=True)

@app.post("/coord_patch")
def coord_patch():
    data = request.json or {}
    required = {"location_id", "lat", "lng"}
    if not required.issubset(data.keys()):
        return jsonify({"status": "error", "error": "missing fields"}), 400

    with PATCH_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090)
