"""
dialect_cleaner.py
==================
Strict post-processing cleaner for all Gujarati dialect CSV files.

Rules per dialect:
  - A comment is KEPT if it matches ≥1 region word OR ≥1 speech marker
  - AND does NOT match any hard-exclude pattern
  - AND passes minimum quality checks (length, Gujarati script ratio)

Run:  python dialect_cleaner.py
Output: <dialect>_clean.csv  (alongside each <dialect>_final.csv)
"""

import csv, re, os, unicodedata

# ─── Gujarati script detection ──────────────────────────────────────────────
GUJARATI_RANGE = range(0x0A80, 0x0AFF + 1)

def gujarati_ratio(text: str) -> float:
    chars = [c for c in text if not c.isspace()]
    if not chars:
        return 0.0
    guj = sum(1 for c in chars if ord(c) in GUJARATI_RANGE)
    return guj / len(chars)

def has_gujarati(text: str, min_ratio: float = 0.25) -> bool:
    return gujarati_ratio(text) >= min_ratio


# ─── Universal junk filters (applied to ALL dialects) ───────────────────────
UNIVERSAL_EXCLUDE = [
    r"^\s*[@#]\w+\s*$",                  # Only a mention/hashtag
    r"^[\U0001F300-\U0001FFFF\s]+$",     # Only emojis
    r"^\d+[\d\s,\.]+$",                  # Only numbers
    r"http[s]?://",                       # URLs
    r"^(subscribe|like|share|bell)",      # Spam calls (English)
    r"(subscribe|bell icon).{0,20}(karo|karjo|dabaavo)",  # Spam in Gujarati
    r"^[a-zA-Z\s]{0,20}$",              # Purely short English
]
UNIVERSAL_EXCLUDE_RE = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in UNIVERSAL_EXCLUDE]

MIN_LEN = 10   # Minimum character length
MIN_GUJ_RATIO = 0.20  # At least 20% Gujarati script

def universal_quality(text: str) -> bool:
    """Returns True if comment passes basic quality checks."""
    t = text.strip()
    if len(t) < MIN_LEN:
        return False
    if not has_gujarati(t, MIN_GUJ_RATIO):
        return False
    for pattern in UNIVERSAL_EXCLUDE_RE:
        if pattern.search(t):
            return False
    return True


# ─── Per-dialect rules ───────────────────────────────────────────────────────
# Each dialect entry:
#   "region_keywords"  : list of strs — any match → keep (case-insensitive)
#   "speech_markers"   : list of strs — dialect-specific words/spellings → keep
#   "hard_excludes"    : list of strs — if matched → always discard
#   "require_match"    : bool — if True, comment MUST match region OR speech marker
#                              if False, only quality check + hard_excludes apply

