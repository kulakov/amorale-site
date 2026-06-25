# amorale-site

Альтернативный топ Author.Today по метрике **А.Морале** — лайки на одного заложившего книгу в библиотеку (при ≥500 в библиотеке).

Живёт на **https://amorale.lance.ru** (Vercel, статика + serverless-функции).

## Состав
- `scan.py` — перебирает каталог Author.Today (по жанрам/форме/объёму, обходит лимит 10k), считает А.Морале → `at_moral_final.json`.
- `build.py` — рендерит `index.html` (вся таблица + поиск/сортировка + переключатель темы).
- `feed.py` — `feed.xml`: недельный RSS-дайджест (новые в топ-100, кто поднялся). RSS-to-email сервиса (Sender) превращает каждый новый `<item>` в письмо.
- `api/hit.js` — невидимый счётчик визитов/referrer/глубины скролла → приватный gist.
- `api/stats.js` — `amorale.lance.ru/stats` под Basic-Auth, своя аналитика посещений.

## Еженедельный апдейт
`.github/workflows/weekly.yml` (понедельник 06:17 UTC): `scan → build → feed → commit → deploy`.
Запустить вручную: Actions → weekly-update → Run workflow (есть флаг `skip_scan` для пересборки без скрейпа).

### Секреты репозитория
- `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` — деплой на Vercel.

Метрику предложил Вадим Нестеров; собрано по просьбе Аси Михеевой.
