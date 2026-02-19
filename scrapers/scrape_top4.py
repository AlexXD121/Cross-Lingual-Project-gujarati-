"""
scrape_top4.py
==============
FOCUSED SCRAPER — Top 4 Most Spoken Gujarati Dialects
Dialects: Standard Gujarati, Surti, Kathiawari, Charotari
Engine: yt-dlp (auto video search) + youtube-comment-downloader
Target: 500 high-quality, dialect-specific sentences per dialect
Quality gates:
  - Gujarati script ratio ≥ 50%
  - Length 15–350 chars
  - Zero duplicates
  - Dialect keyword OR speech-marker REQUIRED (no generic Gujarati)
Output: data/raw/<Dialect>/<key>_final.csv + .json
"""
import json, re, os, csv, time, subprocess

try:
    from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR as SORT_BY_TOP
except ImportError:
    subprocess.run(["pip","install","youtube-comment-downloader","yt-dlp","-q"])
    from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR as SORT_BY_TOP

try:
    import requests; from bs4 import BeautifulSoup; WEB=True
except ImportError:
    subprocess.run(["pip","install","requests","beautifulsoup4","-q"])
    try: import requests; from bs4 import BeautifulSoup; WEB=True
    except: WEB=False

# ── Global settings ──────────────────────────────────────────────────────────
TARGET       = 500
MAX_PER_VID  = 300
BASE_RAW     = r"d:\Cross Lingual Project(gujarati)\data\raw"
GUJ_RANGE    = range(0x0A80, 0x0AFF + 1)
HEADERS      = {"User-Agent":"Mozilla/5.0","Accept-Language":"gu,hi;q=0.9,en;q=0.5"}

# ── Script quality check ──────────────────────────────────────────────────────
def guj_ratio(text):
    chars = [c for c in text if not c.isspace()]
    if not chars: return 0.0
    return sum(1 for c in chars if ord(c) in GUJ_RANGE) / len(chars)

# ── Shared hard exclusions (spam / junk) ─────────────────────────────────────
COMMON_EXCL = [
    r"jay jay garvi gujarat",
    r"SB Hindustani",
    r"http[s]?://",
    r"^\d+$",
    r"^[\U0001F300-\U0001FFFF\s]{1,10}$",
    r"subscribe.*karo",
    r"like.*share.*karo",
    r"^[a-zA-Z\s]{0,20}$",   # pure English with no Gujarati
]
COMMON_EXCL_RE = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in COMMON_EXCL]

