import sqlite3
from collections.abc import Generator
from contextlib import contextmanager

DB_PATH: str = "manga.db"


def set_db_path(path: str) -> None:
    global DB_PATH
    DB_PATH = path


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS read_chapters (
                manga   TEXT NOT NULL,
                chapter TEXT NOT NULL,
                read_at TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (manga, chapter)
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS manga_titles (
                manga       TEXT PRIMARY KEY NOT NULL,
                title       TEXT NOT NULL
            )
        """)
        db.commit()


def get_manga_title(manga: str) -> str | None:
    with get_db() as db:
        row = db.execute(
            "SELECT title FROM manga_titles WHERE manga = ?", (manga,)
        ).fetchone()
    return row["title"] if row else None


def get_recently_read() -> list[str]:
    with get_db() as db:
        rows = db.execute("""
            SELECT manga, MAX(read_at) as last_read
            FROM read_chapters
            GROUP BY manga
            ORDER BY last_read DESC
        """).fetchall()
    return [row["manga"] for row in rows]


def get_read_chapters(manga: str) -> set[str]:
    with get_db() as db:
        rows = db.execute(
            "SELECT chapter FROM read_chapters WHERE manga = ?", (manga,)
        ).fetchall()
    return {row["chapter"] for row in rows}


def mark_read(manga: str, chapter: str) -> None:
    with get_db() as db:
        db.execute(
            "INSERT OR REPLACE INTO read_chapters (manga, chapter) VALUES (?, ?)",
            (manga, chapter),
        )
        db.commit()


def mark_unread(manga: str, chapter: str) -> None:
    with get_db() as db:
        db.execute(
            "DELETE FROM read_chapters WHERE manga = ? AND chapter = ?",
            (manga, chapter),
        )
        db.commit()
