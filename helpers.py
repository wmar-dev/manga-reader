import mimetypes
import os
import re
import zipfile
from pathlib import Path

from flask_caching import Cache

MANGA_ROOT = Path(os.environ.get("MANGA_ROOT", "manga"))

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
COVER_NAMES = ["cover.webp", "cover.png", "cover.jpg", "cover.jpeg"]

cache = Cache()


def natural_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def display_name(s):
    return re.sub(r"[-_]+", " ", s).title()


def manga_title(manga):
    from db import get_manga_title
    return get_manga_title(manga) or display_name(manga)


def chapter_label(manga, chapter):
    # Strip the manga name prefix then find the chapter number.
    # Handles decimal chapters encoded as either "29.5" or "29-5".
    manga_pat = re.sub(r"[-_\s]+", r"[-_]+", re.escape(manga))
    stripped = re.sub(rf"(?i)^{manga_pat}[-_]*", "", chapter)
    m = re.search(r"(\d+)[-_](\d+)$|(\d+\.\d+)|\d+", stripped or chapter)
    if not m:
        return display_name(chapter)
    if m.group(1):
        return f"Chapter {m.group(1)}.{m.group(2)}"
    return f"Chapter {m.group()}"


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
