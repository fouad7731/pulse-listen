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

const SENT_COLORS: Record<string, string> = {
  positive: "#2ecc71",
  neutral: "#94a3b8",
  negative: "#ef4444",
};

export function VolumeTimeline({ data }: { data: TimelinePoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="vol" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#6ee7ff" stopOpacity={0.6} />
            <stop offset="95%" stopColor="#6ee7ff" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#222" />
        <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
        <YAxis stroke="#64748b" fontSize={11} />
        <Tooltip
          contentStyle={{ background: "#14141c", border: "1px solid #333" }}
        />
        <Area
          type="monotone"
          dataKey="posts"
          stroke="#6ee7ff"
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
        <CartesianGrid strokeDasharray="3 3" stroke="#222" />
        <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
        <YAxis stroke="#64748b" fontSize={11} domain={[-1, 1]} />
        <Tooltip
          contentStyle={{ background: "#14141c", border: "1px solid #333" }}
        />
        <Line
          type="monotone"
          dataKey="sentiment_avg"
          stroke="#6ee7ff"
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
        <Tooltip
          contentStyle={{ background: "#14141c", border: "1px solid #333" }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function ThemeBars({ data }: { data: ThemeStat[] }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#222" />
        <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
        <YAxis stroke="#64748b" fontSize={11} />
        <Tooltip
          contentStyle={{ background: "#14141c", border: "1px solid #333" }}
        />
        <Bar dataKey="posts" fill="#6ee7ff" name="Posts" radius={[4, 4, 0, 0]} />
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
        <CartesianGrid strokeDasharray="3 3" stroke="#222" />
        <XAxis type="number" stroke="#64748b" fontSize={11} domain={[-1, 1]} />
        <YAxis
          type="category"
          dataKey="label"
          stroke="#64748b"
          fontSize={11}
          width={110}
        />
        <Tooltip
          contentStyle={{ background: "#14141c", border: "1px solid #333" }}
          formatter={(v: number, _n, p) => [
            `${v} (${p.payload.posts} posts)`,
            "Sentiment moyen",
          ]}
        />
        <Bar dataKey="sentiment_avg" name="Sentiment moyen" radius={[0, 4, 4, 0]}>
          {rows.map((r, i) => (
            <Cell
              key={i}
              fill={r.sentiment_avg >= 0 ? "#2ecc71" : "#ef4444"}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function KeywordBars({ data }: { data: KeywordStat[] }) {
  // mots-cles (sujets boissons) par volume ; couleur = sentiment moyen
  if (data.length === 0) {
    return <div className="py-10 text-center text-sm text-neu">Aucune donnee</div>;
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
        <CartesianGrid strokeDasharray="3 3" stroke="#222" />
        <XAxis type="number" stroke="#64748b" fontSize={11} />
        <YAxis
          type="category"
          dataKey="label"
          stroke="#64748b"
          fontSize={11}
          width={120}
        />
        <Tooltip
          contentStyle={{ background: "#14141c", border: "1px solid #333" }}
          formatter={(v: number, _n, p) => [
            `${v} posts (sentiment ${p.payload.sentiment_avg >= 0 ? "+" : ""}${p.payload.sentiment_avg})`,
            "Volume",
          ]}
        />
        <Bar dataKey="posts" name="Posts" radius={[0, 4, 4, 0]}>
          {rows.map((r, i) => (
            <Cell key={i} fill={r.sentiment_avg >= 0 ? "#2ecc71" : "#ef4444"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
