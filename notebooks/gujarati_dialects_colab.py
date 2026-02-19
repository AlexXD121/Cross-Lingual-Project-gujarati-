# ============================================================
#  GUJARATI DIALECT DATA COLLECTION — GOOGLE COLAB NOTEBOOK
#  Guarantees 500 real dialect sentences per dialect
#  Engine: yt-dlp (auto video search) + youtube-comment-downloader
#  No API key. No browser. Fast.
# ============================================================

# ╔══════════════════════════════════════════════════╗
# ║  CELL 1 — Install                               ║
# ╚══════════════════════════════════════════════════╝
# %%
# !pip install yt-dlp youtube-comment-downloader -q

# ╔══════════════════════════════════════════════════╗
# ║  CELL 2 — Imports                               ║
# ╚══════════════════════════════════════════════════╝
# %%
import json, re, os, csv, time, subprocess
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR as SORT_BY_TOP

# ╔══════════════════════════════════════════════════╗
# ║  CELL 3 — Dialect Config                        ║
# ╚══════════════════════════════════════════════════╝
# %%
# Each dialect has:
#   key           → used as dialect label + filename
#   label         → human-readable name
#   search_queries→ yt-dlp will auto-search these to find real video IDs
#   seed_videos   → pre-verified video IDs (scraped first for speed)
#
# Already done locally:
#   standard_gujarati → 994 tuples ✅
#   kathiawari        → 479 tuples ✅

