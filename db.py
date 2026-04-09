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
    return g.db


def init_db():
    with sqlite3.connect(DB_PATH) as db:
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
    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO read_chapters (manga, chapter) VALUES (?, ?)",
        (manga, chapter),
    )
    db.commit()


def mark_unread(manga, chapter):
    db = get_db()
    db.execute(
        "DELETE FROM read_chapters WHERE manga = ? AND chapter = ?",
        (manga, chapter),
    )
    db.commit()
