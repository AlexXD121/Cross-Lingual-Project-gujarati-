"""
rescrape_kath_surti.py
======================
Targeted rescrape ONLY for Kathiawari and Surti — using the fixed
strict-mode filters from scrape_top4.py.

Pulls from search_queries only (yt-dlp) since seed_video IDs need to be real.
After this finishes, run build_dataset.py to rebuild gujarati_dialects.csv.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from scrape_top4 import DIALECTS, make_filters, search_videos, scrape_video, save
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR as SORT_BY_TOP
import time

TARGET = 500

def run(cfg, dl):
    key, label = cfg["key"], cfg["label"]
    print(f"\n{'='*55}")
    print(f"  {label.upper()}  (strict={cfg.get('strict', False)})")
    print(f"{'='*55}")

    is_valid = make_filters(cfg)
    seen = set()
    coll = []

    # Phase 1 — seed videos (valid ones will yield comments; invalid silently fail)
    print(f"\n  Phase 1: {len(cfg['seed_videos'])} seed videos")
    for v in cfg["seed_videos"]:
        if len(coll) >= TARGET: break
        new = scrape_video(v, dl, seen, is_valid)
        if new:
            coll.extend(new)
            print(f"    {v} → +{len(new)} | {len(coll)}/{TARGET}")
        time.sleep(1)

    # Phase 2 — yt-dlp search queries
    if len(coll) < TARGET:
        print(f"\n  Phase 2: Search queries (need {TARGET - len(coll)} more)")
        for q in cfg["search_queries"]:
            if len(coll) >= TARGET: break
            for v in search_videos(q, n=25):
                if len(coll) >= TARGET: break
                new = scrape_video(v, dl, seen, is_valid)
                if new:
                    coll.extend(new)
                    print(f"    {v} → +{len(new)} | {len(coll)}/{TARGET}")
                time.sleep(1)

    status = "OK" if len(coll) >= TARGET else f"SHORT by {TARGET - len(coll)}"
    print(f"\n  {label}: {len(coll)}/{TARGET} — {status}")
    if coll:
        save(coll, key, cfg["outdir"])
    return coll


def main():
    dl = YoutubeCommentDownloader()
    targets = [d for d in DIALECTS if d["key"] in ("kathiawari", "surti")]
    for cfg in targets:
        run(cfg, dl)

    print("\n\nDone. Now run:")
    print("  python scrapers\\build_dataset.py")
    print("to rebuild gujarati_dialects.csv and retrain.")

if __name__ == "__main__":
    main()
