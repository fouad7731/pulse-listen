"""Themes et mots-cles surveilles (equivalent des 'zones' de Pulse Forecast).

Ici la dimension d'analyse n'est pas geographique mais thematique :
on suit le buzz autour des sodas, du sucre, des alternatives et du wellness.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Theme:
    """Un theme de veille = un groupe de mots-cles de recherche.

    keywords    : mots-cles anglais (marches US/GB/CA/AU, sentiment VADER)
    keywords_fr : mots-cles francais (marche FR, sentiment francais)
    """
    code: str
    name: str
    keywords: list[str] = field(default_factory=list)
    keywords_fr: list[str] = field(default_factory=list)


THEMES: list[Theme] = [
    Theme("sodas", "Sodas & marques", [
        "soft drink", "coca cola", "pepsi", "dr pepper", "mountain dew",
        "energy drink", "fizzy drink", "sprite zero", "fanta soda",
    ], [
        "soda", "coca cola", "boisson gazeuse", "boisson energisante",
        "limonade", "boisson sucree",
    ]),
    Theme("sugar", "Sucre & sante", [
        "sugar free", "no sugar", "added sugar", "too much sugar",
        "low sugar", "reduce sugar", "cut out sugar",
    ], [
        "sans sucre", "trop de sucre", "sucre ajoute", "reduire le sucre",
        "moins de sucre", "exces de sucre",
    ]),
    Theme("alternatives", "Alternatives", [
        "zero sugar", "diet soda", "sparkling water", "kombucha",
        "prebiotic soda", "olipop", "poppi", "seltzer",
    ], [
        "zero sucre", "soda light", "eau petillante", "kombucha",
        "boisson fermentee", "soda prebiotique",
    ]),
    Theme("wellness", "Bien-etre", [
        "gut health", "healthy drink", "wellness drink", "sugar detox",
        "quit soda", "quitting soda", "soda addiction",
    ], [
        "sante intestinale", "boisson saine", "microbiote", "detox sucre",
        "arreter le soda", "addiction au sucre",
    ]),
]

# Index inverse : keyword -> theme code (anglais)
KEYWORD_TO_THEME: dict[str, str] = {
    kw.lower(): t.code for t in THEMES for kw in t.keywords
}

# Toutes les requetes a lancer (keyword, theme_code) - anglais
ALL_QUERIES: list[tuple[str, str]] = [
    (kw, t.code) for t in THEMES for kw in t.keywords
]

# Requetes francaises (keyword_fr, theme_code)
ALL_QUERIES_FR: list[tuple[str, str]] = [
    (kw, t.code) for t in THEMES for kw in t.keywords_fr
]


def queries_for_lang(lang: str) -> list[tuple[str, str]]:
    """Liste (keyword, theme) selon la langue ('fr' -> FR, sinon EN)."""
    return ALL_QUERIES_FR if lang == "fr" else ALL_QUERIES


# Langue cible par defaut (VADER = anglais)
LANG = "en"

# Longueur min du texte pour analyse
MIN_TEXT_LEN = 15


def get_theme(code: str) -> Theme:
    for t in THEMES:
        if t.code == code:
            return t
    raise KeyError(code)
