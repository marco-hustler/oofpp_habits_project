"""SQLite setup — default file habits.db, or :memory: for tests."""

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "habits.db"

_DDL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS habits (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    periodicity TEXT    NOT NULL CHECK(periodicity IN ('daily', 'weekly')),
    description TEXT    NOT NULL DEFAULT '',
    created_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS habit_events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id     INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
    completed_at TEXT    NOT NULL
);
"""


def get_connection(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open the DB with foreign keys on and rows addressable by column name."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create tables if needed and return the connection."""
    conn = get_connection(db_path)
    conn.executescript(_DDL)
    conn.commit()
    return conn
