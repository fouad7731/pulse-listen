"use client";

import { useEffect, useState } from "react";
import {
  countryLabel,
  fetchAlerts,
  fetchForecast,
  fetchKeywords,
  fetchOverview,
  fetchThemes,
  fetchTimeline,
  fetchTopPosts,
  fetchTrend,
  formatPct,
  reportUrl,
  type Alert,
  type Forecast,
  type KeywordStat,
  type Overview,
  type Theme,
  type TimelinePoint,
  type TopPost,
  type Trend,
} from "@/lib/api";
import {
  CountrySentimentBars,
  KeywordBars,
  SentimentPie,
  SentimentTimeline,
  ThemeBars,
  VolumeTimeline,
} from "./Charts";

function Kpi({
  label,
  value,
  sub,
  tone = "ink",
}: {
  label: string;
  value: string;
  sub?: string;
  tone?: "ink" | "pos" | "neg";
}) {
  const valueColor =
    tone === "pos" ? "text-pos" : tone === "neg" ? "text-neg" : "text-ink";
  return (
    <div className="coca-card p-5">
      <div className="font-mono text-[11px] uppercase tracking-widest text-muted">
        {label}
      </div>
      <div className={`mt-2 font-mono text-3xl font-semibold ${valueColor}`}>
        {value}
      </div>
      {sub && <div className="mt-1 text-sm text-muted">{sub}</div>}
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="coca-card p-6">
      <h3 className="mb-4 font-display text-xl text-ink">{title}</h3>
      {children}
    </div>
  );
}

function Badge({ label, tone }: { label: string; tone: "src" | "geo" }) {
  const cls =
    tone === "src"
      ? "bg-brand/10 text-brand border-brand/20"
      : "bg-ink/5 text-muted border-ink/10";
  return (
    <span className={`rounded border px-1.5 py-0.5 font-mono text-[10px] uppercase ${cls}`}>
      {label}
    </span>
  );
}

