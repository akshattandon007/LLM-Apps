"""Earworm — data models for podcast transcripts and chunks."""

import sqlite3
import os
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DB_DIR, "earworm.db")


def get_db() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS shows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            feed_url TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            show_id INTEGER NOT NULL REFERENCES shows(id),
            title TEXT NOT NULL,
            description TEXT,
            pub_date TEXT,
            audio_url TEXT,
            source_file TEXT,
            transcript TEXT,
            ingested_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(show_id, title)
        );

        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_id INTEGER NOT NULL REFERENCES episodes(id),
            chunk_index INTEGER NOT NULL,
            text TEXT NOT NULL,
            start_char INTEGER,
            end_char INTEGER,
            token_count INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_chunks_episode ON chunks(episode_id);
        CREATE INDEX IF NOT EXISTS idx_episodes_show ON episodes(show_id);
        CREATE INDEX IF NOT EXISTS idx_episodes_title ON episodes(title);
    """)
    conn.commit()


def insert_show(conn: sqlite3.Connection, name: str, feed_url: str | None = None) -> int:
    conn.execute(
        "INSERT OR IGNORE INTO shows (name, feed_url) VALUES (?, ?)",
        (name, feed_url),
    )
    conn.commit()
    row = conn.execute("SELECT id FROM shows WHERE name = ?", (name,)).fetchone()
    return row["id"]


def insert_episode(
    conn: sqlite3.Connection,
    show_id: int,
    title: str,
    description: str | None,
    pub_date: str | None,
    audio_url: str | None,
    source_file: str | None,
    transcript: str,
) -> int:
    conn.execute(
        """INSERT OR REPLACE INTO episodes
           (show_id, title, description, pub_date, audio_url, source_file, transcript)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (show_id, title, description, pub_date, audio_url, source_file, transcript),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id FROM episodes WHERE show_id = ? AND title = ?", (show_id, title)
    ).fetchone()
    return row["id"]


def insert_chunk(
    conn: sqlite3.Connection,
    episode_id: int,
    chunk_index: int,
    text: str,
    start_char: int,
    end_char: int,
    token_count: int,
) -> int:
    conn.execute(
        """INSERT INTO chunks (episode_id, chunk_index, text, start_char, end_char, token_count)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (episode_id, chunk_index, text, start_char, end_char, token_count),
    )
    conn.commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def clear_chunks_for_episode(conn: sqlite3.Connection, episode_id: int):
    conn.execute("DELETE FROM chunks WHERE episode_id = ?", (episode_id,))
    conn.commit()


def get_episode(conn: sqlite3.Connection, episode_id: int):
    return conn.execute("SELECT * FROM episodes WHERE id = ?", (episode_id,)).fetchone()


def list_shows(conn: sqlite3.Connection):
    return conn.execute("SELECT * FROM shows ORDER BY name").fetchall()


def list_episodes(conn: sqlite3.Connection, show_id: int | None = None):
    if show_id:
        return conn.execute(
            """SELECT e.*, s.name as show_name
               FROM episodes e JOIN shows s ON e.show_id = s.id
               WHERE e.show_id = ? ORDER BY e.pub_date DESC""",
            (show_id,),
        ).fetchall()
    return conn.execute(
        """SELECT e.*, s.name as show_name
           FROM episodes e JOIN shows s ON e.show_id = s.id
           ORDER BY e.pub_date DESC"""
    ).fetchall()


def get_chunks_for_episode(conn: sqlite3.Connection, episode_id: int):
    return conn.execute(
        "SELECT * FROM chunks WHERE episode_id = ? ORDER BY chunk_index",
        (episode_id,),
    ).fetchall()


def get_chunks_by_ids(conn: sqlite3.Connection, chunk_ids: list[int]):
    if not chunk_ids:
        return []
    placeholders = ",".join("?" * len(chunk_ids))
    return conn.execute(
        f"""SELECT c.*, e.title as episode_title, e.pub_date, e.audio_url,
                   s.name as show_name
            FROM chunks c
            JOIN episodes e ON c.episode_id = e.id
            JOIN shows s ON e.show_id = s.id
            WHERE c.id IN ({placeholders})""",
        chunk_ids,
    ).fetchall()


def stats(conn: sqlite3.Connection) -> dict:
    return {
        "shows": conn.execute("SELECT COUNT(*) FROM shows").fetchone()[0],
        "episodes": conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0],
        "chunks": conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0],
    }