"""
build_dataset.py
================
Final data pipeline for the Gujarati dialect project.

Steps:
  1. Load all 4 dialect _balanced.csv files
  2. Clean each one (script ratio, length, dedup, spam removal)
  3. Equalize — cap all dialects at the same count (min of the 4)
  4. Combine into one shuffled CSV: data/combined/gujarati_dialects.csv
  5. Delete all source dialect CSV files from data/raw/

Output: data/combined/gujarati_dialects.csv
Columns: id, sentence, dialect
"""

import csv
import os
import re
import random

# ── Config ────────────────────────────────────────────────────────────────────
BASE_RAW  = r"d:\Cross Lingual Project(gujarati)\data\raw"
BASE_OUT  = r"d:\Cross Lingual Project(gujarati)\data\combined"
OUT_FILE  = os.path.join(BASE_OUT, "gujarati_dialects.csv")

GUJ_RANGE = range(0x0A80, 0x0AFF + 1)
MIN_GUJ   = 0.50
MIN_LEN   = 15
MAX_LEN   = 300
SEED      = 42

SPAM = [
    re.compile(r"http[s]?://",          re.IGNORECASE),
    re.compile(r"subscribe.*karo",      re.IGNORECASE),
    re.compile(r"like.*share.*karo",    re.IGNORECASE),
    re.compile(r"jay\s*jay\s*garvi",    re.IGNORECASE),
    re.compile(r"^\d+$"),
    re.compile(r"^[a-zA-Z\s\d]{0,25}$"),               # pure Latin
    re.compile(r"^[\U0001F300-\U0001FFFF\s]+$", re.UNICODE),  # emoji-only
]

DIALECTS = [
    {
        "key":   "standard_gujarati",
        "label": "Standard Gujarati",
        "file":  os.path.join(BASE_RAW, "Standard Gujarati", "standard_gujarati_balanced.csv"),
    },
    {
        "key":   "kathiawari",
        "label": "Kathiawari",
        "file":  os.path.join(BASE_RAW, "Kathiawari", "kathiawari_balanced.csv"),
    },
    {
        "key":   "surti",
        "label": "Surti",
        "file":  os.path.join(BASE_RAW, "Surti", "surti_balanced.csv"),
    },
    {
        "key":   "charotari",
        "label": "Charotari",
        "file":  os.path.join(BASE_RAW, "Charotari", "charotari_balanced.csv"),
    },
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def guj_ratio(text):
    chars = [c for c in text if not c.isspace()]
    if not chars:
        return 0.0
    return sum(1 for c in chars if ord(c) in GUJ_RANGE) / len(chars)

def is_clean(text):
    t = text.strip()
    if not (MIN_LEN <= len(t) <= MAX_LEN):
        return False
    if guj_ratio(t) < MIN_GUJ:
        return False
    return all(not p.search(t) for p in SPAM)

def load_and_clean(path, key):
    rows = []
    seen = set()
    if not os.path.exists(path):
        print(f"  [!] File not found: {path}")
        return rows
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            s = row.get("sentence", "").strip()
            if s and s not in seen and is_clean(s):
                seen.add(s)
                rows.append(s)
    return rows

def delete_all_raw_csvs():
    """Delete all CSV files under data/raw/ after combining."""
    deleted = []
    for root, _, files in os.walk(BASE_RAW):
        for fname in files:
            if fname.endswith(".csv"):
                fpath = os.path.join(root, fname)
                os.remove(fpath)
                deleted.append(fpath)
    return deleted

# ── Main pipeline ─────────────────────────────────────────────────────────────
def main():
    random.seed(SEED)
    os.makedirs(BASE_OUT, exist_ok=True)

    print("=" * 58)
    print("  GUJARATI DIALECT DATASET PIPELINE")
    print("=" * 58)

    # Step 1 & 2 — Load and clean each dialect
    loaded = {}
    for d in DIALECTS:
        print(f"\n  Loading: {d['label']}")
        rows = load_and_clean(d["file"], d["key"])
        print(f"    Clean rows : {len(rows)}")
        loaded[d["key"]] = {"label": d["label"], "rows": rows}

    # Step 3 — Equalize: cap all at the minimum count
    min_count = min(len(v["rows"]) for v in loaded.values())
    print(f"\n  Equalizing to {min_count} rows per dialect")
    for key, v in loaded.items():
        if len(v["rows"]) > min_count:
            v["rows"] = random.sample(v["rows"], min_count)
        print(f"    {v['label']:<26}: {len(v['rows'])} rows")

    # Step 4 — Combine and shuffle
    all_rows = []
    for key, v in loaded.items():
        for sentence in v["rows"]:
            all_rows.append({
                "id":       None,
                "sentence": sentence,
                "dialect":  key,
            })

    random.shuffle(all_rows)
    for i, row in enumerate(all_rows):
        row["id"] = i + 1

    # Write combined CSV
    with open(OUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "sentence", "dialect"])
        writer.writeheader()
        writer.writerows(all_rows)

    total = len(all_rows)
    print(f"\n  Combined CSV written: {OUT_FILE}")
    print(f"  Total rows: {total} ({min_count} per dialect x {len(loaded)} dialects)")

    # Quick dialect distribution check
    print("\n  Distribution:")
    for key in loaded:
        count = sum(1 for r in all_rows if r["dialect"] == key)
        print(f"    {key:<26}: {count}")

    # Step 5 — Delete all raw dialect CSVs
    print("\n  Deleting source CSV files from data/raw/ ...")
    deleted = delete_all_raw_csvs()
    for f in deleted:
        rel = f.replace(r"d:\Cross Lingual Project(gujarati)\\", "")
        print(f"    Deleted: {rel}")

    print(f"\n  Done. {len(deleted)} files removed.")
    print("=" * 58)
    print(f"  Final output: data/combined/gujarati_dialects.csv")
    print(f"  Rows: {total} | Dialects: {len(loaded)} | Each: {min_count}")
    print("=" * 58)

if __name__ == "__main__":
    main()
