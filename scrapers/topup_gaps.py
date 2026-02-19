"""
topup_gaps.py
=============
Tops up Kathiawari (+23), Surti (+42), Charotari (+30)
to reach exactly 500 balanced rows each.

Reads existing _balanced.csv to know what's already collected,
then scrapes ONLY the shortfall needed. Appends to _balanced.csv.
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

BASE     = r"d:\Cross Lingual Project(gujarati)\data\raw"
TARGET   = 500
GUJ      = range(0x0A80, 0x0AFF+1)
HEADERS  = {"User-Agent":"Mozilla/5.0","Accept-Language":"gu,hi;q=0.9,en;q=0.5"}

def guj_ratio(t):
    ch=[c for c in t if not c.isspace()]; return sum(1 for c in ch if ord(c) in GUJ)/len(ch) if ch else 0

SPAM=[
    re.compile(r"jay\s*jay\s*garvi",re.I), re.compile(r"SB\s*Hindustani",re.I),
    re.compile(r"http[s]?://",re.I),       re.compile(r"subscribe.*karo",re.I),
    re.compile(r"^\d+$"),                  re.compile(r"^[a-zA-Z\s\d]{0,20}$"),
    re.compile(r"^[\U0001F300-\U0001FFFF\s]+$",re.UNICODE),
]

def quality_ok(t):
    t=t.strip()
    if not (15<=len(t)<=300): return False
    if guj_ratio(t)<0.50: return False
    return all(not p.search(t) for p in SPAM)

def load_seen(path):
    seen=set()
    if os.path.exists(path):
        with open(path,encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                s=r.get("sentence","").strip()
                if s: seen.add(s)
    return seen

def append_to_balanced(new_sents, key, outdir, existing_count):
    path=os.path.join(BASE,outdir,f"{key}_balanced.csv")
    rows=[{"id":existing_count+i+1,"sentence":s,"dialect":key,"source":"topup"}
          for i,s in enumerate(new_sents)]
    with open(path,"a",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=["id","sentence","dialect","source"])
        w.writerows(rows)
    return path

def search_videos(q,n=20):
    try:
        r=subprocess.run(["yt-dlp",f"ytsearch{n}:{q}","--get-id","--no-warnings","-q"],
                         capture_output=True,text=True,timeout=30)
        ids=[l.strip() for l in r.stdout.strip().splitlines() if l.strip()]
        print(f"    yt-dlp '{q[:48]}' → {len(ids)} videos"); return ids
    except Exception as e: print(f"    err:{e}"); return []

def scrape_video(vid,dl,seen,max_c=300):
    out=[]
    try:
        gen=dl.get_comments_from_url(f"https://www.youtube.com/watch?v={vid}",sort_by=SORT_BY_TOP)
        for i,c in enumerate(gen):
            if i>=max_c: break
            t=c.get("text","").strip()
            if t and t not in seen and quality_ok(t): seen.add(t); out.append(t)
    except Exception as e: print(f"      [{vid}] {e}")
    return out

def scrape_web(src,seen):
    out=[]
    if not WEB: return out
    try:
        print(f"    🌐 {src['name']}...",end=" ",flush=True)
        r=requests.get(src["url"],headers=HEADERS,timeout=12)
        if r.status_code!=200: print(f"HTTP{r.status_code}"); return out
        soup=BeautifulSoup(r.text,"html.parser")
        for tag in soup(["script","style","nav","footer","header"]): tag.decompose()
        for block in soup.find_all(["p","li","h2","h3"]):
            for s in re.split(r"[।\.\!\?\n]+",block.get_text(" ",strip=True)):
                s=s.strip()
                if s and s not in seen and quality_ok(s): seen.add(s); out.append(s)
        print(f"+{len(out)}"); time.sleep(2)
    except Exception as e: print(f"err:{e}")
    return out

# ── Dialect top-up configs ────────────────────────────────────────────────────
GAPS = [
    {
        "key":"kathiawari","label":"Kathiawari","outdir":"Kathiawari",
        "current":477, "need":23,
        "queries":[
            "Kathiawari comedy gujarati","Saurashtra dialect funny",
            "Rajkot local comedy gujarati","kathiawari boli funny",
            "Junagadh dialect funny","Bhavnagar comedy gujarati",
            "kathiawad dialect comedy","saurashtra comedy video",
        ],
        "web":[
            {"url":"https://www.divyabhaskar.co.in/local/gujarat/rajkot/","name":"DB Rajkot"},
            {"url":"https://sandesh.com/tag/saurashtra","name":"Sandesh Saurashtra"},
            {"url":"https://akilanews.com/category/rajkot/","name":"Akila Rajkot"},
        ],
    },
    {
        "key":"surti","label":"Surti","outdir":"Surti",
        "current":458, "need":42,
        "queries":[
            "Surti comedy gujarati","Surati Jokes gujarati",
            "Surat local comedy video","surti boli funny skit",
            "surat dialect funny video","surti bhasha jokes",
            "Poyri surti comedy","surat ni boli comedy",
        ],
        "web":[
            {"url":"https://www.divyabhaskar.co.in/local/gujarat/surat/","name":"DB Surat"},
            {"url":"https://sandesh.com/tag/surat","name":"Sandesh Surat"},
            {"url":"https://akilanews.com/category/surat/","name":"Akila Surat"},
            {"url":"https://www.gujaratmitra.in/","name":"Gujarat Mitra"},
        ],
    },
    {
        "key":"charotari","label":"Charotari","outdir":"Charotari",
        "current":470, "need":30,
        "queries":[
            "Charotari dialect comedy","Charotar funny gujarati",
            "Anand Kheda local comedy","charotari boli funny",
            "Nadiad local gujarati comedy","charotar local comedy",
            "anand comedy gujarati","charotari skit funny",
        ],
        "web":[
            {"url":"https://www.divyabhaskar.co.in/local/gujarat/anand/","name":"DB Anand"},
            {"url":"https://sandesh.com/tag/anand","name":"Sandesh Anand"},
            {"url":"https://akilanews.com/category/anand/","name":"Akila Anand"},
            {"url":"https://www.divyabhaskar.co.in/local/gujarat/kheda/","name":"DB Kheda"},
        ],
    },
]

def topup(cfg, dl):
    out_path=os.path.join(BASE,cfg["outdir"],f"{cfg['key']}_balanced.csv")
    seen=load_seen(out_path)
    coll=[]; used=set()
    need=cfg["need"]
    print(f"\n{'='*56}")
    print(f"  {cfg['label']}  — need {need} more rows  (have {cfg['current']}/500)")
    print(f"{'='*56}")

    for q in cfg["queries"]:
        if len(coll)>=need: break
        for v in search_videos(q):
            if len(coll)>=need: break
            if v in used: continue
            used.add(v)
            new=scrape_video(v,dl,seen)
            coll.extend(new)
            if new: print(f"    {v} → +{len(new)} | total new: {len(coll)}/{need}")
            time.sleep(1.5)

    if len(coll)<need:
        print(f"\n  ▶ Web fallback (need {need-len(coll)} more)")
        for src in cfg["web"]:
            if len(coll)>=need: break
            coll.extend(scrape_web(src,seen))

    final=coll[:need]
    if final:
        append_to_balanced(final,cfg["key"],cfg["outdir"],cfg["current"])
        print(f"\n  ✅ Appended {len(final)} rows → {os.path.basename(out_path)}")
        print(f"  Total now: {cfg['current']+len(final)}/500")
    else:
        print(f"  ⚠️ Got 0 new rows — try different search terms")
    return len(final)

def main():
    print("="*56)
    print("  TOP-UP SCRAPER — Filling gaps to 500 per dialect")
    print("="*56)
    dl=YoutubeCommentDownloader()
    summary=[]
    for cfg in GAPS:
        got=topup(cfg,dl)
        summary.append((cfg["label"],cfg["current"]+got))

    print("\n"+"="*56)
    print("  FINAL TALLY")
    print("="*56)
    for label,n in summary:
        icon="✅" if n>=TARGET else f"⚠️  ({TARGET-n} short)"
        print(f"  {icon}  {label:<22} {n:>5}/500")
    print("="*56)

if __name__=="__main__": main()
