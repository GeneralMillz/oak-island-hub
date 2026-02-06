#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OCR_DIR = ROOT / "data_raw" / "ocr"
FACTS_OUT = ROOT / "data_extracted" / "facts" / "intervals.jsonl"
FACTS_OUT.parent.mkdir(parents=True, exist_ok=True)

def main():
    # Stub: real OCR parsing to be added later
    if not FACTS_OUT.exists():
        FACTS_OUT.write_text("")
    print(f"[extract_depths_from_ocr] Stub - no intervals extracted yet. File: {FACTS_OUT}")

if __name__ == "__main__":
    main()
