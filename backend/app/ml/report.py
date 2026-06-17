"""Generation d'un rapport PDF de veille (fpdf2, pur Python, sans dep systeme).

Le rapport reprend les memes chiffres que le dashboard : KPIs, sentiment,
repartition par theme et par pays, mots-cles les plus discutes, alertes.
Filtrable par pays et/ou theme (memes parametres que l'API).

fpdf2 + polices coeur (Helvetica) = encodage Latin-1 : les accents francais
passent. On evite emojis / fleches / guillemets typographiques (hors Latin-1).
"""
from __future__ import annotations

from datetime import datetime, timezone

from fpdf import FPDF

from ..data import zones
from . import aggregate, alerts

# Couleurs marque (WyExpert teal)
TEAL = (8, 159, 153)
DARK = (10, 46, 44)
GREEN = (46, 204, 113)
RED = (239, 68, 68)
GRAY = (148, 163, 184)
LIGHT = (240, 244, 244)

_COUNTRY_LABELS = {
    "global": "Global (Bluesky)",
    "US": "Etats-Unis",
    "GB": "Royaume-Uni",
    "CA": "Canada",
    "AU": "Australie",
    "FR": "France",
}


def _country_label(code: str) -> str:
    return _COUNTRY_LABELS.get(code, code)


def _sent_color(v: float) -> tuple[int, int, int]:
    if v >= 0.05:
        return GREEN
    if v <= -0.05:
        return RED
    return GRAY


class _Report(FPDF):
    def header(self) -> None:
        self.set_fill_color(*DARK)
        self.rect(0, 0, self.w, 26, style="F")
        self.set_xy(12, 7)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 6, "Pulse Listen", new_x="LMARGIN", new_y="NEXT")
        self.set_x(12)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*TEAL)
        self.cell(0, 5, "Rapport de veille - Sodas & Wellness")
        self.set_y(32)
        self.set_text_color(0, 0, 0)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*GRAY)
        self.cell(
            0, 5,
            "Sources : Bluesky (parole sociale) + Google News RSS (couverture "
            "mediatique). Sentiment : VADER (local). Page "
            + str(self.page_no()),
            align="C",
        )


def _section_title(pdf: _Report, txt: str) -> None:
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 7, txt, new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*TEAL)
    pdf.set_line_width(0.5)
    y = pdf.get_y()
    pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)


def _kpi_box(pdf: _Report, x: float, w: float, label: str, value: str) -> None:
    y = pdf.get_y()
    pdf.set_fill_color(*LIGHT)
    pdf.rect(x, y, w, 18, style="F")
    pdf.set_xy(x + 2, y + 2)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*GRAY)
    pdf.cell(w - 4, 4, label)
    pdf.set_xy(x + 2, y + 7)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(*DARK)
    pdf.cell(w - 4, 9, value)
    pdf.set_text_color(0, 0, 0)


def _bar_row(pdf: _Report, label: str, value: float, count: int,
             vmax: float, signed: bool) -> None:
    """Une ligne : label + barre proportionnelle + valeur."""
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)
    label_w = 48
    pdf.cell(label_w, 6, label[:30])
    bar_x = pdf.get_x()
    bar_max_w = 90
    y = pdf.get_y()
    # fond de barre
    pdf.set_fill_color(235, 238, 238)
    pdf.rect(bar_x, y + 1, bar_max_w, 4, style="F")
    # barre valeur
    if vmax > 0:
        ratio = min(abs(value) / vmax, 1.0)
    else:
        ratio = 0
    if signed:
        color = _sent_color(value)
    else:
        color = TEAL
    pdf.set_fill_color(*color)
    pdf.rect(bar_x, y + 1, bar_max_w * ratio, 4, style="F")
    pdf.set_x(bar_x + bar_max_w + 3)
    pdf.set_font("Helvetica", "B", 9)
    suffix = f"  ({count} posts)" if count else ""
    if signed:
        pdf.cell(0, 6, f"{value:+.3f}{suffix}", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 6, f"{int(value)}{suffix}", new_x="LMARGIN", new_y="NEXT")


