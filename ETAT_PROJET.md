# Pulse Listen — Etat du projet

> Clone de l'archi **Pulse by Coca-Cola** (FastAPI + Next.js) applique au social
> listening **sodas / sucre / alternatives / wellness** sur Bluesky.

## Avancement (au 2026-06-16) — TERMINE

| Etape | Statut |
|-------|--------|
| Structure backend/ + frontend/ | OK |
| Backend : sentiment (VADER) + storage (SQLite) | OK |
| Backend : collecteur bulk `searchPosts` (no auth) | OK |
| **Collecte dataset reel** | **OK — 1300 posts en base** |
| Backend : agregation tendances + forecast honnete | OK |
| Backend : API FastAPI (endpoints) | OK |
| Frontend : Next.js dashboard | **OK — `npm install` fait, dev teste 200** |
| Test bout-en-bout + README | **OK — README.md, E2E valide** |

> Projet complet et fonctionnel. Voir `README.md` pour le mode d'emploi.

## Donnees reelles collectees

- **1300 posts** Bluesky reels, **~142 jours d'historique**
- Sentiment moyen global : **0.21** (plutot positif)
- Repartition : 688 positifs / 292 neutres / 297 negatifs
- Par theme : Alternatives 560 · Sodas 393 · Bien-etre 190 · Sucre 134
- Base : `backend/data_storage/posts.db`

## Decouverte cle (technique)

`api.bsky.app` autorise `app.bsky.feed.searchPosts` **SANS auth** (HTTP 200 +
curseur). `public.api.bsky.app` renvoie 403. La page 2 de pagination est
souvent rate-limited (403) → on recupere ~1 page utile par mot-cle, suffisant.

## Comment relancer demain

### 1. Backend (API)
```bash
cd /Users/fouadouddene/Documents/pulse-listen/backend
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# -> http://127.0.0.1:8000  (health, /overview, /timeline, /trend, /forecast, /top-posts)
```
(venv deja cree avec : requests, vaderSentiment, pandas, numpy, fastapi, uvicorn)

### 2. Re-collecter plus de donnees (optionnel)
```bash
cd /Users/fouadouddene/Documents/pulse-listen/backend
.venv/bin/python -m app.data.collect_bulk --pages 4 --limit 100
```

### 3. Frontend (PROCHAINE ETAPE — reprendre ici)
```bash
cd /Users/fouadouddene/Documents/pulse-listen/frontend
npm install        # <-- a relancer (interrompu hier)
npm run dev        # -> http://localhost:3000
```
> Note : `npm install` a ete interrompu (exit 137 = OOM/kill). Relancer a froid,
> fermer d'autres apps lourdes si besoin. Tout le code TS/TSX est deja ecrit.

## Fichiers cles

**Backend**
- `app/data/zones.py` — 4 themes, 31 mots-cles, filtres (LANG=en, MIN_TEXT_LEN=15)
- `app/data/sentiment.py` — VADER (label + score)
- `app/data/storage.py` — SQLite, dedup INSERT OR IGNORE sur uri
- `app/data/collect_bulk.py` — collecteur bulk (api.bsky.app, regex word-boundary)
- `app/ml/aggregate.py` — overview/timeline/trend/forecast/top_posts
- `app/main.py` — API FastAPI

**Frontend**
- `lib/api.ts` — types + fetch
- `components/Charts.tsx` — Recharts (volume, sentiment, pie, themes)
- `components/Dashboard.tsx` — dashboard complet (KPIs, filtres theme, top posts)
- `app/page.tsx`, `app/layout.tsx`, `app/globals.css`

## Garde-fou honnete (forecast)

Le module `forecast()` refuse d'inventer des stats : si < 14 jours distincts,
il renvoie `available: false` avec message clair. Au-dela, moyenne mobile 7j
naive (transparente, PAS un modele ML deguise). Pas de fausses metriques.

## TODO demain
1. Relancer `npm install` frontend
2. `npm run dev` + verifier l'affichage (API doit tourner sur :8000)
3. Ecrire README final
4. (Optionnel) re-collecter pour gonfler le volume
