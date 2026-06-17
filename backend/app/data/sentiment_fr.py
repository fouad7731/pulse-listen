"""Analyse de sentiment FRANCAISE, locale et transparente (pur Python).

VADER est anglais : on ne peut pas l'utiliser tel quel sur du texte francais.
On reproduit ici la MEME approche que VADER (lexique de valences + regles de
negation + intensifieurs), mais avec un lexique francais. Aucune dependance
externe (pas de modele ML lourd, build Docker/Railway sur) et methode lisible.

Echelle des valences : -4 a +4 comme VADER. Le score final ('compound') est
normalise dans [-1, 1] avec la meme formule que VADER, pour rester COMPARABLE
avec les scores anglais affiches dans le meme dashboard.
"""
from __future__ import annotations

import math
import re
import unicodedata


def _fold(s: str) -> str:
    """Replie les accents (santé -> sante) pour matcher le lexique ASCII."""
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )

# --- Lexique de valences (mot -> score -4..+4) ---
# Mots d'opinion courants + vocabulaire boissons/sante. Valeurs dans l'esprit
# des lexiques de sentiment publics (mots etablis, pas de donnee inventee).
LEXICON: dict[str, float] = {
    # positif fort
    "excellent": 3.2, "excellente": 3.2, "parfait": 3.1, "parfaite": 3.1,
    "incroyable": 3.0, "genial": 3.0, "geniale": 3.0, "formidable": 3.0,
    "fantastique": 3.0, "magnifique": 2.9, "delicieux": 2.8, "delicieuse": 2.8,
    "savoureux": 2.5, "savoureuse": 2.5, "adore": 2.7, "adorer": 2.7,
    "meilleur": 2.5, "meilleure": 2.5, "super": 2.3, "top": 2.2,
    # positif moyen
    "bon": 1.9, "bonne": 1.9, "bien": 1.5, "agreable": 1.8, "sain": 2.0,
    "saine": 2.0, "healthy": 2.0, "benefique": 2.0, "benefik": 2.0,
    "naturel": 1.4, "naturelle": 1.4, "bio": 1.2, "frais": 1.2, "fraiche": 1.2,
    "efficace": 1.6, "reussite": 2.0, "succes": 2.0, "qualite": 1.3,
    "recommande": 1.8, "plaisir": 1.9, "aime": 1.6, "aimer": 1.6,
    "avantage": 1.4, "ameliore": 1.6, "amelioration": 1.6, "positif": 1.5,
    "leger": 0.9, "legere": 0.9, "rafraichissant": 1.7, "energie": 1.0,
    # negatif moyen
    "mauvais": -1.9, "mauvaise": -1.9, "mal": -1.5, "probleme": -1.4,
    "risque": -1.3, "danger": -1.9, "dangereux": -2.1, "dangereuse": -2.1,
    "nocif": -2.2, "nocive": -2.2, "toxique": -2.4, "nuisible": -2.0,
    "sucre": -0.4, "gras": -0.8, "calorie": -0.6, "calories": -0.6,
    "obesite": -2.2, "diabete": -2.0, "addiction": -2.0, "dependance": -1.8,
    "cher": -1.0, "chere": -1.0, "decevant": -2.0, "deception": -2.0,
    "negatif": -1.5, "inquietude": -1.6, "inquietant": -1.7, "alerte": -1.3,
    "deconseille": -1.8, "eviter": -1.2, "arnaque": -2.5, "faux": -1.5,
    # negatif fort
    "horrible": -3.0, "affreux": -3.0, "catastrophe": -3.2, "catastrophique": -3.2,
    "deteste": -2.8, "detester": -2.8, "degueulasse": -2.9, "degoutant": -2.8,
    "pire": -2.6, "scandale": -2.7, "poison": -2.8, "mortel": -2.5,
    "maladie": -1.9, "malade": -1.7, "souffrance": -2.3, "echec": -2.2,
}

# --- Negations (inversent le sentiment du mot suivant) ---
NEGATIONS = {
    "ne", "pas", "plus", "jamais", "aucun", "aucune", "sans", "ni",
    "rien", "non", "ni",
}

# --- Intensifieurs (modulent l'intensite) ---
BOOSTERS: dict[str, float] = {
    "tres": 0.3, "vraiment": 0.3, "trop": 0.3, "extremement": 0.4,
    "totalement": 0.3, "completement": 0.3, "absolument": 0.3, "super": 0.2,
    "plutot": -0.1, "assez": -0.05, "peu": -0.2, "moins": -0.2,
    "legerement": -0.2, "a peine": -0.3,
}

POS_THRESHOLD = 0.05
NEG_THRESHOLD = -0.05
_NEG_SCALAR = 0.74          # facteur d'attenuation sur negation (comme VADER)
_ALPHA = 15                 # constante de normalisation (comme VADER)

_TOKEN_RE = re.compile(r"[a-zà-ÿ]+", re.IGNORECASE)


def _normalize(score: float) -> float:
    norm = score / math.sqrt((score * score) + _ALPHA)
    return max(-1.0, min(1.0, norm))


def analyze_text_fr(text: str) -> tuple[str, float]:
    """Retourne (label, compound) ; meme contrat que sentiment.analyze_text."""
    if not text or not text.strip():
        return "neutral", 0.0

    # on replie les accents : tokens et lexique sur la meme base ASCII
    tokens = [_fold(t) for t in _TOKEN_RE.findall(text.lower())]
    total = 0.0
    for i, tok in enumerate(tokens):
        if tok not in LEXICON:
            continue
        val = LEXICON[tok]
        # intensifieur juste avant
        if i > 0 and tokens[i - 1] in BOOSTERS:
            boost = BOOSTERS[tokens[i - 1]]
            val += boost * (1 if val > 0 else -1) * 4
        # negation dans les 3 tokens precedents -> inversion attenuee
        window = tokens[max(0, i - 3):i]
        if any(w in NEGATIONS for w in window):
            val = -val * _NEG_SCALAR
        total += val

    compound = round(_normalize(total), 4)
    if compound >= POS_THRESHOLD:
        label = "positive"
    elif compound <= NEG_THRESHOLD:
        label = "negative"
    else:
        label = "neutral"
    return label, compound
