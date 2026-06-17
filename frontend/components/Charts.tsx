"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TimelinePoint, ThemeStat, CountryStat, KeywordStat } from "@/lib/api";
import { countryLabel } from "@/lib/api";

// Palette charte Pulse by Coca-Cola
const BRAND = "#F40009";
const GOLD = "#D4AF37";
const INK = "#1A1A1A";
const GRID = "#E5E5E5";
const AXIS = "#6B6B6B";
const POS = "#1f9d55";
const NEG = "#F40009";
const NEU = "#6B6B6B";

const TOOLTIP = {
  background: "#ffffff",
  border: "1px solid #E5E5E5",
  borderRadius: 10,
  color: "#1A1A1A",
  boxShadow: "0 8px 24px rgba(0,0,0,0.08)",
} as const;

const SENT_COLORS: Record<string, string> = {
  positive: POS,
  neutral: NEU,
  negative: NEG,
};

export function VolumeTimeline({ data }: { data: TimelinePoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="vol" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={BRAND} stopOpacity={0.35} />
            <stop offset="95%" stopColor={BRAND} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID} />
        <XAxis dataKey="date" stroke={AXIS} fontSize={11} />
        <YAxis stroke={AXIS} fontSize={11} />
        <Tooltip contentStyle={TOOLTIP} />
        <Area
          type="monotone"
          dataKey="posts"
          stroke={BRAND}
          strokeWidth={2}
          fill="url(#vol)"
          name="Posts"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function SentimentTimeline({ data }: { data: TimelinePoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID} />
        <XAxis dataKey="date" stroke={AXIS} fontSize={11} />
        <YAxis stroke={AXIS} fontSize={11} domain={[-1, 1]} />
        <Tooltip contentStyle={TOOLTIP} />
        <Line
          type="monotone"
          dataKey="sentiment_avg"
          stroke={INK}
          strokeWidth={2}
          dot={false}
          name="Sentiment moyen"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function SentimentPie({
  breakdown,
}: {
  breakdown: { positive: number; neutral: number; negative: number };
}) {
  const data = [
    { name: "positive", value: breakdown.positive },
    { name: "neutral", value: breakdown.neutral },
    { name: "negative", value: breakdown.negative },
  ];
  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" outerRadius={100} label>
          {data.map((d) => (
            <Cell key={d.name} fill={SENT_COLORS[d.name]} />
          ))}
        </Pie>
        <Tooltip contentStyle={TOOLTIP} />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function ThemeBars({ data }: { data: ThemeStat[] }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID} />
        <XAxis dataKey="name" stroke={AXIS} fontSize={11} />
        <YAxis stroke={AXIS} fontSize={11} />
        <Tooltip contentStyle={TOOLTIP} cursor={{ fill: "rgba(244,0,9,0.05)" }} />
        <Bar dataKey="posts" fill={BRAND} name="Posts" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function CountrySentimentBars({ data }: { data: CountryStat[] }) {
  // sentiment moyen par pays : barre verte si positif, rouge si negatif
  const rows = data.map((c) => ({
    label: countryLabel(c.country),
    sentiment_avg: c.sentiment_avg,
    posts: c.posts,
  }));
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={rows} layout="vertical" margin={{ left: 30 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID} />
        <XAxis type="number" stroke={AXIS} fontSize={11} domain={[-1, 1]} />
        <YAxis type="category" dataKey="label" stroke={AXIS} fontSize={11} width={110} />
        <Tooltip
          contentStyle={TOOLTIP}
          cursor={{ fill: "rgba(0,0,0,0.03)" }}
          formatter={(v: number, _n, p) => [
            `${v} (${p.payload.posts} posts)`,
            "Sentiment moyen",
          ]}
        />
        <Bar dataKey="sentiment_avg" name="Sentiment moyen" radius={[0, 4, 4, 0]}>
          {rows.map((r, i) => (
            <Cell key={i} fill={r.sentiment_avg >= 0 ? POS : NEG} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function KeywordBars({ data }: { data: KeywordStat[] }) {
  // mots-cles (sujets boissons) par volume ; couleur = sentiment moyen
  if (data.length === 0) {
    return <div className="py-10 text-center text-sm text-muted">Aucune donnee</div>;
  }
  const rows = data.map((k) => ({
    label: k.keyword,
    posts: k.posts,
    sentiment_avg: k.sentiment_avg,
  }));
  const height = Math.max(280, rows.length * 26);
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={rows} layout="vertical" margin={{ left: 30 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID} />
        <XAxis type="number" stroke={AXIS} fontSize={11} />
        <YAxis type="category" dataKey="label" stroke={AXIS} fontSize={11} width={120} />
        <Tooltip
          contentStyle={TOOLTIP}
          cursor={{ fill: "rgba(0,0,0,0.03)" }}
          formatter={(v: number, _n, p) => [
            `${v} posts (sentiment ${p.payload.sentiment_avg >= 0 ? "+" : ""}${p.payload.sentiment_avg})`,
            "Volume",
          ]}
        />
        <Bar dataKey="posts" name="Posts" radius={[0, 4, 4, 0]}>
          {rows.map((r, i) => (
            <Cell key={i} fill={r.sentiment_avg >= 0 ? POS : NEG} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