DIALECTS = [

    # ── MAINSTREAM ───────────────────────────────────────────
    {
        "key"   : "surti",
        "label" : "Surti",
        "seed_videos": [
            "iyR9jwE1ZV8", "vtpImhVOVEQ", "oJSr2Skjy8E", "YWTkZzcKXLw",
            "bxPuZIuhjC8", "PHMC6DUhlw4", "kfoIVDSLb90", "2DFpBR4AGzg",
            "lCytsppSHtg", "pAgO16orH2I",
        ],
        "search_queries": [
            "Surti Comedy gujarati",
            "Surati Jokes gujarati",
            "Surti slang video",
            "સૂરતી કૉમેડી",
            "Surat comedy gujarati dialect",
            "Surti funny video",
            "Poyro Poyri surti comedy",
            "Surat local comedy gujarati",
        ],
    },
    {
        "key"   : "pattani",
        "label" : "Pattani (Mehsani)",
        "seed_videos": [],
        "search_queries": [
            "Mehsana gujarati comedy",
            "Patan gujarati dialect",
            "Mehsani bhasha jokes",
            "Utter Gujarat gujarati comedy",
            "Mehsana local comedy video",
            "North Gujarat dialect comedy",
            "Patan Mehsana funny gujarati",
            "Mehsani gujarati funny video",
        ],
    },
    {
        "key"   : "charotari",
        "label" : "Charotari",
        "seed_videos": [],
        "search_queries": [
            "Charotar gujarati comedy",
            "Anand Kheda dialect comedy",
            "Charotari bhasha video",
            "Nadiad gujarati funny video",
            "Vallabh Vidyanagar comedy",
            "Charotar local jokes video",
            "Anand comedy gujarati",
            "Charotari dialect funny",
        ],
    },

    # ── HYBRID ────────────────────────────────────────────────
    {
        "key"   : "kutchi",
        "label" : "Kutchi",
        "seed_videos": [],
        "search_queries": [
            "Kutchi comedy video",
            "Kutchi bhasha jokes",
            "Kachchhi dialect funny",
            "Bhuj Kutch comedy",
            "Kutchi language funny video",
            "Kachchi comedy",
            "Kutch dialect funny video",
            "Kutchi lokgeet comedy",
        ],
    },
    {
        "key"   : "bagadi",
        "label" : "Bagadi",
        "seed_videos": [],
        "search_queries": [
            "Bagad Gujarat dialect comedy",
            "Palanpur Banaskantha comedy",
            "North Gujarat Rajasthani gujarati comedy",
            "Palanpur local comedy video",
            "Banaskantha dialect funny video",
            "Bagad region comedy",
            "North Gujarat border dialect comedy",
            "Palanpur gujarati jokes",
        ],
    },
    {
        "key"   : "vasavi",
        "label" : "Vasavi",
        "seed_videos": [],
        "search_queries": [
            "Vasava tribal Gujarat comedy",
            "Vasavi community Gujarat video",
            "Bharuch Narmada tribal comedy",
            "South Gujarat tribal dialect video",
            "Vasava adivasi song comedy",
            "Vasavi bhasha video",
            "Bharuch local dialect comedy",
            "Narmada tribal Gujarat funny",
        ],
    },
    {
        "key"   : "ghodari",
        "label" : "Ghodari",
        "seed_videos": [],
        "search_queries": [
            "Ghodari dialect gujarati comedy",
            "Dungarpur Banswara gujarati comedy",
            "North hilly Gujarat dialect",
            "Rajasthan Gujarat border dialect comedy",
            "Ghodari bhasha funny video",
            "Hilly Gujarat dialect comedy",
            "Dungarpur gujarati comedy",
            "Banswara border gujarati funny",
        ],
    },

    # ── COMMUNITY ─────────────────────────────────────────────
    {
        "key"   : "parsi_gujarati",
        "label" : "Parsi Gujarati",
        "seed_videos": [],
        "search_queries": [
            "Parsi gujarati comedy",
            "Parsi jokes gujarati language",
            "Parsi Bawa comedy video",
            "Parsi language funny video",
            "Parsiana gujarati comedy",
            "Bawa Bawi gujarati funny",
            "Parsi dialect humor video",
            "Parsi gujarati funny skit",
        ],
    },
    {
        "key"   : "musalmani",
        "label" : "Musalmani Gujarati",
        "seed_videos": [],
        "search_queries": [
            "Memon gujarati comedy",
            "Muslim gujarati dialect funny",
            "Surat Memon comedy video",
            "Urdu gujarati mix comedy",
            "Memon jokes funny video",
            "Muslim community gujarati comedy",
            "Dawoodi Bohra gujarati funny",
            "Memon dialect comedy video",
        ],
    },
    {
        "key"   : "saurashtra_tn",
        "label" : "Saurashtra (Tamil Nadu)",
        "seed_videos": [],
        "search_queries": [
            "Saurashtra community Tamil Nadu",
            "Saurashtrian dialect Tamil Nadu comedy",
            "Saurashtra language TN video",
            "Madurai Saurashtra community",
            "Saurashtra bhasha Tamil Nadu funny",
            "Saurashtrian language comedy",
            "Tamil Nadu gujarati community comedy",
            "Saurashtra TN dialect video",
        ],
    },

    # ── TRIBAL ────────────────────────────────────────────────
    {
        "key"   : "bhili",
        "label" : "Bhili",
        "seed_videos": [],
        "search_queries": [
            "Bhili tribal song comedy",
            "Bhil tribal dance song Gujarat",
            "Bhili bhasha funny video",
            "Bhili comedy Gujarat",
            "Adivasi Bhil Gujarat song",
            "Bhil community comedy video",
            "Bhili dialect funny",
            "Bhil adivasi funny video",
        ],
    },
    {
        "key"   : "gamit",
        "label" : "Gamit",
        "seed_videos": [],
        "search_queries": [
            "Gamit tribal Gujarat comedy",
            "Gamit bhasha song funny",
            "Tapi Dang tribal dialect song",
            "Gamit adivasi funny video",
            "Gamit community song Gujarat",
            "Dang Gamit funny video",
            "Gamit comedy Surat",
            "Gamit adivasi comedy video",
        ],
    },
    {
        "key"   : "chaudhari",
        "label" : "Chaudhari",
        "seed_videos": [],
        "search_queries": [
            "Chaudhari tribal Gujarat comedy",
            "Chaudhary adivasi song funny",
            "Chaudhari bhasha video Gujarat",
            "Tapi tribal dialect chaudhari comedy",
            "Chaudhary tribe Gujarat funny",
            "Chaudhari community song comedy",
            "South Gujarat tribal Chaudhari funny",
            "Chaudhary dialect comedy",
        ],
    },
    {
        "key"   : "rathwi",
        "label" : "Rathwi",
        "seed_videos": [],
        "search_queries": [
            "Rathwa tribal Chhota Udaipur comedy",
            "Rathwi dialect Gujarat funny",
            "Rathwa community dance song",
            "Chhota Udaipur tribal song",
            "Rathwa bhasha funny video",
            "Rathwa dance comedy",
            "Chhota Udaipur comedy video",
            "Rathwa tribal funny video",
        ],
    },
    {
        "key"   : "kukna",
        "label" : "Kukna",
        "seed_videos": [],
        "search_queries": [
            "Kukna tribal South Gujarat",
            "Kukna dialect Maharashtra Gujarat comedy",
            "Kukna bhasha song funny",
            "Kukna adivasi video Gujarat",
            "Kukna community funny video",
            "South Gujarat tribal Kukna comedy",
            "Kukna language funny video",
            "Kukna tribal song Gujarat",
        ],
    },
    {
        "key"   : "dhodia",
        "label" : "Dhodia",
        "seed_videos": [],
        "search_queries": [
            "Dhodia tribal Gujarat comedy",
            "Dhodia bhasha song funny",
            "Valsad Navsari tribal dialect comedy",
            "Dhodia community song funny",
            "Dhodia adivasi comedy",
            "Navsari tribal Dhodia funny video",
            "Dhodia language Gujarat comedy",
            "Dhodia tribe song video",
        ],
    },
    {
        "key"   : "nayki_tadvi",
        "label" : "Nayki Tadvi",
        "seed_videos": [],
        "search_queries": [
            "Tadvi tribal Gujarat comedy",
            "Nayki dialect Gujarat funny",
            "Tadvi Bhil community song",
            "Tadvi adivasi dance song",
            "Nayki Tadvi bhasha Gujarat",
            "Tadvi tribe Gujarat funny video",
            "Nayki dialect comedy",
            "Tadvi community Gujarat video",
        ],
    },

    # ── NOMADIC ───────────────────────────────────────────────
    {
        "key"   : "sidi",
        "label" : "Sidi",
        "seed_videos": [],
        "search_queries": [
            "Sidi community Gujarat Gir",
            "Siddi African Gujarat dance song",
            "Sidi Gir forest community video",
            "Siddi language Gujarat funny",
            "Sidi tribe dance Gujarat",
            "Siddi community video",
            "African Gujarati Sidi community dance",
            "Siddi tribal Gujarat song",
        ],
    },
    {
        "key"   : "ghisadi",
        "label" : "Ghisadi",
        "seed_videos": [],
        "search_queries": [
            "Ghisadi nomadic Gujarat community",
            "Ghisadi blacksmith Gujarat dialect",
            "Nomadic blacksmith Gujarat video",
            "Ghisadi community song video",
            "Ghisadi tribe Gujarat funny",
            "Nomadic tribe Gujarat comedy",
            "Ghisadi dialect funny video",
            "Ghisadi Gujarat community dance",
        ],
    },
    {
        "key"   : "gaduliya_lohar",
        "label" : "Gaduliya Lohar",
        "seed_videos": [],
        "search_queries": [
            "Gaduliya Lohar nomadic community",
            "Gadia Lohar Gujarat community video",
            "Gaduliya Lohar Rajasthani Gujarati comedy",
            "Gaduliya Lohar dialect funny",
            "Lohar nomadic tribe Gujarat dance",
            "Gadia Lohar song funny video",
            "Gaduliya Lohar community video Gujarat",
            "Gaduliya Lohar tribal song",
        ],
    },

    # ── COASTAL ───────────────────────────────────────────────
    {
        "key"   : "kharwa",
        "label" : "Kharwa",
        "seed_videos": [],
        "search_queries": [
            "Kharwa community Saurashtra comedy",
            "Kharva fishermen Gujarat dialect funny",
            "Kharva coastal Saurashtra comedy",
            "Kharwa bhasha Gujarat funny",
            "Coastal Saurashtra seafarer dialect video",
            "Kharwa fishermen funny video",
            "Kharva dialect Saurashtra comedy",
            "Kharwa Gujarat community video",
        ],
    },
    {
        "key"   : "mangeli",
        "label" : "Mangeli",
        "seed_videos": [],
        "search_queries": [
            "Mangela fishing community Gujarat comedy",
            "Mangeli dialect South Coast Gujarat",
            "South coast Gujarat fishing dialect funny",
            "Mangeli bhasha Gujarat video",
            "Coastal Gujarat Marathi Gujarati mix comedy",
            "Mangeli fishermen funny video",
            "South Gujarat coastal dialect comedy",
            "Mangeli community Gujarat funny",
        ],
    },
]

