#!/usr/bin/env python3
"""Definitive A.Morale scan. Adaptive partition (genre -> +form -> +length)
to defeat the 10k per-query cap. A.Morale = likes/library*1000, library>=500."""
import json, time, os, urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
API = "https://api.author.today"; SITE = "https://author.today"
MIN_LIB, TOPK, FLOOR = 500, 200, 220
BASE = os.path.dirname(os.path.abspath(__file__))
LIBCACHE = f"{BASE}/libcache.jsonl"; WORKS = f"{BASE}/works_meta.json"
FINAL = f"{BASE}/at_moral_final.json"; LOG = f"{BASE}/final_scan.log"

GENRES = "fantasy romantic-fantasy fantasy-action urban-fantasy dark-fantasy ironical-fantasy boyar-anime heroic-fantasy epic-fantasy historical-fantasy magic-school everyday-fantasy classic-fantasy slavic-fantasy wuxia techno-fantasy paranormal modern-prose rusreal sci-fi sf-history sf-action sf-space sf-social science-fiction postapocalyptic sf-humor dystopia cyberpunk sf-heroic steampunk sf-romantic adventure historical-adventure poetry humor fanfiction horror popadantsy popadantsy-v-magicheskie-miry popadantsy-vo-vremeni back-to-ussr popadantsy-v-kosmos thriller other fairy-tale publicism drama detskaya-literatura non-fiction biznes-literatura action teen-prose detective detective-science-fiction historical-mystery spy-mystery litrpg romance contemporary-romance short-romance historical-romance realrpg historical-fiction erotica romantic-erotika fantasy-erotika sf-erotika fanfiction-erotika dorama".split()
FORMS = ["novel", "tale", "story", "story-book", "poetry", "translation"]
LENGTHS = [1250, 1000, 750, 500, 400, 300, 200, 100, 60, 20]

def logline(s):
    open(LOG, "a", encoding="utf-8").write(s + "\n"); print(s, flush=True)

def get(url, headers=None, retries=5):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            if i == retries - 1: return None
            time.sleep(0.8 * (i + 1))
    return None

HDR = {"Authorization": "Bearer guest"}
works = {}

def scan(qs):
    """Page a filtered slice by likes desc until below FLOOR/empty/cap. Return capped?"""
    page = 1; last = None
    while page <= 50:
        txt = get(f"{API}/v1/catalog/search?{qs}&sorting=likes&page={page}&ps=200", HDR)
        if not txt: break
        try: rs = json.loads(txt).get("searchResults", [])
        except Exception: break
        if not rs: return False
        for w in rs:
            works.setdefault(w["id"], {"id": w["id"], "title": w.get("title"),
                "author": w.get("authorFIO"), "authorUser": w.get("authorUserName"),
                "likes": w.get("likeCount") or 0, "views": w.get("viewCount")})
        last = rs[-1].get("likeCount", 0)
        if last < FLOOR: return False
        page += 1
    return last is not None and last >= FLOOR  # hit page-50 cap still above floor

def main():
    open(LOG, "w").close()
    t0 = time.time()
    for gi, g in enumerate(GENRES, 1):
        capped = scan(f"genre={g}")
        tag = "CAP" if capped else "ok"
        if capped:
            for form in FORMS:
                c2 = scan(f"genre={g}&form={form}")
                if c2:
                    for L in LENGTHS:
                        scan(f"genre={g}&form={form}&length={L}")
        logline(f"[{gi}/{len(GENRES)}] {g}: {tag} works={len(works)} el={time.time()-t0:.0f}s")
    json.dump(list(works.values()), open(WORKS, "w", encoding="utf-8"), ensure_ascii=False)
    logline(f"ENUM DONE: {len(works)} unique works el={time.time()-t0:.0f}s")

    # library cache (seed from prior rows + libcache)
    cache = {}
    p = f"{BASE}/at_moral_rows.jsonl"
    if os.path.exists(p):
        for l in open(p, encoding="utf-8"):
            try: r = json.loads(l); cache[r["id"]] = r["library"]
            except Exception: pass
    if os.path.exists(LIBCACHE):
        for l in open(LIBCACHE, encoding="utf-8"):
            try: r = json.loads(l); cache[r["id"]] = r["lib"]
            except Exception: pass
    need = [w["id"] for w in works.values() if w["id"] not in cache]
    logline(f"library: have {len(cache)}, need {len(need)}")

    def fetch(wid):
        txt = get(f"{SITE}/work/work-stats?workId={wid}")
        try: return wid, json.loads(txt).get("data", {}).get("totalCount")
        except Exception: return wid, None

    pool = ThreadPoolExecutor(max_workers=10)
    fc = open(LIBCACHE, "a", encoding="utf-8"); done = 0
    for wid, lib in pool.map(fetch, need):
        if lib is not None:
            cache[wid] = lib; fc.write(json.dumps({"id": wid, "lib": lib}) + "\n")
        done += 1
        if done % 2000 == 0:
            fc.flush(); logline(f"  fetched {done}/{len(need)} el={time.time()-t0:.0f}s")
    pool.shutdown(); fc.close()

    rows = []
    for w in works.values():
        lib = cache.get(w["id"])
        if lib is None or lib < MIN_LIB: continue
        rows.append({**w, "library": lib, "ratio": round(w["likes"]/lib*1000.0, 2),
                     "url": f"{SITE}/work/{w['id']}"})
    rows.sort(key=lambda r: r["ratio"], reverse=True)
    json.dump(rows, open(FINAL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    C = rows[TOPK-1]["ratio"] if len(rows) >= TOPK else None
    ok = (C is not None and 2*FLOOR >= C)
    logline(f"DONE: qualifying={len(rows)} cutoff200={C} complete(2*floor>=cutoff)={ok} "
            f"el={time.time()-t0:.0f}s")

if __name__ == "__main__":
    main()