# ════════════════════════════════════════════════════════════════════════════
#  DIALECT DEFINITIONS
# ════════════════════════════════════════════════════════════════════════════
DIALECTS = [

    # ── 1. STANDARD GUJARATI ────────────────────────────────────────────────
    {
        "key":   "standard_gujarati",
        "label": "Standard Gujarati",
        "outdir": r"Standard Gujarati",
        "min_guj": 0.60,   # High threshold — must be proper Gujarati script
        "seed_videos": [
            "dOKCU7BuNAI","k8ypgT40rYI","2M0GQJ4LFHM","v6K1l6vcDlE",
            "qeMDLGtxLjY","RTXL9GbqXzg","Yg8qQ_BrRwI","wlVpb0i0wGs",
            "PBRHvn5SCKY","SL3OvAkVhLg","rYmrQaHVRbI","VJ4M7Y2g8EM",
            "qnNL2h9SVJQ","JWp3Dkj5s5I","T68L6fJ2FBQ","6D6rUNKI5Lc",
        ],
        "search_queries": [
            "Gujarati news anchor standard",
            "standard gujarati speech",
            "Gujarati literature podcast",
            "gujarat government speech gujarati",
            "standard gujarati education video",
            "gujarati university lecture",
            "doordarshan gujarati news",
            "gujarati essay speech",
            "gujarat vidhansabha gujarati speech",
            "akashvani gujarati radio",
            "formal gujarati speech",
            "gujarati documentary standard",
            "gujarat chief minister gujarati speech",
            "standard gujarati poem recitation",
        ],
        "region_words": [
            "gujarat","gujarati","ahmedabad","gandhinagar","gujaratna",
            "gujaratma","gujarat sarkar","gj-","ahmedavad",
        ],
        "speech_markers": [  # Formal/Standard markers
            "prabhu","samaj","sarkaar","vikas","niti","yojana","shikshan",
            "uttam","pragati","matru bhasha","rashtriya","rajya",
        ],
        "web_sources": [
            {"url":"https://www.gujaratsamachar.com/","name":"Gujarat Samachar"},
            {"url":"https://sandesh.com/","name":"Sandesh"},
            {"url":"https://www.divyabhaskar.co.in/local/gujarat/","name":"Divya Bhaskar Gujarat"},
            {"url":"https://akila.news/","name":"Akila News"},
        ],
    },

    # ── 2. SURTI ────────────────────────────────────────────────────────────
    {
        "key":   "surti",
        "label": "Surti",
        "outdir": r"Surti",
        "min_guj": 0.50,
        "seed_videos": [
            "iyR9jwE1ZV8","vtpImhVOVEQ","oJSr2Skjy8E","YWTkZzcKXLw",
            "bxPuZIuhjC8","PHMC6DUhlw4","kfoIVDSLb90","2DFpBR4AGzg",
            "lCytsppSHtg","pAgO16orH2I","6Xk8F5rXDhQ","KJ5tpBl3Vao",
            "q0EQPG1XP5A","Mn6yIBHRPFc","TxLkGz2RJpQ","W9wD5rKjLnM",
        ],
        "search_queries": [
            "Surti comedy gujarati",
            "Surati Jokes gujarati",
            "Surti dialect funny video",
            "સૂ-ર-ત-ી ક-ૉ-મ-ે-ડ-ી",
            "Surat comedy gujarati local",
            "Poyri surti comedy",
            "Surti slang skit",
            "Surat tamari ma comedy",
            "Surti kaka funny video",
            "surat ni boli comedy",
            "surti boli funny skit",
            "surat local gujarati comedy",
            "surat dialect funny video",
            "surti bhasha jokes",
            "surti comedy natak",
        ],
        "region_words": [
            "surat","surti","suurat","suratma","surat ni","surat na",
            "gj-05","gj 05","gj05","dumas","hazira","katargam","varachha",
            "limbayat","udhna","althan","adajan",
        ],
        "speech_markers": [   # Classic Surti vocabulary
            "poyro","poyri","aiyaan","kaiyaan","chhelo","thaano","kaaya",
            "dikaru","dikri","khem cho","sun bhai","ame","tame","tamane",
            "surat ni boli","surti boli","surti language",
        ],
        "web_sources": [
            {"url":"https://www.divyabhaskar.co.in/local/gujarat/surat/","name":"DB Surat"},
            {"url":"https://sandesh.com/tag/surat","name":"Sandesh Surat"},
            {"url":"https://www.gujaratmitra.in/","name":"Gujarat Mitra"},
            {"url":"https://akilanews.com/category/surat/","name":"Akila Surat"},
        ],
    },

    # ── 3. KATHIAWARI ───────────────────────────────────────────────────────
    {
        "key":   "kathiawari",
        "label": "Kathiawari",
        "outdir": r"Kathiawari",
        "min_guj": 0.50,
        "seed_videos": [
            "ZQ7m7PbkAos","X1TkD7BlFrw","94NN_KcAXoE","dJT0NbXk3hQ",
            "YkR3gM2TwPs","VmC4nPjLzXt","UlB5oQkMyWs","TnA6pRjLxVr",
            "SmZ7qQiMwUq","RlY8pPiLwTp","QkX9oOhLvSo","PjW0nNgLuRn",
            "OiV1mMfLtQm","NhU2lLeKsPlL","MgT3kKdJrOk","LfS4jJcIqNj",
        ],
        "search_queries": [
            "Kathiawari comedy gujarati",
            "Saurashtra dialect funny",
            "Rajkot local comedy gujarati",
            "kathiawari boli funny",
            "kathiawadi jokes video",
            "સ-ૌ-ર-ા-ષ-્-ટ-્-ર-ી comedy",
            "Junagadh dialect funny video",
            "Bhavnagar comedy gujarati",
            "Amreli local comedy gujarati",
            "Saurashtra comedy video",
            "Rajkot funny gujarati video",
            "kathiawari natak funny",
            "kathiawad dialect comedy",
            "saurashtra region comedy video",
            "Porbandar dialect funny",
        ],
        "region_words": [
            "kathiawad","kathiawari","kathiawadi","saurashtra","saurashtrian",
            "rajkot","junagadh","bhavnagar","jamnagar","amreli","porbandar",
            "surendranagar","morbi","gondal","jetpur","veraval","somnath",
            "gir","gj-03","gj 03","gj-04","gj 04","gj-12","gj 12",
        ],
        "speech_markers": [   # Kathiawari dialect markers
            "chho","chha","kyaank","tyaank","avo","jao bhai","re bhai",
            "aavo","jaavo","shu che","shu karyo","kathiawari boli",
            "saurashtra ni boli","kathiawad dialect",
        ],
        "web_sources": [
            {"url":"https://www.divyabhaskar.co.in/local/gujarat/rajkot/","name":"DB Rajkot"},
            {"url":"https://sandesh.com/tag/saurashtra","name":"Sandesh Saurashtra"},
            {"url":"https://www.chitralekha.com/gujarati/","name":"Chitralekha"},
            {"url":"https://akilanews.com/category/rajkot/","name":"Akila Rajkot"},
        ],
    },

    # ── 4. CHAROTARI ────────────────────────────────────────────────────────
    {
        "key":   "charotari",
        "label": "Charotari",
        "outdir": r"Charotari",
        "min_guj": 0.50,
        "seed_videos": [
            "dJT0NbXk3hQ","B4MeCs2KXuI","S9wFvBnJpYt","RxHuAmKoZwL",
            "QwGtZlJnYvK","PvFsYkInXuJ","OuErXjHmWtI","NtDqWiGlVsH",
            "MsEpViFlUrG","LrDoUhEkTqF","KqCnTgDjSpE","JpBmSfCiRoD",
            "IoAlReBoQnC","HnZkQdAnPmB","GmYjPcZmOlA","FlXiObYlNkZ",
        ],
        "search_queries": [
            "Charotari dialect comedy",
            "Charotar funny gujarati video",
            "Anand Kheda local comedy",
            "Charotari boli funny",
            "Nadiad local gujarati comedy",
            "Vallabh Vidyanagar comedy",
            "charotar dialect jokes",
            "anand comedy gujarati",
            "charotari skit funny",
            "charotari bhasha video",
            "kheda anand comedy gujarati",
            "charotar local comedy",
            "charotari natak funny",
            "anand district comedy gujarati",
            "charotari gujarati dialect video",
        ],
        "region_words": [
            "charotar","charotari","charotar ni","anand","kheda","nadiad",
            "vallabh vidyanagar","borsad","petlad","umreth","tarapur",
            "karamsad","vidyanagar","gj-07","gj 07","gj-09","gj 09",
        ],
        "speech_markers": [   # Charotari specific vocabulary
            "haalo","haali","aave","jaave","kyaare","tyaare","kiyaanyo",
            "charotari boli","charotar dialect","anand ni boli",
            "charotari language","charotar bhasha",
        ],
        "web_sources": [
            {"url":"https://www.divyabhaskar.co.in/local/gujarat/anand/","name":"DB Anand"},
            {"url":"https://sandesh.com/tag/anand","name":"Sandesh Anand"},
            {"url":"https://akilanews.com/category/anand/","name":"Akila Anand"},
            {"url":"https://www.divyabhaskar.co.in/local/gujarat/kheda/","name":"DB Kheda"},
        ],
    },
]

