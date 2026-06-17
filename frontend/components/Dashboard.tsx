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

function Kpi({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl bg-panel border border-white/5 p-5">
      <div className="text-xs uppercase tracking-wide text-neu">{label}</div>
      <div className="mt-2 text-3xl font-semibold text-white">{value}</div>
      {sub && <div className="mt-1 text-sm text-neu">{sub}</div>}
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl bg-panel border border-white/5 p-5">
      <h3 className="mb-4 text-sm font-semibold text-white">{title}</h3>
      {children}
    </div>
  );
}

function Badge({ label, tone }: { label: string; tone: "src" | "geo" }) {
  const cls =
    tone === "src"
      ? "bg-accent/15 text-accent border-accent/20"
      : "bg-white/5 text-neu border-white/10";
  return (
    <span className={`rounded border px-1.5 py-0.5 text-[10px] uppercase ${cls}`}>
      {label}
    </span>
  );
}

function AlertsBanner({ alerts, scope }: { alerts: Alert[]; scope: string }) {
  if (alerts.length === 0) {
    return (
      <div className="mb-6 flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-neu">
        <span className="text-lg">✅</span>
        <span>Aucune alerte detectee — {scope}.</span>
      </div>
    );
  }
  return (
    <div className="mb-6 space-y-2">
      <div className="text-xs uppercase tracking-wide text-neu">
        Alertes · {scope}
      </div>
      {alerts.map((a, i) => {
        const high = a.severity === "high";
        return (
          <div
            key={i}
            className={`flex items-center gap-3 rounded-xl border p-3 text-sm ${
              high
                ? "border-neg/40 bg-neg/10 text-red-200"
                : "border-amber-500/30 bg-amber-500/5 text-amber-200"
            }`}
          >
            <span className="text-lg">{a.type === "share_spike" ? "📈" : "⚠️"}</span>
            <span>{a.message}</span>
            <span className="ml-auto text-xs uppercase opacity-70">{a.severity}</span>
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
    // liste des pays disponibles (depuis l'overview global)
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
    return (
      <div className="p-10 text-neu">
        Chargement… (verifie que l&apos;API tourne sur :8000)
      </div>
    );
  }

  const dirIcon =
    trend?.direction === "up" ? "▲" : trend?.direction === "down" ? "▼" : "■";
  const dirColor =
    trend?.direction === "up"
      ? "text-pos"
      : trend?.direction === "down"
        ? "text-neg"
        : "text-neu";

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">
            Pulse Listen <span className="text-accent">· Sodas &amp; Wellness</span>
          </h1>
          <p className="mt-1 text-sm text-neu">
            Donnees publiques reelles Bluesky · sentiment VADER ·{" "}
            {overview.n_days} jours d&apos;historique
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
            className="rounded-lg bg-panel border border-white/10 px-4 py-2 text-sm text-white"
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
            className="rounded-lg bg-panel border border-white/10 px-4 py-2 text-sm text-white"
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
            className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-black transition hover:opacity-90"
          >
            Rapport PDF
          </a>
        </div>
      </header>

      {/* Alertes detectees (filtrees par pays) */}
      <AlertsBanner alerts={alerts} scope={scopeLabel} />

      {/* KPIs */}
      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Kpi label="Posts collectes" value={overview.total_posts.toLocaleString()} />
        <Kpi
          label="Sentiment moyen"
          value={overview.sentiment_avg.toFixed(3)}
          sub={overview.sentiment_avg >= 0 ? "globalement positif" : "globalement negatif"}
        />
        <Kpi
          label="Tendance volume"
          value={trend?.available ? `${dirIcon} ${formatPct(trend.delta_pct ?? 0)}` : "—"}
          sub={trend?.available ? "2e moitie vs 1ere" : "donnees insuffisantes"}
        />
        <Kpi
          label="Projection (J+1)"
          value={
            forecast?.available
              ? `${forecast.next_day_estimate} posts/j`
              : "indispo"
          }
          sub={forecast?.available ? "moyenne mobile 7j" : forecast?.reason}
        />
      </div>

      <div className={dirColor} style={{ display: "none" }} />

      {/* Charts grid */}
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
        <div className="mt-6 rounded-xl border border-amber-500/30 bg-amber-500/5 p-5 text-sm text-amber-200">
          <strong>Projection indisponible.</strong> {forecast.message}
        </div>
      )}

      {/* Top posts */}
      <Card title="Posts les plus engageants">
        <div className="mt-2 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-neu">
              <tr className="border-b border-white/10">
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
                <tr key={i} className="border-b border-white/5">
                  <td className="py-2 pr-4 text-accent">@{p.author_handle}</td>
                  <td className="py-2 pr-4 max-w-md truncate text-slate-200">
                    {p.text}
                  </td>
                  <td className="py-2 pr-4">
                    <div className="flex gap-1">
                      <Badge label={p.source} tone="src" />
                      {p.country && p.country !== "global" && (
                        <Badge label={p.country} tone="geo" />
                      )}
                    </div>
                  </td>
                  <td className="py-2 pr-4 text-neu">{p.theme}</td>
                  <td className="py-2 pr-4">
                    <span
                      className={
                        p.sentiment_label === "positive"
                          ? "text-pos"
                          : p.sentiment_label === "negative"
                            ? "text-neg"
                            : "text-neu"
                      }
                    >
                      {p.sentiment_label} ({p.sentiment_score})
                    </span>
                  </td>
                  <td className="py-2 pr-4 text-right text-white">{p.like_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <footer className="mt-10 text-center text-xs text-neu">
        {loading ? "Mise a jour…" : "A jour"} · Pulse Listen · architecture inspiree de
        Pulse by Coca-Cola (FastAPI + Next.js)
      </footer>
    </div>
  );
}