print(f"📋 Total dialects: {len(DIALECTS)}")
print(f"🎯 Target per dialect: 500 sentences")
print(f"📊 Grand total target: {len(DIALECTS) * 500} sentences")


# ╔══════════════════════════════════════════════════╗
# ║  CELL 4 — Text Filters                          ║
# ╚══════════════════════════════════════════════════╝
# %%
def is_gujarati(text: str, min_chars: int = 6) -> bool:
    """True if text contains ≥ min_chars Gujarati Unicode characters."""
    return sum(1 for c in text if '\u0A80' <= c <= '\u0AFF') >= min_chars

def is_mostly_english(text: str, threshold: float = 0.65) -> bool:
    """True if > threshold of the text is ASCII letters."""
    if not text:
        return True
    ascii_alpha = sum(1 for c in text if c.isascii() and c.isalpha())
    return ascii_alpha / max(len(text), 1) > threshold

def is_junk(text: str) -> bool:
    """True if text is basically empty after stripping URLs/punctuation."""
    clean = re.sub(r'http\S+', '', text)
    clean = re.sub(r'[^\w\s]', '', clean, flags=re.UNICODE).strip()
    return len(clean) < 10

def clean_text(text: str) -> str:
    """Strip URLs, hashtags, extra whitespace."""
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'#\w+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def keep(text: str) -> bool:
    """Combined filter — True means sentence is worth keeping."""
    if is_junk(text):            return False
    if is_mostly_english(text):  return False
    if not is_gujarati(text):    return False
    if len(text) < 15:           return False
    if len(text) > 800:          return False
    return True


