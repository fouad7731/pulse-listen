const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export type Theme = {
  code: string;
  name: string;
  keywords: string[];
};

export type ThemeStat = {
  theme: string;
  name: string;
  posts: number;
  sentiment_avg: number;
  positive: number;
  neutral: number;
  negative: number;
};

export type CountryStat = {
  country: string;
  posts: number;
  sentiment_avg: number;
};

export type Overview = {
  total_posts: number;
  sentiment_avg: number;
  sentiment_breakdown: { positive: number; neutral: number; negative: number };
  by_theme: ThemeStat[];
  by_country: CountryStat[];
  n_days: number;
  generated_at?: string;
};

export type TimelinePoint = {
  date: string;
  posts: number;
  sentiment_avg: number;
  positive: number;
  negative: number;
};

export type Trend = {
  available: boolean;
  reason?: string;
  n_days?: number;
  total_posts?: number;
  first_half_posts?: number;
  second_half_posts?: number;
  delta_pct?: number;
  direction?: "up" | "down" | "flat";
};

export type Forecast = {
  available: boolean;
  reason?: string;
  n_days?: number;
  min_required?: number;
  message?: string;
  method?: string;
  next_day_estimate?: number;
  note?: string;
};

export type TopPost = {
  author_handle: string;
  text: string;
  theme: string;
  keyword: string;
  source: string;
  country: string;
  sentiment_label: string;
  sentiment_score: number;
  like_count: number;
  repost_count: number;
};

export type Alert = {
  type: "share_spike" | "sentiment_drop";
  severity: "high" | "medium";
  theme: string;
  theme_name: string;
  message: string;
  metric: number;
};

export type AlertsResponse = {
  count: number;
  alerts: Alert[];
  country?: string | null;
  params: Record<string, number>;
};

export type KeywordStat = {
  keyword: string;
  posts: number;
  sentiment_avg: number;
  theme: string;
};

export type SourcesResponse = {
  by_source: Record<string, number>;
  total: number;
};

export type CountriesResponse = {
  by_country: Record<string, number>;
  total: number;
};

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`API ${path} -> ${r.status}`);
  return r.json();
}

function qs(params: Record<string, string | number | undefined>): string {
  const parts = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== "")
    .map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`);
  return parts.length ? `?${parts.join("&")}` : "";
}

// ----- Mode STATIQUE (hebergement gratuit : donnees pre-generees) -----
// Active si NEXT_PUBLIC_STATIC=1. Le frontend charge un bundle unique
// (data/data.json) et y pioche, au lieu d'appeler une API live.
const STATIC = process.env.NEXT_PUBLIC_STATIC === "1";
const k = (v?: string) => v || "all";        // cle de combinaison
const tk = (t?: string, c?: string) => `${k(t)}|${k(c)}`;

type Bundle = {
  themes: Theme[];
  countries: string[];
  overview: Record<string, Overview>;
  alerts: Record<string, AlertsResponse>;
  timeline: Record<string, TimelinePoint[]>;
  trend: Record<string, Trend>;
  forecast: Record<string, Forecast>;
  top_posts: Record<string, TopPost[]>;
  keywords: Record<string, KeywordStat[]>;
};

let _bundle: Promise<Bundle> | null = null;
function bundle(): Promise<Bundle> {
  if (!_bundle) {
    _bundle = fetch("/data/data.json", { cache: "no-store" }).then((r) => {
      if (!r.ok) throw new Error(`bundle -> ${r.status}`);
      return r.json();
    });
  }
  return _bundle;
}

export const fetchThemes = () =>
  STATIC ? bundle().then((b) => b.themes) : get<Theme[]>("/themes");
export const fetchOverview = (country?: string) =>
  STATIC
    ? bundle().then((b) => b.overview[k(country)])
    : get<Overview>(`/overview${qs({ country })}`);
export const fetchTimeline = (theme?: string, country?: string) =>
  STATIC
    ? bundle().then((b) => b.timeline[tk(theme, country)] ?? [])
    : get<TimelinePoint[]>(`/timeline${qs({ theme, country })}`);
export const fetchTrend = (theme?: string, country?: string) =>
  STATIC
    ? bundle().then((b) => b.trend[tk(theme, country)])
    : get<Trend>(`/trend${qs({ theme, country })}`);
export const fetchForecast = (theme?: string, country?: string) =>
  STATIC
    ? bundle().then((b) => b.forecast[tk(theme, country)])
    : get<Forecast>(`/forecast${qs({ theme, country })}`);
export const fetchTopPosts = (theme?: string, limit = 15, country?: string) =>
  STATIC
    ? bundle().then((b) => b.top_posts[tk(theme, country)] ?? [])
    : get<TopPost[]>(`/top-posts${qs({ theme, country, limit })}`);
export const fetchAlerts = (country?: string) =>
  STATIC
    ? bundle().then((b) => b.alerts[k(country)])
    : get<AlertsResponse>(`/alerts${qs({ country })}`);
export const fetchKeywords = (theme?: string, limit = 12, country?: string) =>
  STATIC
    ? bundle().then((b) => b.keywords[tk(theme, country)] ?? [])
    : get<KeywordStat[]>(`/keywords${qs({ theme, country, limit })}`);
export const fetchSources = () => get<SourcesResponse>("/sources");
export const fetchCountries = () => get<CountriesResponse>("/countries");

// URL du rapport PDF : statique pre-genere, ou endpoint live.
export const reportUrl = (theme?: string, country?: string) =>
  STATIC
    ? `/reports/${k(theme)}__${k(country)}.pdf`
    : `${API}/report${qs({ theme, country })}`;

export function formatPct(n: number): string {
  return `${n >= 0 ? "+" : ""}${n.toFixed(1)}%`;
}

const COUNTRY_LABELS: Record<string, string> = {
  global: "Global (Bluesky)",
  US: "Etats-Unis",
  GB: "Royaume-Uni",
  CA: "Canada",
  AU: "Australie",
  FR: "France",
};

export function countryLabel(code: string): string {
  return COUNTRY_LABELS[code] ?? code;
}
