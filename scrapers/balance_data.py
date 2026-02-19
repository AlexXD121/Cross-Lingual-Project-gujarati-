"""
balance_data.py
===============
Balances all 4 dialect datasets to exactly 500 high-quality rows each.

Strategy per dialect:
  - Standard Gujarati (994 rows): quality-filter then pick TOP 500
    sorted by Gujarati script ratio (highest first)
  - Surti / Charotari (500 raw, over-cleaned): re-clean from _final.csv
    with quality-only filters (NO dialect marker required — trust the scraper)
  - Kathiawari (479 rows): quality-filter all 479 → flag how many are short

Quality filters (same for all dialects):
  - Gujarati script ratio >= 50%
  - Length 15–300 characters
  - No duplicates
  - No spam / emoji-only / pure-English rows

Output: data/raw/<Dialect>/<key>_balanced.csv  (500 rows each)
"""
import csv, re, os

BASE = r"d:\Cross Lingual Project(gujarati)\data\raw"
TARGET = 500

GUJ_RANGE = range(0x0A80, 0x0AFF + 1)
MIN_GUJ   = 0.50
MIN_LEN   = 15
MAX_LEN   = 300

# Shared spam patterns
SPAM = [
    re.compile(r"jay\s*jay\s*garvi",       re.IGNORECASE),
    re.compile(r"SB\s*Hindustani",         re.IGNORECASE),
    re.compile(r"http[s]?://",             re.IGNORECASE),
    re.compile(r"subscribe.*karo",         re.IGNORECASE),
    re.compile(r"like.*share.*karo",       re.IGNORECASE),
    re.compile(r"^\d+$"),
    re.compile(r"^[a-zA-Z\s\d]{0,20}$"),  # pure English / numbers
    re.compile(r"^[\U0001F300-\U0001FFFF\s]+$", re.UNICODE),  # emoji-only
]

def guj_ratio(text):
    chars = [c for c in text if not c.isspace()]
    if not chars: return 0.0
    return sum(1 for c in chars if ord(c) in GUJ_RANGE) / len(chars)

def quality_ok(text):
    t = text.strip()
    if not (MIN_LEN <= len(t) <= MAX_LEN): return False
    if guj_ratio(t) < MIN_GUJ: return False
    for p in SPAM:
        if p.search(t): return False
    return True

def load_csv(path):
    if not os.path.exists(path): return []
    with open(path, encoding="utf-8-sig") as f:
        return [row.get("sentence","").strip() for row in csv.DictReader(f)]

def save_balanced(sentences, key, outdir):
    out_path = os.path.join(BASE, outdir, f"{key}_balanced.csv")
    rows = [{"id": i+1, "sentence": s, "dialect": key, "source": "balanced"}
            for i, s in enumerate(sentences)]
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["id","sentence","dialect","source"])
        w.writeheader()
        w.writerows(rows)
    return out_path

# ── Dialect configurations ──────────────────────────────────────────────────
DIALECTS = [
    {
        "key":    "standard_gujarati",
        "label":  "Standard Gujarati",
        "outdir": "Standard Gujarati",
        "source": "standard_gujarati_final.csv",
        "strategy": "trim",          # pick best 500 from 994
    },
    {
        "key":    "kathiawari",
        "label":  "Kathiawari",
        "outdir": "Kathiawari",
        "source": "kathiawari_final.csv",
        "strategy": "all",           # take all that pass quality, flag if <500
    },
    {
        "key":    "surti",
        "label":  "Surti",
        "outdir": "Surti",
        "source": "surti_final.csv",
        "strategy": "quality_only",  # re-clean from raw — no marker required
    },
    {
        "key":    "charotari",
        "label":  "Charotari",
        "outdir": "Charotari",
        "source": "charotari_final.csv",
        "strategy": "quality_only",
    },
]

# ── Main ─────────────────────────────────────────────────────────────────────
print("=" * 60)
print("  DATASET BALANCER — Target: 500 rows per dialect")
print("=" * 60)

results = []
for cfg in DIALECTS:
    src_path = os.path.join(BASE, cfg["outdir"], cfg["source"])
    raw = load_csv(src_path)
    print(f"\n  {cfg['label']}")
    print(f"    Loaded  : {len(raw)} raw rows from {cfg['source']}")

    # De-duplicate
    seen = set()
    unique = []
    for s in raw:
        if s and s not in seen:
            seen.add(s); unique.append(s)
    print(f"    Unique  : {len(unique)} rows after dedup")

    # Quality filter
    passed = [s for s in unique if quality_ok(s)]
    print(f"    Quality : {len(passed)} rows pass (Guj≥50%, len {MIN_LEN}–{MAX_LEN}, no spam)")

    # Strategy
    if cfg["strategy"] == "trim":
        # Sort by Gujarati ratio descending → take top TARGET
        passed.sort(key=lambda s: guj_ratio(s), reverse=True)
        final = passed[:TARGET]
        print(f"    Trimmed : {len(final)} (top by Gujarati script %)")
    elif cfg["strategy"] == "all":
        final = passed[:TARGET]
        if len(passed) < TARGET:
            print(f"    ⚠️  Only {len(passed)} quality rows — need {TARGET-len(passed)} more")
    else:  # quality_only
        final = passed[:TARGET]

    # Save
    if final:
        out = save_balanced(final, cfg["key"], cfg["outdir"])
        print(f"    Saved   : {len(final)} rows → {os.path.basename(out)}")
    else:
        print(f"    ❌ No rows passed quality filter!")

    results.append((cfg["label"], len(final), TARGET))

# ── Summary ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  BALANCE SUMMARY")
print("=" * 60)
for label, n, tgt in results:
    bar   = "█" * (n // 10)
    icon  = "✅" if n >= tgt else f"⚠️  ({tgt-n} short)"
    print(f"  {icon}  {label:<26} {n:>5}/{tgt}  {bar}")
print("=" * 60)
print("\n  👉 Use *_balanced.csv files for model training.")
print("     Each has equal weight — model will not lean toward any dialect.")
