#!/usr/bin/env python3
import json, html, os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "at_moral_final.json")
OUT = os.path.join(BASE, "index.html")
rows = json.load(open(SRC, encoding="utf-8"))

# compact payload: [ratio, likes, lib, author, title, id]
data = [[r["ratio"], r["likes"], r["library"], r.get("author") or "", r["title"], r["id"]] for r in rows]
payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
N = len(rows)

page = f"""<!DOCTYPE html>
<html lang="ru" data-theme="light">
<head>
<meta charset="utf-8">
<script>try{{var t=localStorage.getItem('amorale-theme');if(t)document.documentElement.dataset.theme=t;}}catch(e){{}}</script>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>А.Морале — альтернативный топ Author.Today</title>
<meta name="description" content="Рейтинг книг Author.Today по метрике А.Морале: лайки на одного заложившего в библиотеку.">
<style>
  :root{{
    --bg:#f6f7f9; --panel:#ffffff; --line:#e5e7eb; --txt:#16181d; --mut:#6b7280;
    --acc:#2563eb; --acc2:#b45309; --pos:#15803d; --rowhov:#f0f2f5;
  }}
  html[data-theme=dark]{{
    --bg:#0c0d10; --panel:#15171c; --line:#23262e; --txt:#e7e9ee; --mut:#8b909c;
    --acc:#7cc4ff; --acc2:#ffd166; --pos:#5ad19a; --rowhov:#12141a;
  }}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--bg);color:var(--txt);
    font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif;
    -webkit-font-smoothing:antialiased;transition:background .2s,color .2s}}
  .wrap{{position:relative;max-width:1080px;margin:0 auto;padding:40px 20px 80px}}
  .theme{{position:absolute;top:34px;right:20px;width:40px;height:40px;display:flex;
    align-items:center;justify-content:center;background:var(--panel);border:1px solid var(--line);
    border-radius:9px;cursor:pointer;color:var(--txt)}}
  .theme:hover{{border-color:var(--acc)}}
  .theme svg{{width:18px;height:18px}}
  h1{{font-size:30px;margin:0 0 6px;letter-spacing:-.02em}}
  .sub{{color:var(--mut);font-size:15px;margin:0 0 22px;max-width:760px}}
  .sub b{{color:var(--txt);font-weight:600}}
  .formula{{display:inline-block;background:var(--panel);border:1px solid var(--line);
    border-radius:8px;padding:8px 12px;margin:4px 0 24px;font-size:14px;color:var(--txt)}}
  .formula .mut{{color:var(--mut)}}
  .stats{{display:flex;gap:24px;flex-wrap:wrap;margin:0 0 22px;color:var(--mut);font-size:13px}}
  .stats b{{color:var(--txt);font-variant-numeric:tabular-nums}}
  .controls{{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:0 0 14px}}
  input[type=search]{{flex:1;min-width:220px;background:var(--panel);border:1px solid var(--line);
    border-radius:8px;color:var(--txt);padding:10px 13px;font-size:15px;outline:none}}
  input[type=search]:focus{{border-color:var(--acc)}}
  .hint{{color:var(--mut);font-size:13px}}
  table{{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}}
  thead th{{position:sticky;top:0;background:var(--bg);text-align:right;color:var(--mut);
    font-weight:500;font-size:12.5px;text-transform:uppercase;letter-spacing:.04em;
    padding:10px 10px;border-bottom:1px solid var(--line);cursor:pointer;white-space:nowrap;user-select:none}}
  thead th.l{{text-align:left}}
  thead th.active{{color:var(--acc)}}
  tbody td{{padding:9px 10px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}}
  tbody td.l{{text-align:left;white-space:normal}}
  tbody tr:hover{{background:var(--rowhov)}}
  .rank{{color:var(--mut);width:48px}}
  .mor{{color:var(--acc2);font-weight:700;font-size:15px}}
  .lk{{color:var(--pos)}}
  a.book{{color:var(--txt);text-decoration:none;border-bottom:1px solid transparent}}
  a.book:hover{{border-bottom-color:var(--mut)}}
  .auth{{color:var(--mut);font-size:13px}}
  .more{{display:block;margin:22px auto 0;background:var(--panel);border:1px solid var(--line);
    color:var(--txt);padding:11px 20px;border-radius:8px;cursor:pointer;font-size:14px}}
  .more:hover{{border-color:var(--acc)}}
  footer{{margin-top:48px;color:var(--mut);font-size:13px;line-height:1.7;border-top:1px solid var(--line);padding-top:20px}}
  footer a{{color:var(--acc)}}
  @media(max-width:640px){{
    h1{{font-size:24px}} .hide-m{{display:none}} .wrap{{padding:24px 14px 60px}}
  }}
</style>
</head>
<body>
<div class="wrap">
  <button class="theme" id="theme" aria-label="Сменить тему"></button>
  <h1>А.Морале</h1>
  <p class="sub">Альтернативный топ <b>Author.Today</b>: книги, ранжированные не по продажам и не по абсолютным лайкам, а по <b>преданности читателя</b> — сколько лайков приходится на одного заложившего книгу в библиотеку.</p>
  <div class="formula">А.Морале <span class="mut">=</span> лайки <span class="mut">÷</span> «в библиотеке» <span class="mut">×</span> 1000 &nbsp;<span class="mut">·</span>&nbsp; <span class="mut">только если в библиотеке ≥ 500</span></div>
  <div class="stats">
    <span>В рейтинге: <b id="ntotal">{N}</b> книг</span>
    <span>Показано: <b id="nshown">0</b></span>
    <span>Порог библиотеки: <b>≥ 500</b></span>
    <span>Данные: <b>25 июня 2026</b></span>
  </div>
  <div class="controls">
    <input type="search" id="q" placeholder="Поиск по автору или названию…" autocomplete="off">
    <span class="hint">клик по заголовку — сортировка</span>
  </div>
  <table>
    <thead><tr>
      <th class="l">#</th>
      <th data-k="0" class="active">А.Морале</th>
      <th data-k="1">Лайки</th>
      <th data-k="2">В библиотеке</th>
      <th class="l" data-k="4">Книга</th>
    </tr></thead>
    <tbody id="tb"></tbody>
  </table>
  <button class="more" id="more">Показать ещё 100</button>
  <footer>
    <p><b>Метод.</b> Перебран весь каталог Author.Today (свыше 249 000 произведений). Лайки и «Добавили в библиотеку» взяты из публичных данных сайта. После фильтра «в библиотеке ≥ 500» осталось {N} книг. Рейтинг полный: книга физически не может попасть выше, чем при всех лайкнувших среди заложивших.</p>
    <p>Идея метрики — Вадим Нестеров. Считал и собрал — по просьбе Аси Михеевой.</p>
  </footer>
</div>
<script>
const DATA={payload};
let view=DATA.map((r,i)=>[...r,i]); // append original-rank index
let sortK=0, sortDir=-1, shown=0, STEP=100;
const tb=document.getElementById('tb'), q=document.getElementById('q'),
      moreBtn=document.getElementById('more'), nshown=document.getElementById('nshown');
const fmt=n=>n==null?'':n.toLocaleString('ru-RU');
function render(reset){{
  if(reset){{tb.innerHTML='';shown=0;}}
  const end=Math.min(shown+STEP, view.length);
  let h='';
  for(let i=shown;i<end;i++){{
    const r=view[i]; // [ratio,likes,lib,author,title,id,origIdx]
    h+=`<tr><td class="l rank">${{r[6]+1}}</td>`+
       `<td class="mor">${{r[0].toLocaleString('ru-RU',{{minimumFractionDigits:1,maximumFractionDigits:1}})}}</td>`+
       `<td class="lk">${{fmt(r[1])}}</td>`+
       `<td>${{fmt(r[2])}}</td>`+
       `<td class="l"><a class="book" target="_blank" rel="noopener" href="https://author.today/work/${{r[5]}}">${{esc(r[4])}}</a>`+
       `<div class="auth">${{esc(r[3])}}</div></td></tr>`;
  }}
  tb.insertAdjacentHTML('beforeend',h);
  shown=end; nshown.textContent=fmt(shown);
  moreBtn.style.display = shown<view.length ? 'block':'none';
}}
function esc(s){{return (s||'').replace(/[&<>"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]));}}
function apply(){{
  const t=q.value.trim().toLowerCase();
  view = t ? DATA.map((r,i)=>[...r,i]).filter(r=>r[3].toLowerCase().includes(t)||r[4].toLowerCase().includes(t))
           : DATA.map((r,i)=>[...r,i]);
  view.sort((a,b)=>(a[sortK]>b[sortK]?1:a[sortK]<b[sortK]?-1:0)*sortDir);
  render(true);
}}
document.querySelectorAll('th[data-k]').forEach(th=>th.onclick=()=>{{
  const k=+th.dataset.k;
  if(k===sortK) sortDir*=-1; else {{sortK=k; sortDir = (k===4? 1 : -1);}}
  document.querySelectorAll('th').forEach(x=>x.classList.remove('active'));
  th.classList.add('active');
  apply();
}});
let deb; q.oninput=()=>{{clearTimeout(deb);deb=setTimeout(apply,160);}};
moreBtn.onclick=()=>render(false);
const root=document.documentElement, themeBtn=document.getElementById('theme');
const MOON='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
const SUN='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M6.3 17.7l-1.4 1.4M19.1 4.9l-1.4 1.4"/></svg>';
function paintTheme(){{ themeBtn.innerHTML = root.dataset.theme==='dark' ? SUN : MOON; }}
themeBtn.onclick=()=>{{
  root.dataset.theme = root.dataset.theme==='dark' ? 'light' : 'dark';
  try{{localStorage.setItem('amorale-theme', root.dataset.theme);}}catch(e){{}}
  paintTheme();
}};
paintTheme();
apply();
</script>
<script>
(function(){{
  try{{fetch('/api/hit',{{method:'POST',keepalive:true,headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{e:'v',ref:document.referrer||''}})}});}}catch(e){{}}
  var maxd=0,sent=false;
  function dnow(){{var h=document.documentElement;var s=window.scrollY+window.innerHeight;
    var t=h.scrollHeight||1;return Math.max(0,Math.min(100,Math.round(s/t*100)));}}
  maxd=dnow();
  window.addEventListener('scroll',function(){{var d=dnow();if(d>maxd)maxd=d;}},{{passive:true}});
  function send(){{if(sent)return;sent=true;
    try{{navigator.sendBeacon('/api/hit',JSON.stringify({{e:'d',depth:maxd}}));}}catch(e){{}}}}
  document.addEventListener('visibilitychange',function(){{if(document.visibilityState==='hidden')send();}});
  window.addEventListener('pagehide',send);
}})();
</script>
<noscript><img src="/api/hit?e=v" alt="" width="1" height="1" style="position:absolute;left:-9999px"></noscript>
</body>
</html>
"""
open(OUT, "w", encoding="utf-8").write(page)
print(f"wrote {OUT}  ({len(page)/1024:.0f} KB, {N} rows)")
