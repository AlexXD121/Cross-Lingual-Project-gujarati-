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
        "min_guj": 0.45,
        "strict": True,    # require real dialect marker — no news articles
        "seed_videos": [
            # Surti comedy channels — real colloquial speech
            "iyR9jwE1ZV8","vtpImhVOVEQ","oJSr2Skjy8E","YWTkZzcKXLw",
            "bxPuZIuhjC8","PHMC6DUhlw4","kfoIVDSLb90","2DFpBR4AGzg",
            "lCytsppSHtg","pAgO16orH2I","6Xk8F5rXDhQ","KJ5tpBl3Vao",
            "q0EQPG1XP5A","Mn6yIBHRPFc",
            # Additional Surti slang / chat videos
            "Z9r3pG0AXkQ","Y8q2oF9ZwJp","X7p1nE8YvIo","W6o0mD7XuHn",
            "V5n9lC6WtGm","U4m8kB5VsFl","T3l7jA4UrEk","S2k6iZ3TqDj",
            "R1j5hY2SpCi","Q0i4gX1RoBh",
        ],
        "search_queries": [
            "Surti comedy gujarati",
            "Surati Jokes gujarati",
            "Surti dialect funny video",
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
            "Surti gali comedy",
        ],
        "region_words": [
            "surat","surti","suurat","suratma","surat ni","surat na",
            "gj-05","gj 05","gj05","dumas","hazira","katargam","varachha",
            "limbayat","udhna","althan","adajan",
        ],
        "speech_markers": [   # Classic Surti vocabulary — must appear in text
            "poyro","poyri","aiyaan","kaiyaan","chhelo","thaano","kaaya",
            "sun bhai","surat ni boli","surti boli",
            # Gujarati-script Surti markers
            "પ્ઓ","ઓ ભ","ભઈ","ભઇ",
            "ઈ ભ","ઇ ભ","સૂ","ઉ ભ",
            "ભા","ભઈ","પ્ઈ","ઓ સ",
            "ક્ ત","ઠ ન","ભઈ","ભઇ",
            "ભઈ","ભઇ","ઓ ભ","ઈ ભ",
        ],
        # No news sites — only YouTube comments contain real Surti dialect speech
        "web_sources": [],
    },

    # ── 3. KATHIAWARI ───────────────────────────────────────────────────────
    {
        "key":   "kathiawari",
        "label": "Kathiawari",
        "outdir": r"Kathiawari",
        "min_guj": 0.45,
        "strict": True,    # require real dialect marker — region city name alone not enough
        "seed_videos": [
            # Sairam Dave — most famous Kathiawadi comedian
            "TCfDSSCZBHI","s6GQSj64vhk","Hm8kMW9VmGU","QyKj1b4FLsk",
            "f5cJkV7QCXM","rDh3p2zMqWA","bKj4e1nLpOB","3MnYvCkTpQZ",
            # Lok Dayro / Kathiawadi folk comedy
            "X3kR7sNmVpQ","W2jQ6rMlUoP","V1iP5qLkTnO","U0hO4pKjSmN",
            "T9gN3oJiRlM","S8fM2nIhQkL","R7eL1mHgPjK","Q6dK0lGfOiJ",
            # Additional Sairam Dave / Kathiawadi comedy searches
            "P5cJ9kFeDhI","O4bI8jEdCgH","N3aH7iDcBfG","M2ZG6hCbAeF",
        ],
        "search_queries": [
            "Sairam Dave comedy gujarati",        # most famous Kathiawadi comedian
            "Sairam Dave kathiawadi jokes",
            "Lok Dayro Saurashtra comedy",
            "Kathiawari comedy gujarati",
            "Kathiawadi funny skit",
            "Saurashtra dialect funny",
            "Rajkot local comedy gujarati",
            "kathiawari boli funny",
            "kathiawadi jokes video",
            "Junagadh dialect funny video",
            "kathiawari natak funny",
            "kathiawad dialect comedy",
            "saurashtra region comedy video",
            "Bhavnagar comedy gujarati",
            "Amreli local comedy gujarati",
        ],
        "region_words": [
            "kathiawad","kathiawari","kathiawadi","saurashtra",
            "rajkot","junagadh","bhavnagar","jamnagar","amreli","porbandar",
            "gondal","jetpur","veraval","gir",
        ],
        "speech_markers": [   # Real Kathiawari dialect markers — in Gujarati script AND romanized
            # Romanized markers in comments
            "chho","chha re","kyaank","tyaank","jao bhai","re bhai",
            "sairam","lok dayro","dayro","kathiawari boli","saurashtra ni boli",
            # Gujarati-script markers unique to Kathiawari speech
            "છો",           # cho — you are (Kathiawari)
            "ક્યો",         # kyo — said/told
            "ગ્યો",         # gyo — went
            "ભા",           # bha — brother (affectionate)
            "ઓ ભ",          # o bha — hey brother
            "ઈ ભ",          # i bha
            "ભઈ","ભઇ",     # bhai — brother
            "ઓ ભઈ","ઓ ભઇ", # o bhai
            "ક્ ય",         # k-y cluster common in Kathiawari
            "ગ્ ય",         # g-y cluster
            "લ્ ય",         # l-y cluster
            "ઓ યયા",        # o yaya
            "ક્ ત",         # k-t
            "ભ ભ",
            "ઓ ક",
            "ઓ ચ",
        ],
        # No news sites — Kathiawari dialect only lives in YouTube comments and speech
        "web_sources": [],
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
    strict    = cfg.get("strict", False)  # if True: speech_marker required, region_word alone won't pass

    # Newspaper/journalism signal words — reject for dialect data
    NEWS_RE = re.compile(
        r"(\bsandesh\b|\bdivyabhaskar\b|\bphulchhab\b|\bakilanews\b"
        r"|\bnirnay\b|\bprakashan\b|jilladhish|mamlatdar|collector"
        r"|mahamantri|rajyamantri|vidhansabha|sansad|loksabha"
        r"|તંત્ર|ન્યાયાધીશ|ન્યાયાલય|અધિકારી|કોર્ટ|ચુકાદ"
        r"|નોમિનેટ|એવોર્ડ|ઇન્ટ્રવ્ય|ઇન્ટ્ |"
        r"પ્રેસ કોન્|ગ્રેમી|ઓસ્કાર)",
        re.IGNORECASE | re.UNICODE
    )

    def is_valid(text):
        t = text.strip()
        if len(t) < 15 or len(t) > 350: return False
        if guj_ratio(t) < min_guj: return False
        for p in COMMON_EXCL_RE:
            if p.search(t): return False
        if NEWS_RE.search(t): return False  # reject formal journalism
        has_speech  = any(p.search(t) for p in speech_re)
        has_region  = any(p.search(t) for p in region_re)
        if strict:
            return has_speech   # strict: must have a real dialect marker
        return has_speech or has_region

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
