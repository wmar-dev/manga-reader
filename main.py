import mimetypes
import os
import re
import zipfile
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, g
from flask_caching import Cache

import db as db_module

load_dotenv()

MANGA_ROOT = Path(os.environ.get("MANGA_ROOT", "manga"))
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 5000))
DB_PATH = os.environ.get("DB_PATH", "manga.db")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
COVER_NAMES = ["cover.webp", "cover.png", "cover.jpg", "cover.jpeg"]

db_module.set_db_path(DB_PATH)

app = Flask(__name__)
cache = Cache(app, config={"CACHE_TYPE": "SimpleCache"})


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


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


def find_cover(manga):
    for filename in COVER_NAMES:
        p = MANGA_ROOT / manga / filename
        if p.is_file():
            mime, _ = mimetypes.guess_type(filename)
            return p, mime
    return None, None


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


app.jinja_env.globals.update(display_name=display_name, chapter_label=chapter_label)

from routes import bp  # noqa: E402 — imported after app/cache are defined
app.register_blueprint(bp)


if __name__ == "__main__":
    db_module.init_db()
    app.run(host=HOST, port=PORT, debug=True)
