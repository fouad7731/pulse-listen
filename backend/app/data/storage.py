"""Stockage SQLite des posts collectes, avec dedup sur l'URI."""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# Chemin de la base : configurable via PULSE_DB_PATH (ex: volume Railway
# /data/posts.db). Par defaut, dossier local data_storage/ pour le dev.
_DEFAULT_DB = Path(__file__).resolve().parents[2] / "data_storage" / "posts.db"
DB_PATH = Path(os.getenv("PULSE_DB_PATH", str(_DEFAULT_DB)))

TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    uri TEXT PRIMARY KEY,
    author_handle TEXT,
    text TEXT,
    created_at TEXT,
    lang TEXT,
    like_count INTEGER,
    repost_count INTEGER,
    reply_count INTEGER,
    keyword TEXT,
    theme TEXT,
    sentiment_label TEXT,
    sentiment_score REAL,
    collected_at TEXT,
    source TEXT DEFAULT 'bluesky',
    country TEXT DEFAULT 'global'
);
"""

INDEX_SCHEMA = """
CREATE INDEX IF NOT EXISTS idx_theme ON posts(theme);
CREATE INDEX IF NOT EXISTS idx_sentiment ON posts(sentiment_label);
CREATE INDEX IF NOT EXISTS idx_created ON posts(created_at);
CREATE INDEX IF NOT EXISTS idx_source ON posts(source);
CREATE INDEX IF NOT EXISTS idx_country ON posts(country);
"""


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Migrations douces : ajoute les colonnes manquantes sur bases existantes."""
    cols = {row["name"] for row in conn.execute("PRAGMA table_info(posts)")}
    if "source" not in cols:
        conn.execute("ALTER TABLE posts ADD COLUMN source TEXT DEFAULT 'bluesky'")
    if "country" not in cols:
        conn.execute("ALTER TABLE posts ADD COLUMN country TEXT DEFAULT 'global'")


def init_db() -> None:
    conn = get_connection()
    conn.executescript(TABLE_SCHEMA)  # table d'abord
    _migrate(conn)                    # puis migration colonnes
    conn.executescript(INDEX_SCHEMA)  # index ensuite (depend de 'source')
    conn.commit()
    conn.close()


def save_posts(posts: list[dict]) -> int:
    """INSERT OR IGNORE (dedup sur uri). Retourne le nb de nouveaux inseres."""
    if not posts:
        return 0
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    inserted = 0
    for p in posts:
        cur = conn.execute(
            """INSERT OR IGNORE INTO posts (
                uri, author_handle, text, created_at, lang, like_count,
                repost_count, reply_count, keyword, theme,
                sentiment_label, sentiment_score, collected_at, source, country
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                p["uri"], p.get("author_handle", ""), p.get("text", ""),
                p.get("created_at", ""), p.get("lang", ""), p.get("like_count", 0),
                p.get("repost_count", 0), p.get("reply_count", 0),
                p.get("keyword", ""), p.get("theme", ""),
                p.get("sentiment_label", "neutral"), p.get("sentiment_score", 0.0),
                now, p.get("source", "bluesky"), p.get("country", "global"),
            ),
        )
        inserted += cur.rowcount
    conn.commit()
    conn.close()
    return inserted


def count_posts() -> int:
    conn = get_connection()
    n = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    conn.close()
    return n


def count_by_source() -> dict[str, int]:
    """Repartition du nombre de posts par source de collecte."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT COALESCE(source, 'bluesky') AS src, COUNT(*) AS n "
        "FROM posts GROUP BY src"
    ).fetchall()
    conn.close()
    return {r["src"]: r["n"] for r in rows}


def count_by_country() -> dict[str, int]:
    """Repartition du nombre de posts par pays (couverture media News)."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT COALESCE(country, 'global') AS c, COUNT(*) AS n "
        "FROM posts GROUP BY c ORDER BY n DESC"
    ).fetchall()
    conn.close()
    return {r["c"]: r["n"] for r in rows}
