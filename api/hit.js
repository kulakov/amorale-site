// Visit counter + referrer + scroll depth. Stores in a private GitHub gist.
const crypto = require('crypto');

const GIST_ID = process.env.GIST_ID;
const GH = process.env.GH_TOKEN;
const SALT = process.env.IP_SALT || 'amorale-salt';
const FILE = 'amorale_counter.json';
const API = `https://api.github.com/gists/${GIST_ID}`;
const GIF = Buffer.from('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7', 'base64');
const BOT = /bot|crawl|spider|slurp|bing|yandex|baidu|duckduck|facebookexternal|whatsapp|telegrambot|preview|monitor|headless|curl|wget|python-requests|node-fetch|axios|vercel|lighthouse|pingdom|uptime|ahrefs|semrush/i;
const SELF = 'amorale.lance.ru';

function ghHeaders() {
  return { Authorization: `Bearer ${GH}`, 'User-Agent': 'amorale-counter', Accept: 'application/vnd.github+json' };
}
function cleanRef(ref) {
  if (!ref) return '(прямой / без реферера)';
  let s = String(ref).replace(/^https?:\/\//i, '').replace(/\/$/, '');
  try { if (s.split('/')[0].toLowerCase().includes(SELF)) return '(внутренний переход)'; } catch (e) {}
  return s.slice(0, 120);
}
function readRaw(req) {
  return new Promise((resolve) => {
    let b = ''; req.on('data', (c) => (b += c)); req.on('end', () => resolve(b)); req.on('error', () => resolve(''));
  });
}

module.exports = async (req, res) => {
  res.setHeader('Content-Type', 'image/gif');
  res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0');
  try {
    const ua = req.headers['user-agent'] || '';
    if (BOT.test(ua) || !GIST_ID || !GH) { res.end(GIF); return; }

    // parse payload — read raw (bodyParser disabled) so any content-type parses the same
    let body = {};
    if (req.method !== 'GET') {
      const raw = await readRaw(req);
      try { body = JSON.parse(raw); } catch (e) { body = {}; }
    }
    const ev = body.e || 'v';

    const r = await fetch(API, { headers: ghHeaders() });
    const j = await r.json();
    const data = JSON.parse(j.files[FILE].content);
    data.total = data.total || 0;
    data.days = data.days || {};
    data.refs = data.refs || {};
    data.depth = data.depth || {}; // bucket index 0..9 => count

    if (ev === 'd') {
      let d = Number(body.depth); if (!isFinite(d)) d = 0;
      const idx = Math.max(0, Math.min(9, Math.floor(d / 10)));
      data.depth[idx] = (data.depth[idx] || 0) + 1;
    } else {
      const day = new Date().toISOString().slice(0, 10);
      const ip = (req.headers['x-forwarded-for'] || '').split(',')[0].trim()
              || req.headers['x-real-ip'] || (req.socket && req.socket.remoteAddress) || '';
      const iph = crypto.createHash('sha256').update(SALT + ip).digest('hex').slice(0, 12);
      data.total += 1;
      const dd = data.days[day] || (data.days[day] = { h: 0, u: [] });
      dd.h += 1; if (!dd.u.includes(iph)) dd.u.push(iph);
      const refKey = cleanRef(body.ref != null ? body.ref : req.headers['referer'] || '');
      data.refs[refKey] = (data.refs[refKey] || 0) + 1;
    }

    await fetch(API, {
      method: 'PATCH',
      headers: { ...ghHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ files: { [FILE]: { content: JSON.stringify(data) } } }),
    });
  } catch (e) { /* never break the page */ }
  res.end(GIF);
};

module.exports.config = { api: { bodyParser: false } };