def build_pdf(country: str | None = None, theme: str | None = None) -> bytes:
    ov = aggregate.overview(country)
    kws = aggregate.top_keywords(theme, 10, country)
    al = alerts.summary(country)

    scope_parts = []
    scope_parts.append(_country_label(country) if country else "Tous pays")
    if theme:
        try:
            scope_parts.append(zones.get_theme(theme).name)
        except KeyError:
            scope_parts.append(theme)
    else:
        scope_parts.append("Tous themes")
    scope = " - ".join(scope_parts)

    pdf = _Report(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Meta
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GRAY)
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    pdf.cell(0, 5, f"Genere le {now}  |  Perimetre : {scope}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    # KPIs
    w = (pdf.w - pdf.l_margin - pdf.r_margin - 8) / 3
    x0 = pdf.l_margin
    _kpi_box(pdf, x0, w, "Posts analyses", f"{ov['total_posts']:,}".replace(",", " "))
    _kpi_box(pdf, x0 + w + 4, w, "Sentiment moyen", f"{ov['sentiment_avg']:+.3f}")
    _kpi_box(pdf, x0 + 2 * (w + 4), w, "Jours d'historique", str(ov["n_days"]))
    pdf.ln(22)

    # Sentiment global
    br = ov["sentiment_breakdown"]
    total = max(br["positive"] + br["neutral"] + br["negative"], 1)
    _section_title(pdf, "Repartition du sentiment")
    for lbl, key, val in [
        ("Positif", "positive", br["positive"]),
        ("Neutre", "neutral", br["neutral"]),
        ("Negatif", "negative", br["negative"]),
    ]:
        pct = val / total * 100
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(48, 6, f"{lbl}")
        bar_x = pdf.get_x()
        y = pdf.get_y()
        pdf.set_fill_color(235, 238, 238)
        pdf.rect(bar_x, y + 1, 90, 4, style="F")
        col = GREEN if key == "positive" else RED if key == "negative" else GRAY
        pdf.set_fill_color(*col)
        pdf.rect(bar_x, y + 1, 90 * (pct / 100), 4, style="F")
        pdf.set_x(bar_x + 93)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 6, f"{pct:.0f}%  ({val} posts)",
                 new_x="LMARGIN", new_y="NEXT")

    # Par theme
    _section_title(pdf, "Volume par theme")
    tmax = max((t["posts"] for t in ov["by_theme"]), default=1)
    for t in ov["by_theme"]:
        _bar_row(pdf, t["name"], t["posts"], 0, tmax, signed=False)

    # Par pays (seulement si vue globale, sinon redondant)
    if not country and ov.get("by_country"):
        _section_title(pdf, "Sentiment moyen par pays")
        for c in ov["by_country"]:
            _bar_row(pdf, _country_label(c["country"]), c["sentiment_avg"],
                     c["posts"], 1.0, signed=True)

    # Mots-cles
    if kws:
        _section_title(pdf, "Mots-cles les plus discutes")
        kmax = max((k["posts"] for k in kws), default=1)
        for k in kws:
            _bar_row(pdf, k["keyword"], k["posts"], 0, kmax, signed=False)

    # Alertes
    _section_title(pdf, "Alertes detectees")
    pdf.set_font("Helvetica", "", 9)
    if al["count"] == 0:
        pdf.set_text_color(*GRAY)
        pdf.cell(0, 6, "Aucune alerte sur ce perimetre.",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
    else:
        for a in al["alerts"]:
            sev = a["severity"].upper()
            col = RED if a["severity"] == "high" else (200, 140, 0)
            pdf.set_x(pdf.l_margin)
            pdf.set_text_color(*col)
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(0, 6, f"[{sev}] {a['message']}",
                           new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)

    out = pdf.output()
    return bytes(out)