# ════════════════════════════════════════════════════════════════════════════
#  CORE FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

def make_filters(cfg):
    region_re = [re.compile(re.escape(w), re.IGNORECASE) for w in cfg["region_words"]]
    speech_re = [re.compile(re.escape(w), re.IGNORECASE) for w in cfg["speech_markers"]]
    min_guj   = cfg["min_guj"]

    def is_valid(text):
        t = text.strip()
        if len(t) < 15 or len(t) > 350: return False
        if guj_ratio(t) < min_guj: return False
        for p in COMMON_EXCL_RE:
            if p.search(t): return False
        if any(p.search(t) for p in region_re): return True
        if any(p.search(t) for p in speech_re): return True
        return False

    return is_valid


def search_videos(q, n=20):
    try:
        r = subprocess.run(
            ["yt-dlp", f"ytsearch{n}:{q}", "--get-id", "--no-warnings", "-q"],
            capture_output=True, text=True, timeout=30
        )
        ids = [l.strip() for l in r.stdout.strip().splitlines() if l.strip()]
        print(f"    yt-dlp '{q[:50]}' → {len(ids)} videos")
        return ids
    except Exception as e:
        print(f"    yt-dlp err: {e}")
        return []


def scrape_video(vid, dl, seen, is_valid):
    out = []
    try:
        gen = dl.get_comments_from_url(
            f"https://www.youtube.com/watch?v={vid}", sort_by=SORT_BY_TOP
        )
        for i, c in enumerate(gen):
            if i >= MAX_PER_VID: break
            t = c.get("text", "").strip()
            if t and t not in seen and is_valid(t):
                seen.add(t); out.append(t)
    except Exception as e:
        print(f"      [{vid}] {e}")
    return out


