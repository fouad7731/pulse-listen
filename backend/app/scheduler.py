"""Scheduler de collecte automatique (APScheduler, en process avec l'API).

Au lieu d'un cron systeme externe, on lance un BackgroundScheduler dans le
process FastAPI. Il declenche periodiquement les collecteurs Bluesky et News.

Transparent et coupable : les jobs s'executent en thread de fond ; chaque run
logge son resultat. Desactivable via la variable d'env PULSE_SCHEDULER=0.

Intervalles par defaut (volontairement espaces pour rester poli avec les APIs
publiques gratuites) :
    - Bluesky : toutes les 6h
    - News    : toutes les 6h (decale de 3h pour ne pas tout lancer en meme temps)
"""
from __future__ import annotations

import os
import threading
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from .data import collect_bulk, collect_news

# Heures entre deux collectes (modifiable via env)
BLUESKY_INTERVAL_H = int(os.getenv("PULSE_BLUESKY_INTERVAL_H", "6"))
NEWS_INTERVAL_H = int(os.getenv("PULSE_NEWS_INTERVAL_H", "6"))

# Pays collectes pour les News (editions Google News reelles)
NEWS_COUNTRIES = ["US", "GB", "CA", "AU"]

_scheduler: BackgroundScheduler | None = None
# Evite deux collectes simultanees (Bluesky + News qui se chevauchent)
_lock = threading.Lock()


def _run_bluesky() -> None:
    if not _lock.acquire(blocking=False):
        print("[scheduler] collecte deja en cours, skip Bluesky", flush=True)
        return
    try:
        print("[scheduler] collecte Bluesky auto…", flush=True)
        collect_bulk.collect_all(pages=2, limit=100)
    except Exception as e:  # un job planté ne doit pas tuer le scheduler
        print(f"[scheduler] erreur collecte Bluesky : {e}", flush=True)
    finally:
        _lock.release()


def _run_news() -> None:
    if not _lock.acquire(blocking=False):
        print("[scheduler] collecte deja en cours, skip News", flush=True)
        return
    try:
        print("[scheduler] collecte News auto…", flush=True)
        collect_news.collect_all(limit=30, countries=NEWS_COUNTRIES)
    except Exception as e:
        print(f"[scheduler] erreur collecte News : {e}", flush=True)
    finally:
        _lock.release()


def start() -> BackgroundScheduler | None:
    """Demarre le scheduler si PULSE_SCHEDULER != '0'. Idempotent."""
    global _scheduler
    if os.getenv("PULSE_SCHEDULER", "1") == "0":
        print("[scheduler] desactive (PULSE_SCHEDULER=0)", flush=True)
        return None
    if _scheduler is not None:
        return _scheduler

    _scheduler = BackgroundScheduler(daemon=True)
    # Collecte initiale peu apres le demarrage (decalee pour ne pas tout lancer
    # en meme temps), puis a intervalle regulier. Ainsi les donnees sont
    # rafraichies des le lancement, pas seulement 6h plus tard.
    now = datetime.now()
    _scheduler.add_job(
        _run_bluesky, "interval", hours=BLUESKY_INTERVAL_H,
        id="collect_bluesky", max_instances=1, coalesce=True,
        next_run_time=now + timedelta(seconds=30),
    )
    _scheduler.add_job(
        _run_news, "interval", hours=NEWS_INTERVAL_H,
        id="collect_news", max_instances=1, coalesce=True,
        next_run_time=now + timedelta(seconds=150),
    )
    _scheduler.start()
    print(
        f"[scheduler] demarre : Bluesky/{BLUESKY_INTERVAL_H}h, "
        f"News/{NEWS_INTERVAL_H}h",
        flush=True,
    )
    return _scheduler


def shutdown() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