# ╔══════════════════════════════════════════════════╗
# ║  CELL 5 — Auto Video Discovery via yt-dlp       ║
# ╚══════════════════════════════════════════════════╝
# %%
def find_video_ids(query: str, max_results: int = 15) -> list:
    """
    Use yt-dlp to search YouTube and return video ID strings.
    No download. Pure metadata search.
    """
    try:
        cmd = [
            "yt-dlp",
            f"ytsearch{max_results}:{query}",
            "--print", "id",
            "--no-download",
            "--quiet",
            "--no-warnings",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        ids = [line.strip() for line in result.stdout.strip().split('\n')
               if line.strip() and len(line.strip()) == 11]
        return ids
    except Exception as e:
        print(f"      ⚠️  yt-dlp search failed for '{query}': {e}")
        return []


# ╔══════════════════════════════════════════════════╗
# ║  CELL 6 — Core Scraper (guaranteed 500)         ║
# ╚══════════════════════════════════════════════════╝
# %%
def scrape_dialect(cfg: dict, target: int = 500, max_per_video: int = 200) -> list:
    """
    Scrape YouTube comments for one dialect until `target` sentences collected.

    Strategy:
    1. Try seed_videos first (pre-verified, fastest)
    2. Auto-search each query in turn using yt-dlp until we hit target
    3. Deduplicate on the fly with a seen-set
    """
    key    = cfg["key"]
    label  = cfg["label"]
    seeds  = cfg.get("seed_videos", [])
    queries = cfg.get("search_queries", [])

    dl        = YoutubeCommentDownloader()
    collected = []
    seen      = set()
    used_ids  = set()

    def _pull_video(vid_id: str) -> int:
        """Pull comments from a single video. Returns how many new ones added."""
        if vid_id in used_ids:
            return 0
        used_ids.add(vid_id)
        added = 0
        try:
            gen = dl.get_comments_from_url(
                f"https://www.youtube.com/watch?v={vid_id}",
                sort_by=SORT_BY_TOP
            )
            for comment in gen:
                if len(collected) >= target or added >= max_per_video:
                    break
                text = clean_text(comment.get("text", ""))
                if text not in seen and keep(text):
                    seen.add(text)
                    collected.append({
                        "id":       len(collected) + 1,
                        "sentence": text,
                        "dialect":  key,
                        "source":   "youtube_comments",
                    })
                    added += 1
        except Exception as e:
            print(f"         ⚠️  {vid_id}: {e}")
        return added

    print(f"\n{'='*60}")
    print(f"🗂️   {label}  [{key}]   target={target}")
    print(f"{'='*60}")

    #── Phase 1: seed videos (fast, pre-verified) ──────────────
    if seeds:
        print(f"  Phase 1: {len(seeds)} seed videos")
        for vid in seeds:
            if len(collected) >= target:
                break
            n = _pull_video(vid)
            print(f"    {vid} → +{n}  total={len(collected)}")
            time.sleep(0.5)

    # ── Phase 2: auto-search queries until target reached ──────
    if len(collected) < target:
        print(f"  Phase 2: auto-search ({len(queries)} queries)")
        for q in queries:
            if len(collected) >= target:
                break
            print(f"    🔍 '{q}'")
            vids = find_video_ids(q, max_results=15)
            print(f"       → {len(vids)} video IDs found")
            for vid in vids:
                if len(collected) >= target:
                    break
                n = _pull_video(vid)
                if n:
                    print(f"       {vid} → +{n}  total={len(collected)}")
                time.sleep(0.4)

    # ── Re-index IDs cleanly ───────────────────────────────────
    for i, item in enumerate(collected, 1):
        item["id"] = i

    shortfall = target - len(collected)
    if shortfall > 0:
        print(f"  ⚠️  Short by {shortfall} (dialect has limited YouTube content)")
    else:
        print(f"  ✅ {label}: {len(collected)} sentences  DONE")

    return collected


# ╔══════════════════════════════════════════════════╗
# ║  CELL 7 — Save Helpers                          ║
# ╚══════════════════════════════════════════════════╝
# %%
BASE_DIR = r"d:\Cross Lingual Project(gujarati)\data\raw"
os.makedirs(BASE_DIR, exist_ok=True)

def save_json(data: list, key: str):
    path = f"{BASE_DIR}/{key}_final.json"
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"    💾 JSON: {path}")