DIALECT_RULES = {

    # ── MAINSTREAM ────────────────────────────────────────────────────────────
    "surti": {
        "require_match": True,
        "region_keywords": [
            "સૂરત", "surat", "surti", "surati", "suratlala", "gj-05", "gj 05",
            "gj5", "gj 5", "valsad", "વલસાડ", "navsari", "નવસારી", "bharuch",
            "ભરૂચ", "bardoli", "baroli", "daman", "surat thi", "સૂરત થી",
            "kamamrejo", "kamrej", "kamsad", "olpad", "mandvi", "palsana",
            "katargam", "rander", "pal ", "varachha", "diamond city",
            "395",    # Surat PIN prefix
            "fried", "fred",   # Freddy Daruwala / Surti comedian
            "surti lala", "સૂરતીલ", "suratlal",
            "lavaari", "lavari",  # Surti comedy show
        ],
        "speech_markers": [
            "બો ", "બો મ", "બો ભ", "બો સ",   # 'bahu' → 'bo'
            "ઐ ભ", "ઐ ભ", "ઐ ભ", "ઐ ભ",
            "ઐ,", "ઐ ", "ઐ!",
            "ઐયો", "ડોસ્ટ", "પોયરો", "પૉયરો",
            "ની ગ",
            "hira", "હીરા ના કારખ", "karkhan",
            "lava ", "lavi ", "lavari",
            "સૂ ક", "સૂ મ",
            "કાથી",    # 'kathi' = Surti 'kyanthi' (where from)
            "ખમ્મ",    # Khamma — Surti greeting
        ],
        "hard_excludes": [
            "jay johar", "જય જોહ",
            "jay aadivasi", "jay adivasi",
            "SB Hindustani",
        ],
    },

    "pattani": {
        "require_match": True,
        "region_keywords": [
            "મહેસાણ", "mehsana", "mehsani", "mehoni", "mehona", "mehonan",
            "mehsaan", "patan", "પાટણ", "unjha", "ઉંઝા", "chanasma", "ચાણ",
            "kheralu", "visnagar", "vijapur", "sidhpur", "સિદ્ધ",
            "gj-2", "gj 2", "gj2",
        ],
        "speech_markers": [
            "mehoni ભ", "mehsani ભ",
            "આ ભ ઈ",       # 'bhai' dropped h
            "ઇ ", "ઈ ",    # North Gujarati vowel shift
        ],
        "hard_excludes": [
            "SB Hindustani",  "s.b hindustani", "sb hindustani",
            "ફુમત", "ફૂમત", "fumat",  # SB Hindustani character
            "jay mataji",  "જય માતાજ", "jay maa",
            "jay johar", "jay johor",
            "aadivasi", "આદિવ",
        ],
    },

    "charotari": {
        "require_match": True,
        "region_keywords": [
            "charotar", "ચારોટ", "anand", "આણંદ", "kheda", "ખેડ",
            "nadiad", "નડિ", "vallabh vidyanagar", "vallabh", "petlad",
            "borsad", "karamsad", "cambay", "khambhat",
            "gj-17", "gj 17", "gj17",
            "charotari", "dakor", "डाकोर", "ડાક",
            "anklav", "sojitra", "tarapur", "umreth",
            "gj-16", "gj 16",   # Kheda
            "charotar", "chartor",
        ],
        "speech_markers": [
            "ઓ ભ",      # 'o' ending typical of Charotari
            "ઓ યા",
            "સૈ ",
            "ભઈ ",      # 'bhai' pronounced 'bhei'
        ],
        "hard_excludes": [
            "jay johar", "SB Hindustani",
        ],
    },

    # ── HYBRID ────────────────────────────────────────────────────────────────
    "kutchi": {
        "require_match": True,
        "region_keywords": [
            "kutchi", "kutch", "kachchhi", "kachchi", "kachchh",
            "કચ્છ", "kcchh", "bhuj", "ભૂજ", "bhachau", "gandhidham",
            "mandvi", "mundra", "rapar", "anjar",
        ],
        "speech_markers": [
            "kutchi ભ", "kutchi ba",
            "aa thyo", "aa thya",   # Kutchi phonology
        ],
        "hard_excludes": [
            "jay jay garvi", "aadivasi", "jay johar",
        ],
    },

    "bagadi": {
        "require_match": True,
        "region_keywords": [
            "palanpur", "banaskantha", "bagad", "deesa", "disa",
            "patan", "radhanpur", "tharad", "dhanera",
            "gj-11", "gj 11", "banas",
        ],
        "speech_markers": [
            "ઠ ", " ઢ ",  # retroflex heavy Bagadi
        ],
        "hard_excludes": [
            "SB Hindustani", "ફુમત", "jay mataji", "jay johar", "aadivasi",
        ],
    },

    "vasavi": {
        "require_match": True,
        "region_keywords": [
            "vasava", "vasavi", "bharuch", "ભરૂચ", "narmada", "નર્મ",
            "rajpipla", "dediapada", "tilakwada", "jhagadia",
        ],
        "speech_markers": [
            "vasava ભ", "aadivaasi",
            "aadivaasi vasava",
        ],
        "hard_excludes": [
            "jay jay garvi", "jay johar", "SB Hindustani",
        ],
    },

    "ghodari": {
        "require_match": True,
        "region_keywords": [
            "ghodari", "ghodad", "dungarpur", "banswara",
            "godhra", "ગોધ", "aravalli", "sabarkantha",
        ],
        "speech_markers": [],
        "hard_excludes": [
            "jay jay garvi", "SB Hindustani", "jay johar",
        ],
    },

    # ── COMMUNITY ─────────────────────────────────────────────────────────────
    "parsi_gujarati": {
        "require_match": True,
        "region_keywords": [
            "parsi", "parsee", "bawa", "bawi", "zoroastrian",
            "parsiana", "irani", "navjote", "nowruz",
        ],
        "speech_markers": [
            "bawa", "bawi", "kem che bawa", "dikra",
            "parsi gujarati",
        ],
        "hard_excludes": [
            "jay jay garvi", "aadivasi", "SB Hindustani",
        ],
    },

    "musalmani": {
        "require_match": True,
        "region_keywords": [
            "memon", "meman", "bohra", "dawoodi", "bohra",
            "musalmani", "musalman", "surat memon",
        ],
        "speech_markers": [
            "memon ભ", "bohra ભ",
            "uyaa", "aave che",  # Memon phonetics
        ],
        "hard_excludes": [
            "jay jay garvi", "aadivasi", "SB Hindustani",
        ],
    },

    "saurashtra_tn": {
        "require_match": True,
        "region_keywords": [
            "saurashtra", "saurashtrian", "madurai", "tamil nadu",
            "tn", "chennai", "coimbatore", "saurashtra community",
        ],
        "speech_markers": [
            "saurashtrian bhasha", "saurashtra language",
        ],
        "hard_excludes": [
            "jay jay garvi", "SB Hindustani",
        ],
    },

    # ── TRIBAL ────────────────────────────────────────────────────────────────
    "bhili": {
        "require_match": True,
        "region_keywords": [
            "bhili", "bhil", "ભીલ", "adivasi bhil",
            "dang", "ડાંગ", "nandurbar", "jhabua",
        ],
        "speech_markers": [
            "bhili bol", "bhil community",
        ],
        "hard_excludes": [
            "jay jay garvi", "SB Hindustani",
        ],
    },

    "gamit": {
        "require_match": True,
        "region_keywords": [
            "gamit", "ગામ", "tapi", "dang", "vyara",
            "songadh", "surat tribal",
        ],
        "speech_markers": [],
        "hard_excludes": [
            "jay jay garvi", "SB Hindustani",
        ],
    },

    "chaudhary": {
        "require_match": True,
        "region_keywords": [
            "chaudhary", "chaudhari", "patidar north",
            "sabarkantha", "aravalli", "banaskantha",
            "aadivaasi chaudhary",
        ],
        "speech_markers": [],
        "hard_excludes": [
            "jay jay garvi", "SB Hindustani", "jay johar",
        ],
    },

    "rabari": {
        "require_match": True,
        "region_keywords": [
            "rabari", "rebari", "rabaari", "rabari samaj",
            "rabari community", "maldharis", "maldhari",
        ],
        "speech_markers": [
            "rabari bol", "rabari bhasha",
        ],
        "hard_excludes": [
            "jay jay garvi", "SB Hindustani",
        ],
    },

    "koli": {
        "require_match": True,
        "region_keywords": [
            "koli", "કોળ", "koli patel", "talapada koli",
            "maher", "koli samaj",
        ],
        "speech_markers": [],
        "hard_excludes": [
            "jay jay garvi", "SB Hindustani", "jay johar",
        ],
    },

    "harijanwas": {
        "require_match": True,
        "region_keywords": [
            "harijanwas", "harijan", "dalit", "vankars", "chamars",
            "ambedkar", "buddha", "harijans gujarat",
        ],
        "speech_markers": [],
        "hard_excludes": [
            "jay jay garvi", "SB Hindustani",
        ],
    },

    "ghisadi": {
        "require_match": False,   # Very rare dialect, relax rule
        "region_keywords": [
            "ghisadi", "ghisari", "lohar community gujarat",
        ],
        "speech_markers": [],
        "hard_excludes": [
            "jay jay garvi", "SB Hindustani",
        ],
    },

    "mangeli": {
        "require_match": False,   # Very rare
        "region_keywords": [
            "mangeli", "mangeliya", "sidi", "siddi", "siddi community",
            "african gujarati",
        ],
        "speech_markers": [],
        "hard_excludes": [
            "jay jay garvi", "SB Hindustani",
        ],
    },

    "vaghri": {
        "require_match": True,
        "region_keywords": [
            "vaghri", "waghri", "vaghara", "aadivaasi vaghri",
        ],
        "speech_markers": [],
        "hard_excludes": [
            "jay jay garvi", "SB Hindustani",
        ],
    },

    "mer": {
        "require_match": True,
        "region_keywords": [
            "mer", "mer community", "mer saurashtra", "porbandar",
            "પોરબ", "jamnagar", "morbi", "mer gujarati",
        ],
        "speech_markers": [],
        "hard_excludes": [
            "jay jay garvi", "SB Hindustani",
        ],
    },

    "patanwadi": {
        "require_match": True,
        "region_keywords": [
            "patanwadi", "patan wadi", "north gujarat nomadic",
            "vijapur", "patanwadis",
        ],
        "speech_markers": [],
        "hard_excludes": [
            "jay jay garvi", "SB Hindustani",
        ],
    },

    "aahiri": {
        "require_match": False,  # Very rare
        "region_keywords": [
            "aahiri", "ahiri", "ahir community", "ahir gujarat",
            "ahir saurashtra",
        ],
        "speech_markers": [],
        "hard_excludes": [
            "jay jay garvi", "SB Hindustani",
        ],
    },
}


