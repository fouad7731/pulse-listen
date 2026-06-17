"""Detection d'alertes : pics de volume et bascules de sentiment.

Logique honnete et transparente (pas de boite noire) :
- PIC DE VOLUME : le volume des N derniers jours depasse la moyenne historique
  de plus d'un seuil (z-score simple ou ratio).
- BASCULE SENTIMENT : le sentiment recent d'un theme chute nettement vs son
  historique (passage en territoire negatif ou forte baisse).

On compare une fenetre "recente" a une baseline "historique" par theme.
"""
from __future__ import annotations

import pandas as pd

from ..data import storage, zones
from . import aggregate

# Parametres de detection
RECENT_DAYS = 3          # fenetre "recente"
BASELINE_DAYS = 21       # fenetre de reference (hors fenetre recente)
SENTIMENT_DROP_ALERT = 0.20  # chute de 0.20 de sentiment moyen -> alerte
MIN_RECENT_POSTS = 5     # bruit : on ignore les themes trop peu actifs

# --- Detection "share of voice" (part de voix) ---
# Le volume ABSOLU est inexploitable : les connecteurs (Google News RSS, Bluesky
# search) remontent surtout du contenu des dernieres 48-72h, donc chaque collecte
# regonfle mecaniquement le present -> faux "pic x10" systematique.
# On mesure plutot la PART d'un theme dans le total (share of voice) : combien la
# conversation se concentre sur ce theme MAINTENANT vs son niveau habituel. Cette
# metrique est insensible au volume de collecte (si tout gonfle, les parts
# restent stables) -> c'est la mesure honnete et standard en social listening.
SOV_RATIO_ALERT = 1.5    # part de voix recente >= 1.5x sa part habituelle -> alerte
SOV_MIN_SHARE = 0.05     # on ignore les themes <5% de part (trop marginaux)
MIN_BASELINE_POSTS = 30  # volume baseline minimal global pour des parts fiables


def _theme_name(code: str) -> str:
    try:
        return zones.get_theme(code).name
    except KeyError:
        return code


def detect(country: str | None = None) -> list[dict]:
    """Retourne la liste des alertes detectees (vide si rien d'anormal).

    Si `country` est fourni, l'analyse (part de voix + sentiment) se fait
    uniquement sur les posts de ce pays -> alertes specifiques au marche.
    """
    df = aggregate._load_df()
    if not df.empty and country:
        df = df[df["country"] == country]
    if df.empty or df["date"].nunique() < (RECENT_DAYS + 3):
        return []

    dates = sorted(df["date"].unique())
    recent_dates = set(dates[-RECENT_DAYS:])
    baseline_dates = set(dates[-(RECENT_DAYS + BASELINE_DAYS):-RECENT_DAYS])
    if not baseline_dates:
        return []

    df_recent = df[df["date"].isin(recent_dates)]
    df_baseline = df[df["date"].isin(baseline_dates)]
    total_recent = len(df_recent)
    total_baseline = len(df_baseline)

    # Totaux insuffisants -> les parts ne sont pas fiables, on s'abstient.
    if total_recent < MIN_RECENT_POSTS or total_baseline < MIN_BASELINE_POSTS:
        reliable_sov = False
    else:
        reliable_sov = True

    alerts: list[dict] = []

    for code in sorted(df["theme"].unique()):
        sub = df[df["theme"] == code]
        recent = sub[sub["date"].isin(recent_dates)]
        baseline = sub[sub["date"].isin(baseline_dates)]

        n_recent = len(recent)
        if n_recent < MIN_RECENT_POSTS:
            continue

        # --- Share of voice (part de voix recente vs habituelle) ---
        # Part = posts du theme / total tous themes, sur chaque fenetre.
        # Insensible au volume de collecte : seule la REPARTITION compte.
        if reliable_sov:
            share_recent = n_recent / total_recent
            share_base = len(baseline) / total_baseline
            if share_recent >= SOV_MIN_SHARE and share_base > 0:
                sov_ratio = share_recent / share_base
                if sov_ratio >= SOV_RATIO_ALERT:
                    alerts.append({
                        "type": "share_spike",
                        "severity": "high" if sov_ratio >= 2 else "medium",
                        "theme": code,
                        "theme_name": _theme_name(code),
                        "message": (
                            f"Montee en part de voix sur \"{_theme_name(code)}\" : "
                            f"{share_recent*100:.0f}% des conversations recentes "
                            f"(x{sov_ratio:.1f} vs habituel, "
                            f"{share_base*100:.0f}%)."
                        ),
                        "metric": round(sov_ratio, 2),
                    })

        # --- Bascule de sentiment ---
        if not baseline.empty:
            recent_sent = float(recent["sentiment_score"].mean())
            base_sent = float(baseline["sentiment_score"].mean())
            drop = base_sent - recent_sent
            if drop >= SENTIMENT_DROP_ALERT:
                alerts.append({
                    "type": "sentiment_drop",
                    "severity": "high" if recent_sent < 0 else "medium",
                    "theme": code,
                    "theme_name": _theme_name(code),
                    "message": (
                        f"Sentiment en baisse sur \"{_theme_name(code)}\" : "
                        f"{base_sent:+.2f} -> {recent_sent:+.2f} "
                        f"(-{drop:.2f})."
                    ),
                    "metric": round(recent_sent, 3),
                })

    # tri : severite high d'abord
    alerts.sort(key=lambda a: 0 if a["severity"] == "high" else 1)
    return alerts


def summary(country: str | None = None) -> dict:
    """Enveloppe pour l'API : alertes + parametres de detection."""
    al = detect(country)
    return {
        "count": len(al),
        "alerts": al,
        "country": country,
        "params": {
            "recent_days": RECENT_DAYS,
            "baseline_days": BASELINE_DAYS,
            "sov_ratio_alert": SOV_RATIO_ALERT,
            "sov_min_share": SOV_MIN_SHARE,
            "sentiment_drop_alert": SENTIMENT_DROP_ALERT,
            "min_baseline_posts": MIN_BASELINE_POSTS,
        },
    }
