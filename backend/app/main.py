"""API FastAPI — Pulse Listen (social listening sodas/wellness).

Endpoints :
    GET /                      health + nb de posts
    GET /themes                liste des themes surveilles
    GET /sources               repartition des posts par source (bluesky/news)
    GET /countries             repartition des posts par pays (editions News)
    GET /overview              KPIs globaux + repartition theme + pays
    GET /timeline?theme=&country=    volume + sentiment par jour
    GET /trend?theme=&country=       tendance (delta volume)
    GET /forecast?theme=&country=    projection honnete (garde-fou)
    GET /top-posts?theme=&country=   posts les plus engageants
    GET /keywords?theme=&country=    mots-cles (sujets boissons) les plus presents
    GET /alerts?country=       pics de part de voix + bascules de sentiment
    GET /report?theme=&country=      rapport PDF telechargeable
"""
from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from . import scheduler
from .data import storage, zones
from .ml import aggregate, alerts, report

app = FastAPI(title="Pulse Listen API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    storage.init_db()
    scheduler.start()


@app.on_event("shutdown")
def _shutdown() -> None:
    scheduler.shutdown()


@app.get("/")
def health() -> dict:
    return {"status": "ok", "service": "pulse-listen", "posts": storage.count_posts()}


@app.get("/themes")
def themes() -> list[dict]:
    return [
        {"code": t.code, "name": t.name, "keywords": t.keywords}
        for t in zones.THEMES
    ]


@app.get("/sources")
def sources() -> dict:
    return {"by_source": storage.count_by_source(), "total": storage.count_posts()}


@app.get("/countries")
def countries() -> dict:
    return {"by_country": storage.count_by_country(), "total": storage.count_posts()}


@app.get("/overview")
def overview(country: str | None = Query(default=None)) -> dict:
    return aggregate.overview(country)


@app.get("/timeline")
def timeline(
    theme: str | None = Query(default=None),
    country: str | None = Query(default=None),
) -> list[dict]:
    return aggregate.timeline(theme, country)


@app.get("/trend")
def trend(
    theme: str | None = Query(default=None),
    country: str | None = Query(default=None),
) -> dict:
    return aggregate.trend(theme, country)


@app.get("/forecast")
def forecast(
    theme: str | None = Query(default=None),
    country: str | None = Query(default=None),
) -> dict:
    return aggregate.forecast(theme, country)


@app.get("/top-posts")
def top_posts(
    theme: str | None = Query(default=None),
    country: str | None = Query(default=None),
    limit: int = Query(default=15, ge=1, le=50),
) -> list[dict]:
    return aggregate.top_posts(theme, limit, country)


@app.get("/keywords")
def keywords(
    theme: str | None = Query(default=None),
    country: str | None = Query(default=None),
    limit: int = Query(default=12, ge=1, le=50),
) -> list[dict]:
    return aggregate.top_keywords(theme, limit, country)


@app.get("/alerts")
def get_alerts(country: str | None = Query(default=None)) -> dict:
    return alerts.summary(country)


@app.get("/report")
def report_pdf(
    theme: str | None = Query(default=None),
    country: str | None = Query(default=None),
) -> Response:
    pdf_bytes = report.build_pdf(country, theme)
    stamp = "pulse-listen-rapport"
    if country:
        stamp += f"-{country}"
    if theme:
        stamp += f"-{theme}"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{stamp}.pdf"'},
    )
