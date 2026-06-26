#!/usr/bin/env python3
"""Scan Author.Today and rank by A.Morale = likes/library*1000 (library>=500).
Includes 18+ content when authenticated. Auth resolution (for the weekly cron):
  1. AT_LOGIN + AT_PASSWORD env -> login-by-password -> fresh token (self-refreshing)
  2. AT_TOKEN env -> use as-is (expires ~24h, manual)
  3. else 'guest' -> WARNING: 18+ excluded.
Parallel wave enumeration at low concurrency to avoid the per-user tarpit;
work-stats (library counts) hit the public site endpoint at higher concurrency."""
import json, os, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
API = "https://api.author.today"; SITE = "https://author.today"
FLOOR, MIN_LIB, TOPK = 220, 500, 200
LIBCACHE = f"{BASE}/libcache.jsonl"; FINAL = f"{BASE}/at_moral_final.json"; LOG = f"{BASE}/scan.log"
ENUM_WORKERS, STAT_WORKERS = 3, 10

GENRES = "fantasy romantic-fantasy fantasy-action urban-fantasy dark-fantasy ironical-fantasy boyar-anime heroic-fantasy epic-fantasy historical-fantasy magic-school everyday-fantasy classic-fantasy slavic-fantasy wuxia techno-fantasy paranormal modern-prose rusreal sci-fi sf-history sf-action sf-space sf-social science-fiction postapocalyptic sf-humor dystopia cyberpunk sf-heroic steampunk sf-romantic adventure historical-adventure poetry humor fanfiction horror popadantsy popadantsy-v-magicheskie-miry popadantsy-vo-vremeni back-to-ussr popadantsy-v-kosmos thriller other fairy-tale publicism drama detskaya-literatura non-fiction biznes-literatura action teen-prose detective detective-science-fiction historical-mystery spy-mystery litrpg romance contemporary-romance short-romance historical-romance realrpg historical-fiction erotica romantic-erotika fantasy-erotika sf-erotika fanfiction-erotika dorama".split()
FORMS = ["novel", "tale", "story", "story-book", "poetry", "translation"]
LENGTHS = [1250, 1000, 750, 500, 400, 300, 200, 100, 60, 20]

def logline(s):
    open(LOG, "a", encoding="utf-8").write(s + "\n"); print(s, flush=True)

def _post(url, payload, token):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, method="POST",
        headers={"User-Agent": UA, "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def resolve_token():
    login, pw = os.environ.get("AT_LOGIN"), os.environ.get("AT_PASSWORD")
    if login and pw:
        try:
            d = _post(f"{API}/v1/account/login-by-password", {"login": login, "password": pw}, "guest")
            tok = d.get("token")
            if tok:
                logline("auth: logged in via AT_LOGIN/AT_PASSWORD (18+ included)"); return tok
            logline(f"auth: login response had no token ({list(d)[:5]}); falling back")
        except Exception as e:
            logline(f"auth: login-by-password failed ({e}); falling back")
    if os.environ.get("AT_TOKEN"):
        logline("auth: using AT_TOKEN env (18+ included)"); return os.environ["AT_TOKEN"].strip()
    logline("auth: WARNING — no credentials, using guest token; 18+ content WILL be excluded")
    return "guest"

TOKEN = resolve_token()
HDR = {"User-Agent": UA, "Authorization": f"Bearer {TOKEN}"}

def get(url, retries=6):
    for i in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=45) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            if i == retries - 1: return None
            time.sleep(1.2 * (i + 1))
    return None

def scan_query(qs):
    out, page, last = [], 1, None
    while page <= 50:
        txt = get(f"{API}/v1/catalog/search?{qs}&sorting=likes&ps=200&page={page}")
        if not txt: break
        try: rs = json.loads(txt).get("searchResults", [])
        except Exception: break
        if not rs: return out, False
        for w in rs:
            out.append({"id": w["id"], "title": w.get("title"), "author": w.get("authorFIO"),
                        "authorUser": w.get("authorUserName"), "likes": w.get("likeCount") or 0,
                        "views": w.get("viewCount"), "adult": w.get("adultOnly")})
        last = rs[-1].get("likeCount", 0)
        if last < FLOOR: return out, False
        page += 1
    return out, (last is not None and last >= FLOOR)

def main():
    open(LOG, "w").close(); t0 = time.time()
    works = {}
    def add(ws):
        for w in ws: works.setdefault(w["id"], w)
        return True
    pool = ThreadPoolExecutor(max_workers=ENUM_WORKERS)

    r1 = list(pool.map(scan_query, [f"genre={g}" for g in GENRES]))
    capped = [g for g, (ws, cap) in zip(GENRES, r1) if (add(ws) and cap)]
    logline(f"wave1: {len(works)} works, capped={capped} el={time.time()-t0:.0f}s")

    t2 = [(g, f) for g in capped for f in FORMS]
    r2 = list(pool.map(lambda t: scan_query(f"genre={t[0]}&form={t[1]}"), t2))
    capped2 = [t for t, (ws, cap) in zip(t2, r2) if (add(ws) and cap)]
    logline(f"wave2: {len(works)} works, capped2={len(capped2)} el={time.time()-t0:.0f}s")

    t3 = [(g, f, L) for (g, f) in capped2 for L in LENGTHS]
    r3 = list(pool.map(lambda t: scan_query(f"genre={t[0]}&form={t[1]}&length={t[2]}"), t3))
    for ws, _ in r3: add(ws)
    logline(f"wave3: {len(works)} works ({sum(1 for w in works.values() if w.get('adult'))} adult) el={time.time()-t0:.0f}s")

    cache = {}
    if os.path.exists(LIBCACHE):
        for l in open(LIBCACHE, encoding="utf-8"):
            try: r = json.loads(l); cache[r["id"]] = r["lib"]
            except Exception: pass
    need = [w["id"] for w in works.values() if w["id"] not in cache]
    logline(f"library: cached {len(cache)}, fetching {len(need)} el={time.time()-t0:.0f}s")
    def fetch(wid):
        txt = get(f"{SITE}/work/work-stats?workId={wid}")
        try: return wid, json.loads(txt).get("data", {}).get("totalCount")
        except Exception: return wid, None
    spool = ThreadPoolExecutor(max_workers=STAT_WORKERS)
    fc = open(LIBCACHE, "a", encoding="utf-8")
    for wid, lib in spool.map(fetch, need):
        if lib is not None:
            cache[wid] = lib; fc.write(json.dumps({"id": wid, "lib": lib}) + "\n")
    fc.close(); spool.shutdown(); pool.shutdown()

    rows = []
    for w in works.values():
        lib = cache.get(w["id"])
        if lib is None or lib < MIN_LIB: continue
        rows.append({"id": w["id"], "title": w["title"], "author": w["author"],
                     "authorUser": w["authorUser"], "likes": w["likes"], "library": lib,
                     "views": w["views"], "adult": bool(w.get("adult")),
                     "ratio": round(w["likes"] / lib * 1000.0, 2), "url": f"{SITE}/work/{w['id']}"})
    rows.sort(key=lambda r: r["ratio"], reverse=True)
    json.dump(rows, open(FINAL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    C = rows[TOPK-1]["ratio"] if len(rows) >= TOPK else None
    logline(f"DONE: qualifying={len(rows)} (adult={sum(1 for r in rows if r['adult'])}) "
            f"cutoff200={C} complete={2*FLOOR <= (C or 0)} el={time.time()-t0:.0f}s")

if __name__ == "__main__":
    main()
