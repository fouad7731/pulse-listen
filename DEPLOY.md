# Déploiement Pulse Listen — Vercel (frontend) + Railway (backend)

Objectif : une URL partagée qui s'auto-update toute seule (collecte toutes les 6h),
sans dépendre de ton Mac.

Architecture :
- **Backend** (FastAPI + SQLite + scheduler) → **Railway** (container persistant + volume disque)
- **Frontend** (Next.js) → **Vercel** (gratuit)

---

## Étape 0 — Code sur GitHub ✅ (fait par Claude)

Repo privé : `https://github.com/fouad7731/pulse-listen`

---

## Étape 1 — Backend sur Railway

1. Va sur **railway.app** → *Login with GitHub* (compte fouad7731).
2. *New Project* → *Deploy from GitHub repo* → choisis **pulse-listen**.
3. Railway détecte le repo. Dans les **Settings** du service :
   - **Root Directory** : `backend`
   - (le `Dockerfile` et `railway.json` sont déjà là, build auto)
4. Onglet **Variables** → ajoute :
   - `PULSE_DB_PATH` = `/data/posts.db`
   - `PULSE_SCHEDULER` = `1`
5. Onglet **Volumes** (ou *+ New* → *Volume*) :
   - Monte un volume sur le chemin **`/data`** (c'est là que vit la base, pour
     qu'elle survive aux redéploiements).
6. **Deploy**. Attends le build (~2-3 min). Le scheduler lance une collecte
   ~30s après le démarrage.
7. Onglet **Settings → Networking → Generate Domain** : tu obtiens une URL
   publique du type `https://pulse-listen-production.up.railway.app`.
   → **Note cette URL**, c'est l'API.
8. Vérifie : ouvre `https://<ton-url-railway>/overview` dans le navigateur,
   tu dois voir du JSON.

---

## Étape 2 — Frontend sur Vercel

1. Va sur **vercel.com** → *Login with GitHub* (compte fouad7731).
2. *Add New… → Project* → importe **pulse-listen**.
3. Dans la config d'import :
   - **Root Directory** : `frontend`
   - Framework : *Next.js* (auto-détecté)
4. **Environment Variables** → ajoute :
   - `NEXT_PUBLIC_API_URL` = l'URL Railway de l'étape 1.7
     (ex : `https://pulse-listen-production.up.railway.app`)
5. **Deploy**. Attends ~1-2 min.
6. Tu obtiens une URL du type `https://pulse-listen.vercel.app`.
   → **C'est l'URL à envoyer à ta collègue.** 🎉

---

## Vérif finale

- Ouvre l'URL Vercel → le dashboard charge avec les données.
- Le backend Railway collecte tout seul toutes les 6h → ça reste frais
  jusqu'à vendredi (et après) sans toucher à rien, Mac éteint compris.

## Coût

- Vercel : gratuit (hobby).
- Railway : crédit d'essai ~5$ offert, largement suffisant pour quelques jours.
  Au-delà, ~5$/mois si tu veux le garder en ligne.