# ─── Cleaner engine ───────────────────────────────────────────────────────────

def compile_patterns(word_list):
    return [re.compile(re.escape(w), re.IGNORECASE | re.UNICODE) for w in word_list]

def matches_any(text: str, patterns: list) -> bool:
    return any(p.search(text) for p in patterns)

def clean_dialect(key: str, rules: dict, base_dir: str) -> dict:
    in_path = os.path.join(base_dir, f"{key}_final.csv")
    out_path = os.path.join(base_dir, f"{key}_clean.csv")

    if not os.path.exists(in_path):
        return {"key": key, "status": "MISSING", "original": 0, "kept": 0}

    # Compile rule patterns
    region_re  = compile_patterns(rules.get("region_keywords", []))
    speech_re  = compile_patterns(rules.get("speech_markers", []))
    exclude_re = compile_patterns(rules.get("hard_excludes", []))
    require    = rules.get("require_match", True)

    kept_rows = []
    total = 0

    with open(in_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or ["id", "sentence", "dialect", "source"]

        for row in reader:
            total += 1
            text = row.get("sentence", "").strip()

            # 1. Universal quality gate
            if not universal_quality(text):
                continue

            # 2. Hard excludes (always reject)
            if matches_any(text, exclude_re):
                continue

            # 3. Dialect-specific match requirement
            if require:
                if not (matches_any(text, region_re) or matches_any(text, speech_re)):
                    continue

            kept_rows.append(row)

    # Re-number IDs
    for i, row in enumerate(kept_rows, 1):
        row["id"] = str(i)

    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept_rows)

    return {
        "key": key,
        "status": "OK",
        "original": total,
        "kept": len(kept_rows),
        "removed": total - len(kept_rows),
        "pct_kept": round(len(kept_rows) / total * 100, 1) if total else 0,
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    BASE_DIR = r"d:\Cross Lingual Project(gujarati)\data\raw"

    print("=" * 60)
    print("  GUJARATI DIALECT CLEANER — Strict Per-Dialect Rules")
    print("=" * 60)
    print(f"  Scanning: {BASE_DIR}\n")

    results = []
    for key, rules in DIALECT_RULES.items():
        result = clean_dialect(key, rules, BASE_DIR)
        results.append(result)

        if result["status"] == "MISSING":
            print(f"  ⏭️  [{key}]  — file not found yet (scraper still running?)")
        else:
            bar = "▓" * int(result["pct_kept"] / 5) + "░" * (20 - int(result["pct_kept"] / 5))
            print(
                f"  ✅ [{key:<20}]  "
                f"{result['original']:>4} → {result['kept']:>4} kept  "
                f"({result['pct_kept']:>5.1f}%)  [{bar}]"
            )
            if result["kept"] < 100:
                print(f"     ⚠️  Only {result['kept']} sentences — may need more sources!")

    print("\n" + "=" * 60)
    total_in  = sum(r["original"] for r in results if r["status"] == "OK")
    total_out = sum(r["kept"]     for r in results if r["status"] == "OK")
    print(f"  TOTAL:  {total_in} raw  →  {total_out} clean")
    print(f"  Overall retention: {round(total_out/total_in*100,1) if total_in else 0}%")
    print("=" * 60)
    print("\n  Clean files saved as: <dialect>_clean.csv")
    print("  These are the files to use for your dataset.\n")

if __name__ == "__main__":
    main()
