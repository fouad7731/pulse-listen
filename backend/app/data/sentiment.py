"""Analyse de sentiment locale (gratuit, offline).

- Anglais : VADER (lexique + regles, reference).
- Francais : moteur a lexique francais maison (sentiment_fr), meme approche,
  scores normalises sur la meme echelle pour rester comparables.

Le routage se fait par langue via analyze(text, lang).
"""
from __future__ import annotations

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from .sentiment_fr import analyze_text_fr

_analyzer = SentimentIntensityAnalyzer()

POS_THRESHOLD = 0.05
NEG_THRESHOLD = -0.05


def analyze_text(text: str) -> tuple[str, float]:
    """Sentiment ANGLAIS via VADER. (label, compound_score)."""
    if not text or not text.strip():
        return "neutral", 0.0
    compound = _analyzer.polarity_scores(text)["compound"]
    if compound >= POS_THRESHOLD:
        label = "positive"
    elif compound <= NEG_THRESHOLD:
        label = "negative"
    else:
        label = "neutral"
    return label, round(compound, 4)


def analyze(text: str, lang: str = "en") -> tuple[str, float]:
    """Route vers le bon moteur selon la langue ('fr' -> francais, sinon VADER)."""
    if lang == "fr":
        return analyze_text_fr(text)
    return analyze_text(text)
