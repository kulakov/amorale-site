// Password-protected stats: visits, referrers, scroll depth. Reads the private gist.
const GIST_ID = process.env.GIST_ID;
const GH = process.env.GH_TOKEN;
const USER = process.env.STATS_USER || 'lance';
const PASS = process.env.STATS_PASS || '';
const FILE = 'amorale_counter.json';

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

module.exports = async (req, res) => {
  const expected = 'Basic ' + Buffer.from(`${USER}:${PASS}`).toString('base64');
  if (!PASS || (req.headers.authorization || '') !== expected) {
    res.setHeader('WWW-Authenticate', 'Basic realm="amorale stats"');
    res.statusCode = 401;
    res.end('Требуется авторизация');
    return;
  }

  let data = { total: 0, days: {}, refs: {}, depth: {} };
  try {
    const r = await fetch(`https://api.github.com/gists/${GIST_ID}`, {
      headers: { Authorization: `Bearer ${GH}`, 'User-Agent': 'amorale-counter' },
    });
    const j = await r.json();
    data = Object.assign(data, JSON.parse(j.files[FILE].content));
  } catch (e) { /* zeros */ }

  const days = Object.entries(data.days || {}).sort((a, b) => (a[0] < b[0] ? 1 : -1));
  const uniqAll = new Set([].concat(...days.map(([, d]) => d.u || []))).size;
  const dayRows = days.map(([day, d]) =>
    `<tr><td>${day}</td><td>${d.h}</td><td>${(d.u || []).length}</td></tr>`).join('');

  const refs = Object.entries(data.refs || {}).sort((a, b) => b[1] - a[1]);
  const refMax = refs.length ? refs[0][1] : 1;
  const refRows = refs.map(([k, v]) =>
    `<tr><td class=lab title="${esc(k)}">${esc(k)}</td><td>${v}</td>
     <td class=barcell><span class=bar style="width:${Math.round(v / refMax * 100)}%"></span></td></tr>`).join('');

  const depth = data.depth || {};
  const depthSamples = Object.values(depth).reduce((a, b) => a + b, 0);
  const depthMax = Math.max(1, ...Object.values(depth).map(Number));
  const reachedEnd = depth['9'] || 0;
  const depthRows = Array.from({ length: 10 }, (_, i) => {
    const c = depth[i] || 0;
    return `<tr><td>${i * 10}–${i * 10 + 10}%</td><td>${c}</td>
      <td class=barcell><span class=bar style="width:${Math.round(c / depthMax * 100)}%"></span></td></tr>`;
  }).reverse().join('');

  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.end(`<!doctype html><html lang=ru><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>amorale · статистика</title>
<style>body{font:15px/1.5 -apple-system,system-ui,sans-serif;margin:44px auto;max-width:720px;
padding:0 18px;color:#16181d}h1{font-size:21px;margin:0 0 4px}h2{font-size:15px;text-transform:uppercase;
letter-spacing:.04em;color:#6b7280;margin:34px 0 8px;font-weight:600}.big{font-size:38px;font-weight:700;margin:14px 0 2px}
.mut{color:#6b7280}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
td,th{padding:7px 10px;border-bottom:1px solid #eceef1;text-align:right}td:first-child,th:first-child{text-align:left}
th{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#6b7280;font-weight:500}
.lab{max-width:360px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.barcell{width:34%}.bar{display:inline-block;height:9px;border-radius:5px;background:#2563eb;min-width:2px}</style>
<h1>amorale.lance.ru — статистика</h1>
<div class=big>${data.total || 0}</div>
<div class=mut>всего заходов · ${uniqAll} уникальных (по хэшу IP)</div>

<h2>Глубина прокрутки</h2>
<div class=mut style="margin-bottom:6px">Дочитали до конца (90–100%): <b>${reachedEnd}</b> из ${depthSamples} замеров${depthSamples ? ` · ${Math.round(reachedEnd / depthSamples * 100)}%` : ''}</div>
<table><thead><tr><th>Докуда доскроллили</th><th>Визиты</th><th></th></tr></thead><tbody>${depthRows}</tbody></table>

<h2>Откуда пришли</h2>
<table><thead><tr><th>Источник (referrer)</th><th>Заходы</th><th></th></tr></thead>
<tbody>${refRows || '<tr><td colspan=3 class=mut>пока пусто</td></tr>'}</tbody></table>

<h2>По дням</h2>
<table><thead><tr><th>День (UTC)</th><th>Заходы</th><th>Уник.</th></tr></thead>
<tbody>${dayRows || '<tr><td colspan=3 class=mut>пока пусто</td></tr>'}</tbody></table>

<p class=mut style="margin-top:24px;font-size:13px">Невидимый трекер на странице. Боты отфильтрованы. Глубина — максимум прокрутки за визит, шлётся при уходе. Многие переходы из Telegram/приложений приходят без referrer → «прямой».</p>
</html>`);
};
