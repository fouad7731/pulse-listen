# Déploiement Pulse Listen — 100% gratuit (Vercel + GitHub Actions)

**Site live : https://pulse-listen.vercel.app**

## Architecture (sans serveur, gratuite)

```
GitHub Action (cron toutes les 6h, gratuit)
  → collecte Bluesky + Google News (US/GB/CA/AU/FR)
  → regenere frontend/public/data/data.json + les PDF
  → commit + push sur main
        ↓
Frontend Vercel (gratuit) lit data.json depuis le repo public
(raw.githubusercontent.com) → se met à jour tout seul, SANS redéploiement.
```

- Pas de backend allumé 24/7 (donc gratuit, rien à crasher en démo).
- Le mode statique est activé côté Vercel par `NEXT_PUBLIC_STATIC=1` et
  `NEXT_PUBLIC_DATA_BASE` (URL raw du repo public).
- En local, le frontend reste sur l'API live (`backend` FastAPI) pour le dev.

## Rien à faire au quotidien

L'auto-collecte tourne via `.github/workflows/collect.yml`. Pour forcer un
rafraîchissement immédiat : onglet **Actions** du repo → *Collecte & export* →
*Run workflow*. Ou en CLI : `gh workflow run collect.yml`.

## Lancer en local (dev)

```bash
# backend (API live)
cd backend && .venv/bin/python -m uvicorn app.main:app --port 8000
# frontend
cd frontend && npm run dev
```

## Régénérer les données statiques à la main

```bash
cd backend && python -m app.collect_once   # collecte + export
```