function AlertsBanner({ alerts, scope }: { alerts: Alert[]; scope: string }) {
  if (alerts.length === 0) {
    return (
      <div className="mb-6 flex items-center gap-3 rounded-2xl border border-line bg-white p-4 text-sm text-muted">
        <span className="text-lg">✅</span>
        <span>Aucune alerte detectee — {scope}.</span>
      </div>
    );
  }
  return (
    <div className="mb-6 space-y-2">
      <div className="font-mono text-[11px] uppercase tracking-widest text-brand">
        Alertes · {scope}
      </div>
      {alerts.map((a, i) => {
        const high = a.severity === "high";
        return (
          <div
            key={i}
            className={`flex items-center gap-3 rounded-2xl border p-4 text-sm ${
              high
                ? "border-brand/30 bg-brand/5 text-ink"
                : "border-gold/40 bg-gold/10 text-ink"
            }`}
          >
            <span className="text-lg">{a.type === "share_spike" ? "📈" : "⚠️"}</span>
            <span>{a.message}</span>
            <span className="ml-auto font-mono text-[11px] uppercase text-muted">
              {a.severity}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export default function Dashboard() {
  const [themes, setThemes] = useState<Theme[]>([]);
  const [theme, setTheme] = useState<string>("");
  const [country, setCountry] = useState<string>("");
  const [overview, setOverview] = useState<Overview | null>(null);
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [trend, setTrend] = useState<Trend | null>(null);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [topPosts, setTopPosts] = useState<TopPost[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [keywords, setKeywords] = useState<KeywordStat[]>([]);
  const [countries, setCountries] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchThemes().then(setThemes).catch(() => {});
    fetchOverview()
      .then((ov) => setCountries(ov.by_country.map((c) => c.country)))
      .catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const t = theme || undefined;
    const c = country || undefined;
    Promise.all([
      fetchOverview(c),
      fetchTimeline(t, c),
      fetchTrend(t, c),
      fetchForecast(t, c),
      fetchTopPosts(t, 15, c),
      fetchAlerts(c),
      fetchKeywords(t, 12, c),
    ])
      .then(([ov, tl, tr, fc, tp, al, kw]) => {
        setOverview(ov);
        setTimeline(tl);
        setTrend(tr);
        setForecast(fc);
        setTopPosts(tp);
        setAlerts(al.alerts);
        setKeywords(kw);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [theme, country]);

  const scopeLabel = country ? countryLabel(country) : "tous pays";

  if (!overview) {
    return <div className="p-10 text-muted">Chargement…</div>;
  }

  const dirIcon =
    trend?.direction === "up" ? "▲" : trend?.direction === "down" ? "▼" : "■";
  const sentTone = overview.sentiment_avg >= 0 ? "pos" : "neg";

  return (
    <div className="min-h-screen">
      {/* HERO */}
      <header className="bg-coca-hero text-white">
        <div className="mx-auto max-w-7xl px-6 py-12 sm:py-16 relative z-10">
          <p className="font-mono text-xs uppercase tracking-widest text-white/80">
            Module 02 · Social Listening
          </p>
          <h1 className="mt-3 font-display text-5xl sm:text-7xl leading-[1.05]">
            Pulse Listen<span className="text-gold">.</span>
          </h1>
          <p className="mt-2 font-display text-2xl sm:text-3xl text-white/85">
            Le pouls social des boissons.
          </p>
          <p className="mt-5 max-w-2xl text-white/80 leading-relaxed">
            Veille sentiment et tendances sur les conversations sodas, sucre,
            alternatives et bien-etre — Bluesky (parole sociale) + Google News
            (couverture mediatique), {overview.n_days} jours d&apos;historique.
          </p>
          <div className="mt-6 dynamic-island bg-white/10 backdrop-blur-sm">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-gold animate-pulse" />
            <span className="font-mono text-white/90">
              {overview.total_posts.toLocaleString()} posts analyses · 5 marches
            </span>
          </div>
        </div>
      </header>

      <main className="bg-wave">
        <div className="mx-auto max-w-7xl px-6 py-8">
          {/* CONTROLES */}
          <div className="mb-6 flex flex-wrap items-center gap-3">
            <select
              value={theme}
              onChange={(e) => setTheme(e.target.value)}
              className="rounded-full border border-line bg-white px-4 py-2 text-sm text-ink"
            >
              <option value="">Tous les themes</option>
              {themes.map((t) => (
                <option key={t.code} value={t.code}>
                  {t.name}
                </option>
              ))}
            </select>
            <select
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              className="rounded-full border border-line bg-white px-4 py-2 text-sm text-ink"
            >
              <option value="">Tous les pays</option>
              {countries.map((c) => (
                <option key={c} value={c}>
                  {countryLabel(c)}
                </option>
              ))}
            </select>
            <a
              href={reportUrl(theme || undefined, country || undefined)}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-coca ml-auto text-sm"
            >
              Rapport PDF
            </a>
          </div>

          {/* Alertes (filtrees par pays) */}
          <AlertsBanner alerts={alerts} scope={scopeLabel} />

          {/* KPIs */}
          <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
            <Kpi label="Posts collectes" value={overview.total_posts.toLocaleString()} />
            <Kpi
              label="Sentiment moyen"
              value={overview.sentiment_avg.toFixed(3)}
              tone={sentTone}
              sub={overview.sentiment_avg >= 0 ? "globalement positif" : "globalement negatif"}
            />
            <Kpi
              label="Tendance volume"
              value={trend?.available ? `${dirIcon} ${formatPct(trend.delta_pct ?? 0)}` : "—"}
              sub={trend?.available ? "2e moitie vs 1ere" : "donnees insuffisantes"}
            />
            <Kpi
              label="Projection (J+1)"
              value={forecast?.available ? `${forecast.next_day_estimate}` : "indispo"}
              sub={forecast?.available ? "posts/j · moyenne mobile 7j" : forecast?.reason}
            />
          </div>

          {/* Charts */}
          <div className="grid gap-6 lg:grid-cols-2">
            <Card title="Volume de posts dans le temps">
              <VolumeTimeline data={timeline} />
            </Card>
            <Card title="Sentiment moyen dans le temps">
              <SentimentTimeline data={timeline} />
            </Card>
            <Card title="Repartition du sentiment">
              <SentimentPie breakdown={overview.sentiment_breakdown} />
            </Card>
            <Card title="Volume par theme">
              <ThemeBars data={overview.by_theme} />
            </Card>
            <Card title="Sentiment moyen par pays">
              <CountrySentimentBars data={overview.by_country} />
            </Card>
            <Card title={`Mots-cles les plus discutes · ${scopeLabel}`}>
              <KeywordBars data={keywords} />
            </Card>
          </div>

          {/* Forecast honnete */}
          {forecast && !forecast.available && (
            <div className="mt-6 rounded-2xl border border-gold/40 bg-gold/10 p-5 text-sm text-ink">
              <strong>Projection indisponible.</strong> {forecast.message}
            </div>
          )}

          {/* Top posts */}
          <div className="mt-6">
            <Card title="Posts les plus engageants">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="font-mono text-[11px] uppercase tracking-wider text-muted">
                    <tr className="border-b border-line">
                      <th className="py-2 pr-4">Auteur</th>
                      <th className="py-2 pr-4">Texte</th>
                      <th className="py-2 pr-4">Source</th>
                      <th className="py-2 pr-4">Theme</th>
                      <th className="py-2 pr-4">Sentiment</th>
                      <th className="py-2 pr-4 text-right">Likes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {topPosts.map((p, i) => (
                      <tr key={i} className="border-b border-line/70">
                        <td className="py-2 pr-4 font-medium text-brand">@{p.author_handle}</td>
                        <td className="py-2 pr-4 max-w-md truncate text-ink">{p.text}</td>
                        <td className="py-2 pr-4">
                          <div className="flex gap-1">
                            <Badge label={p.source} tone="src" />
                            {p.country && p.country !== "global" && (
                              <Badge label={p.country} tone="geo" />
                            )}
                          </div>
                        </td>
                        <td className="py-2 pr-4 text-muted">{p.theme}</td>
                        <td className="py-2 pr-4">
                          <span
                            className={
                              p.sentiment_label === "positive"
                                ? "text-pos"
                                : p.sentiment_label === "negative"
                                  ? "text-neg"
                                  : "text-muted"
                            }
                          >
                            {p.sentiment_label} ({p.sentiment_score})
                          </span>
                        </td>
                        <td className="py-2 pr-4 text-right font-mono text-ink">{p.like_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>

          <footer className="mt-10 pb-8 text-center font-mono text-xs text-muted">
            {loading ? "Mise a jour…" : "A jour"} · Pulse Listen · architecture
            inspiree de Pulse by Coca-Cola (FastAPI + Next.js)
          </footer>
        </div>
      </main>
    </div>
  );
}
