import sqlite3

from flask import g

DB_PATH: str = "manga.db"


def set_db_path(path: str):
    global DB_PATH
    DB_PATH = path


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
    return g.db


def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("""
            CREATE TABLE IF NOT EXISTS read_chapters (
                manga   TEXT NOT NULL,
                chapter TEXT NOT NULL,
                read_at TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (manga, chapter)
            )
        """)


def get_read_chapters(manga):
    db = get_db()
    rows = db.execute(
        "SELECT chapter FROM read_chapters WHERE manga = ?", (manga,)
    ).fetchall()
    return {row["chapter"] for row in rows}


def mark_read(manga, chapter):
    with get_db() as db:
        db.execute(
            "INSERT OR REPLACE INTO read_chapters (manga, chapter) VALUES (?, ?)",
            (manga, chapter),
        )


def mark_unread(manga, chapter):
    with get_db() as db:
        db.execute(
            "DELETE FROM read_chapters WHERE manga = ? AND chapter = ?",
            (manga, chapter),
        )