def scrape_web(src, seen, is_valid):
    out = []
    if not WEB: return out
    try:
        print(f"    🌐 {src['name']} ...", end=" ", flush=True)
        r = requests.get(src["url"], headers=HEADERS, timeout=12)
        if r.status_code != 200:
            print(f"HTTP {r.status_code}"); return out
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script","style","nav","footer","header"]):
            tag.decompose()
        for block in soup.find_all(["p","li","h2","h3"]):
            raw = block.get_text(" ", strip=True)
            for sent in re.split(r"[।\.\!\?\n]+", raw):
                s = sent.strip()
                if s and s not in seen and is_valid(s):
                    seen.add(s); out.append(s)
        print(f"+{len(out)}")
        time.sleep(2)
    except Exception as e:
        print(f"err: {e}")
    return out


def load_existing(path):
    """Load already-collected sentences to avoid re-scraping."""
    seen = set()
    if os.path.exists(path):
        with open(path, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                s = row.get("sentence","").strip()
                if s: seen.add(s)
    return seen


def save(sentences, key, outdir):
    rows = [{"id":i+1,"sentence":s,"dialect":key,"source":"youtube+web"}
            for i, s in enumerate(sentences)]
    out = os.path.join(BASE_RAW, outdir)
    os.makedirs(out, exist_ok=True)
    with open(f"{out}/{key}_final.json","w",encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    with open(f"{out}/{key}_final.csv","w",newline="",encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["id","sentence","dialect","source"])
        w.writeheader(); w.writerows(rows)
    print(f"\n  💾 {len(rows)} rows → {out}/{key}_final.csv")


# ════════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════════

def run_dialect(cfg, dl):
    key, label = cfg["key"], cfg["label"]
    outdir = cfg["outdir"]
    csv_path = os.path.join(BASE_RAW, outdir, f"{key}_final.csv")

    print(f"\n{'='*62}")
    print(f"  {label.upper()} SCRAPER")
    print(f"  Target: {TARGET} | Gujarati ≥ {int(cfg['min_guj']*100)}%")
    print(f"{'='*62}")

    is_valid = make_filters(cfg)

    # Load existing to deduplicate
    seen = load_existing(csv_path)
    coll = list(seen)
    print(f"  Loaded {len(seen)} existing rows")

    if len(coll) >= TARGET:
        print(f"  ✅ Already at {len(coll)}/{TARGET} — skipping"); return coll

    used = set()

    # Phase 1 — seed videos
    print(f"\n  ▶ Phase 1: {len(cfg['seed_videos'])} seed videos")
    for v in cfg["seed_videos"]:
        if len(coll) >= TARGET: break
        if v in used: continue
        used.add(v)
        new = scrape_video(v, dl, seen, is_valid)
        coll.extend(new)
        if new: print(f"    {v} → +{len(new)} | {len(coll)}/{TARGET}")
        time.sleep(1.5)

    # Phase 2 — yt-dlp search
    if len(coll) < TARGET:
        print(f"\n  ▶ Phase 2: yt-dlp search (need {TARGET-len(coll)} more)")
        for q in cfg["search_queries"]:
            if len(coll) >= TARGET: break
            for v in search_videos(q):
                if len(coll) >= TARGET: break
                if v in used: continue
                used.add(v)
                new = scrape_video(v, dl, seen, is_valid)
                coll.extend(new)
                if new: print(f"    {v} → +{len(new)} | {len(coll)}/{TARGET}")
                time.sleep(1.5)

    # Phase 3 — regional news sites
    if len(coll) < TARGET:
        print(f"\n  ▶ Phase 3: Regional web (need {TARGET-len(coll)} more)")
        for src in cfg["web_sources"]:
            if len(coll) >= TARGET: break
            coll.extend(scrape_web(src, seen, is_valid))

    save(coll, key, outdir)
    status = "✅" if len(coll) >= TARGET else f"⚠️  Short by {TARGET-len(coll)}"
    print(f"  {status}  {label}: {len(coll)}/{TARGET} collected")
    return coll


def main():
    print("\n" + "="*62)
    print("  TOP 4 GUJARATI DIALECT SCRAPER")
    print("  Standard Gujarati | Surti | Kathiawari | Charotari")
    print("="*62)
    dl = YoutubeCommentDownloader()
    summary = []
    for cfg in DIALECTS:
        coll = run_dialect(cfg, dl)
        summary.append((cfg["label"], len(coll)))

    print("\n" + "="*62)
    print("  FINAL SUMMARY")
    print("="*62)
    for label, n in summary:
        bar = "█" * (n // 25)
        status = "✅" if n >= TARGET else "⚠️"
        print(f"  {status} {label:<26} {n:>5}/{TARGET}  {bar}")
    print("="*62)


if __name__ == "__main__":
    main()
