#!/usr/bin/env python3
"""Generate amorale weekly RSS feed (feed.xml) with a digest item.
Diffs current ranking vs previous snapshot; emits entrants + climbers.
RSS-to-email services turn each new <item> into an email automatically."""
import json, os, html, datetime, sys, re

BASE = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.join(BASE, "at_moral_final.json")
PREV = os.path.join(BASE, "prev_top.json")
FEED = os.path.join(BASE, "feed.xml")
SITE = "https://amorale.lance.ru"
TOPN = 100          # "топ" we track entrants for
SNAP = 1500         # how many ranks we remember for climb detection
KEEP_ITEMS = 24     # max items kept in feed

MONTHS = ["", "января", "февраля", "марта", "апреля", "мая", "июня",
          "июля", "августа", "сентября", "октября", "ноября", "декабря"]

def esc(s): return html.escape(str(s or ""), quote=True)

def load_json(p, d):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return d

def rfc822(dt):
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    mon = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{days[dt.weekday()]}, {dt.day:02d} {mon[dt.month]} {dt.year} {dt:%H:%M:%S} +0000"

def build_digest_html(rows, prev):
    cur = {r["id"]: i + 1 for i, r in enumerate(rows)}
    top = rows[:TOPN]
    first_run = not prev
    parts = []
    if first_run:
        parts.append(f"<p>Запущен альтернативный топ Author.Today по метрике <b>А.Морале</b> — "
                     f"лайки на одного заложившего книгу в библиотеку (только при ≥500 в библиотеке). "
                     f"Сейчас в рейтинге <b>{len(rows)}</b> книг.</p>")
    else:
        prev_rank = {int(k): v["rank"] for k, v in prev.items()}
        # entrants into top-N
        entrants = [r for r in top if prev_rank.get(r["id"], 10**9) > TOPN]
        # climbers: improved rank the most (within current top SNAP)
        climbers = []
        for i, r in enumerate(rows[:SNAP]):
            pr = prev_rank.get(r["id"])
            if pr:
                delta = pr - (i + 1)
                if delta > 0:
                    climbers.append((delta, i + 1, pr, r))
        climbers.sort(reverse=True, key=lambda x: x[0])
        if entrants:
            parts.append("<p><b>Новые в топ-100 за неделю:</b></p><ul>" + "".join(
                f"<li>#{cur[r['id']]} · А.Морале {r['ratio']:.0f} — "
                f"<a href=\"{SITE}\">{esc(r['title'])}</a> <i>({esc(r['author'])})</i></li>"
                for r in entrants[:10]) + "</ul>")
        if climbers:
            parts.append("<p><b>Сильнее всех поднялись:</b></p><ul>" + "".join(
                f"<li>{esc(r['title'])} — +{d} мест (#{pr}→#{nr}), А.Морале {r['ratio']:.0f}</li>"
                for d, nr, pr, r in climbers[:8]) + "</ul>")
        if not entrants and not climbers:
            parts.append("<p>За неделю топ-100 без заметных движений — лидеры держатся.</p>")
    # always: current top-10
    parts.append("<p><b>Топ-10 сейчас:</b></p><ol>" + "".join(
        f"<li>А.Морале {r['ratio']:.0f} — <a href=\"{SITE}\">{esc(r['title'])}</a> "
        f"<i>({esc(r['author'])})</i> · {r['likes']}❤ / {r['library']} в библ.</li>"
        for r in rows[:10]) + "</ol>")
    parts.append(f'<p style="margin-top:18px"><a href="{SITE}">Весь рейтинг на amorale.lance.ru →</a></p>')
    return "\n".join(parts)

def existing_items(feedpath):
    if not os.path.exists(feedpath):
        return []
    txt = open(feedpath, encoding="utf-8").read()
    return re.findall(r"<item>.*?</item>", txt, re.S)

def main():
    now = datetime.datetime.utcnow()
    # allow date override for deterministic runs: argv[1] = YYYY-MM-DD
    if len(sys.argv) > 1:
        try: now = datetime.datetime.strptime(sys.argv[1], "%Y-%m-%d")
        except Exception: pass
    rows = load_json(FINAL, [])
    if not rows:
        print("no ranking data, abort"); return
    prev = load_json(PREV, {})

    title = (f"А.Морале — запуск рейтинга" if not prev
             else f"А.Морале — обновление {now.day} {MONTHS[now.month]}")
    desc = build_digest_html(rows, prev)
    guid = f"{SITE}/#update-{now:%Y-%m-%d}"
    item = (f"<item>\n<title>{esc(title)}</title>\n<link>{SITE}</link>\n"
            f"<guid isPermaLink=\"false\">{guid}</guid>\n<pubDate>{rfc822(now)}</pubDate>\n"
            f"<description><![CDATA[{desc}]]></description>\n</item>")

    items = [item] + existing_items(FEED)
    items = items[:KEEP_ITEMS]
    feed = (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n<channel>\n'
            f'<title>А.Морале — альтернативный топ Author.Today</title>\n'
            f'<link>{SITE}</link>\n'
            f'<description>Еженедельный дайджест рейтинга книг Author.Today по преданности читателя.</description>\n'
            f'<language>ru</language>\n<lastBuildDate>{rfc822(now)}</lastBuildDate>\n'
            + "\n".join(items) + "\n</channel>\n</rss>\n")
    open(FEED, "w", encoding="utf-8").write(feed)

    # save snapshot for next diff
    snap = {str(r["id"]): {"rank": i + 1, "ratio": r["ratio"]} for i, r in enumerate(rows[:SNAP])}
    json.dump(snap, open(PREV, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"feed.xml written: {len(items)} item(s); snapshot {len(snap)} ranks; first_run={not prev}")

if __name__ == "__main__":
    main()