def save_csv(data: list, key: str):
    path = f"{BASE_DIR}/{key}_final.csv"
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['id', 'sentence', 'dialect', 'source'])
        w.writeheader()
        w.writerows(data)
    print(f"    📄 CSV:  {path}")


# ╔══════════════════════════════════════════════════╗
# ║  CELL 8 — RUN ALL DIALECTS                      ║
# ╚══════════════════════════════════════════════════╝
# %%
TARGET        = 500
ALL_RESULTS   = {}

for dialect in DIALECTS:
    key  = dialect["key"]
    data = scrape_dialect(dialect, target=TARGET)
    ALL_RESULTS[key] = data
    save_json(data, key)
    save_csv(data, key)
    time.sleep(2)  # polite pause between dialects

print("\n" + "="*60)
print("🎉  ALL DIALECTS FINISHED")
print("="*60)
for k, v in ALL_RESULTS.items():
    flag = "✅" if len(v) >= TARGET else f"⚠️  only {len(v)}"
    print(f"  {k:<22}  {len(v):>3}/500  {flag}")


# ╔══════════════════════════════════════════════════╗
# ║  CELL 9 — Zip & Download                        ║
# ╚══════════════════════════════════════════════════╝
# %%
import shutil

zip_path = r"d:\Cross Lingual Project(gujarati)\gujarati_dialects_data"
shutil.make_archive(zip_path, 'zip', BASE_DIR)
print(f"📦 Archive saved: {zip_path}.zip")
print(f"📁 Individual files at: {BASE_DIR}")


# ╔══════════════════════════════════════════════════╗
# ║  CELL 10 — Visual Summary                       ║
# ╚══════════════════════════════════════════════════╝
# %%
print("\n" + "="*60)
print("📊  FINAL COLLECTION REPORT")
print("="*60)
grand_total = 0
for k, v in ALL_RESULTS.items():
    grand_total += len(v)
    filled  = int(len(v) / 5)              # 500 → 100 chars → 20 blocks
    empty   = 20 - filled
    bar     = "█" * filled + "░" * empty
    pct     = int(len(v) / TARGET * 100)
    print(f"  {k:<22} [{bar}] {pct:>3}%  ({len(v)}/500)")
print(f"\n  {'GRAND TOTAL':<22}  {grand_total} sentences  "
      f"across {len(ALL_RESULTS)} dialects")
print("="*60)
