# Pulse Listen — Social Listening Sodas & Wellness

Outil maison de **veille sociale temps reel** sur Bluesky autour des sodas,
du sucre, des alternatives et du bien-etre. Inspire de l'architecture
**Pulse by Coca-Cola** (FastAPI + Next.js), mais applique a de la **vraie
donnee publique gratuite** avec analyse de sentiment.

> Aucune cle API, aucun n8n, aucun service payant. 100% local.

---

## Ce que ca fait

- **Collecte multi-sources** : posts publics reels Bluesky (parole sociale) +
  Google News RSS (couverture mediatique), sans authentification
- **Multi-pays** sur News : editions US / GB / CA (donnee pays REELLE via le
  param `gl` de Google News, pas une geoloc inventee) ; Bluesky = `global`
- **Analyse le sentiment** de chaque post (VADER, local, offline)
- **Detecte des alertes** : pics de volume + bascules de sentiment (seuils
  transparents, pas de boite noire)
- **Collecte automatique** : scheduler APScheduler integre a l'API (Bluesky/6h,
  News/6h)
- **Stocke** en SQLite avec dedup automatique
- **Agrege** volume + sentiment par jour, par theme et par pays
- **Expose** une API FastAPI
- **Affiche** un dashboard Next.js (KPIs, bandeau d'alertes, filtres
  theme/pays, courbes, repartition, top posts avec badges source/pays)

### Dataset actuel
- **~4000 posts reels** collectes · Bluesky 1661 · News 2426
- Repartition pays (News) : US ~605 · GB ~627 · CA ~592 · global 2263
- Sentiment moyen global : **~0.17** (globalement positif)

---

## Architecture

```
pulse-listen/
├── backend/                       FastAPI + ML (Python)
│   ├── app/
│   │   ├── data/
│   │   │   ├── zones.py           4 themes, 31 mots-cles, filtres
│   │   │   ├── sentiment.py       VADER (label + score)
│   │   │   ├── storage.py         SQLite, dedup INSERT OR IGNORE
│   │   │   └── collect_bulk.py    collecteur (api.bsky.app, no auth)
│   │   ├── ml/
│   │   │   └── aggregate.py       overview/timeline/trend/forecast
│   │   └── main.py                API FastAPI
│   ├── data_storage/posts.db      base SQLite (1300 posts)
│   └── .venv/                     environnement Python
└── frontend/                      Next.js 15 + TS + Tailwind + Recharts
    ├── app/                       App Router (page, layout, globals)
    ├── components/                Dashboard + Charts
    └── lib/api.ts                 client API type
```

---

## Lancer le projet

### 1. Backend (API)
```bash
cd backend
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
API sur **http://127.0.0.1:8000**

### 2. Frontend (dashboard)
```bash
cd frontend
npm run dev     # npm install deja fait
```
Dashboard sur **http://localhost:3000** (l'API doit tourner en parallele)

### 3. (Re)collecter des donnees
```bash
cd backend
# Bluesky (parole sociale)
.venv/bin/python -m app.data.collect_bulk --pages 4 --limit 100
# Google News RSS, multi-pays (couverture mediatique)
.venv/bin/python -m app.data.collect_news --countries US,GB,CA --limit 30
```

> La collecte tourne aussi **automatiquement** via le scheduler integre a
> l'API (Bluesky/6h, News/6h). Pour le desactiver : `PULSE_SCHEDULER=0`
> avant de lancer uvicorn.

---

## Endpoints API

Filtres communs : `theme=` (sodas/sugar/alternatives/wellness) et
`country=` (global/US/GB/CA).

| Endpoint | Description |
|----------|-------------|
| `GET /` | health + nombre de posts |
| `GET /themes` | liste des 4 themes surveilles |
| `GET /sources` | repartition des posts par source (bluesky/news) |
| `GET /countries` | repartition des posts par pays |
| `GET /overview?country=` | KPIs globaux + repartition par theme + par pays |
| `GET /timeline?theme=&country=` | volume + sentiment par jour |
| `GET /trend?theme=&country=` | tendance (delta volume) |
| `GET /forecast?theme=&country=` | projection (garde-fou si historique court) |
| `GET /top-posts?theme=&country=&limit=` | posts les plus engageants |
| `GET /alerts` | pics de volume + bascules de sentiment detectes |

---

## Detail technique : donnee publique sans auth

Bluesky a restreint l'acces public a `searchPosts` fin 2025 :
- `public.api.bsky.app` → **403** (auth requise)
- `api.bsky.app` → **200** (autorise, avec curseur de pagination)

Le collecteur utilise `api.bsky.app`. La page 2 de pagination est souvent
rate-limitee (403), donc on recupere ~1 page utile par mot-cle — suffisant
pour un volume confortable sur 31 mots-cles.

### Filtres qualite appliques
- **Langue** : posts EN explicites uniquement (`langs` contient `en`)
- **Longueur** : >= 15 caracteres (anti-bruit)
- **Matching** : regex word-boundary (`\bmot\b`) anti faux-positifs
  (ex : evite "soda" dans "asshole", "sprite" jeu video → "sprite soda")
- **Dedup** : `INSERT OR IGNORE` sur l'URI du post

---

## Note d'honnetete sur le "forecast"

Le module `forecast()` **refuse d'inventer des stats** :
- si < 14 jours distincts → renvoie `available: false` + message clair
- sinon → moyenne mobile 7j **naive et transparente** (pas un modele ML
  entraine deguise en vraie prediction)

Contrairement au Pulse original (qui a des annees de ventes historiques pour
entrainer un XGBoost), on n'a pas l'historique necessaire pour une vraie
prediction ML fiable. On l'assume au lieu de produire de fausses metriques.

---

## Stack

| Couche | Techno |
|--------|--------|
| Collecte | `requests` + Bluesky AT Protocol (api.bsky.app) |
| Sentiment | `vaderSentiment` (local, offline, gratuit) |
| Stockage | SQLite |
| Agregation | `pandas` |
| API | `FastAPI` + `uvicorn` |
| Frontend | `Next.js 15` + TypeScript + Tailwind + Recharts |
