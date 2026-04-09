import mimetypes
import os
import re
import sqlite3
import zipfile
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, g, make_response, render_template, send_file
from flask_caching import Cache

load_dotenv()

MANGA_ROOT = Path(os.environ.get("MANGA_ROOT", "manga"))
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 5000))
DB_PATH = os.environ.get("DB_PATH", "manga.db")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

app = Flask(__name__)
cache = Cache(app, config={"CACHE_TYPE": "SimpleCache"})


# --- Database ---

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


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


# --- Helpers ---

def natural_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def display_name(s):
    return re.sub(r"[-_]+", " ", s).title()


def chapter_label(manga, chapter):
    # Strip the manga name prefix then find the chapter number
    manga_pat = re.sub(r"[-_\s]+", r"[-_]+", re.escape(manga))
    stripped = re.sub(rf"(?i)^{manga_pat}[-_]*", "", chapter)
    m = re.search(r"\d+(\.\d+)?", stripped or chapter)
    return f"Chapter {m.group()}" if m else display_name(chapter)


def safe_name(s):
    return bool(s) and "/" not in s and ".." not in s and s == os.path.basename(s)


@cache.memoize(timeout=0)
def get_zip_pages(zip_path):
    with zipfile.ZipFile(zip_path) as zf:
        names = [
            n for n in zf.namelist()
            if Path(n).suffix.lower() in IMAGE_EXTS
            and not any(part.startswith(".") for part in Path(n).parts)
            and not n.startswith("__MACOSX")
        ]
    return sorted(names, key=lambda n: natural_key(Path(n).name))


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


# --- Routes ---

COVER_FORMATS = [("cover.webp", "image/webp"), ("cover.png", "image/png"), ("cover.jpg", "image/jpeg")]


def find_cover(manga):
    for filename, _ in COVER_FORMATS:
        p = MANGA_ROOT / manga / filename
        if p.is_file():
            return p
    return None


@app.route("/cover/<manga>")
def cover(manga):
    if not safe_name(manga):
        abort(400)
    cover_path = find_cover(manga)
    if cover_path is None:
        abort(404)
    mime = next(mime for fn, mime in COVER_FORMATS if cover_path.name == fn)
    return send_file(cover_path, mimetype=mime, max_age=86400)


@cache.cached(timeout=300, key_prefix="all_manga")
def all_manga():
    if not MANGA_ROOT.is_dir():
        return []
    return sorted(
        (p.name for p in MANGA_ROOT.iterdir() if p.is_dir() and not p.name.startswith(".")),
        key=natural_key,
    )


@cache.memoize(timeout=300)
def get_chapters(manga):
    return sorted(
        (p.stem for p in (MANGA_ROOT / manga).glob("*.zip") if not p.name.startswith(".")),
        key=natural_key,
    )


@app.route("/")
def index():
    db = get_db()
    # Manga with read chapters, ordered by most recently read
    rows = db.execute("""
        SELECT manga, MAX(read_at) as last_read
        FROM read_chapters
        GROUP BY manga
        ORDER BY last_read DESC
    """).fetchall()

    recommendations = []
    for row in rows:
        manga = row["manga"]
        if not (MANGA_ROOT / manga).is_dir():
            continue
        chapters = get_chapters(manga)
        read = get_read_chapters(manga)
        unread = [ch for ch in chapters if ch not in read]
        if unread:
            recommendations.append({
                "manga": manga,
                "next_chapter": unread[0],
                "has_cover": find_cover(manga) is not None,
            })

    return render_template("index.html", recommendations=recommendations, display_name=display_name, chapter_label=chapter_label)


@app.route("/manga")
def directory():
    manga_list = all_manga()
    covers = {m for m in manga_list if find_cover(m) is not None}
    return render_template("directory.html", manga_list=manga_list, covers=covers, display_name=display_name)


@app.route("/manga/<manga>")
def chapter_list(manga):
    if not safe_name(manga):
        abort(400)
    manga_dir = MANGA_ROOT / manga
    if not manga_dir.is_dir():
        abort(404)
    chapters = get_chapters(manga)
    read = get_read_chapters(manga)
    has_cover = find_cover(manga) is not None
    return render_template("chapters.html", manga=manga, chapters=chapters, read=read, has_cover=has_cover, display_name=display_name, chapter_label=chapter_label)


@app.route("/manga/<manga>/<chapter>")
def reader(manga, chapter):
    if not safe_name(manga) or not safe_name(chapter):
        abort(400)
    zip_path = MANGA_ROOT / manga / f"{chapter}.zip"
    if not zip_path.is_file():
        abort(404)
    pages = get_zip_pages(zip_path)
    total = len(pages)
    if total == 0:
        abort(404)

    chapters = get_chapters(manga)
    idx = chapters.index(chapter) if chapter in chapters else -1
    prev_chapter_url = f"/manga/{manga}/{chapters[idx - 1]}" if idx > 0 else None
    next_chapter_url = f"/manga/{manga}/{chapters[idx + 1]}" if idx >= 0 and idx < len(chapters) - 1 else None

    return render_template(
        "reader.html",
        manga=manga,
        chapter=chapter,
        total=total,
        prev_chapter_url=prev_chapter_url,
        next_chapter_url=next_chapter_url,
        display_name=display_name,
        chapter_label=chapter_label,
    )


@app.route("/manga/<manga>/<chapter>/read", methods=["POST"])
def mark_read_route(manga, chapter):
    if not safe_name(manga) or not safe_name(chapter):
        abort(400)
    mark_read(manga, chapter)
    return ("", 204)


@app.route("/manga/<manga>/<chapter>/read", methods=["DELETE"])
def mark_unread_route(manga, chapter):
    if not safe_name(manga) or not safe_name(chapter):
        abort(400)
    mark_unread(manga, chapter)
    return ("", 204)


@app.route("/img/<manga>/<chapter>/<int:page>")
def image(manga, chapter, page):
    if not safe_name(manga) or not safe_name(chapter):
        abort(400)
    zip_path = MANGA_ROOT / manga / f"{chapter}.zip"
    if not zip_path.is_file():
        abort(404)
    pages = get_zip_pages(zip_path)
    if page < 1 or page > len(pages):
        abort(404)
    page_name = pages[page - 1]
    with zipfile.ZipFile(zip_path) as zf:
        data = zf.read(page_name)
    mime, _ = mimetypes.guess_type(page_name)
    mime = mime or "image/jpeg"
    resp = make_response(data)
    resp.headers["Content-Type"] = mime
    resp.headers["Cache-Control"] = "public, max-age=3600"
    return resp


if __name__ == "__main__":
    init_db()
    app.run(host=HOST, port=PORT, debug=True)
