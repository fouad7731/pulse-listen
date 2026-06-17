"""Analyse de sentiment locale via VADER (gratuit, offline, anglais)."""
from __future__ import annotations

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()

POS_THRESHOLD = 0.05
NEG_THRESHOLD = -0.05


def analyze_text(text: str) -> tuple[str, float]:
    """Retourne (label, compound_score) ; label in positive/neutral/negative."""
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
