import mimetypes
import zipfile

from flask import Blueprint, abort, make_response, render_template, send_file

from db import get_db, get_read_chapters, mark_read, mark_unread
from helpers import MANGA_ROOT, find_cover, get_chapters, get_zip_pages, all_manga, safe_name

bp = Blueprint("manga", __name__)


@bp.route("/cover/<manga>")
def cover(manga):
    if not safe_name(manga):
        abort(400)
    cover_path, mime = find_cover(manga)
    if cover_path is None:
        abort(404)
    return send_file(cover_path, mimetype=mime, max_age=86400)


@bp.route("/")
def index():
    db = get_db()
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
            cover_path, _ = find_cover(manga)
            recommendations.append({
                "manga": manga,
                "next_chapter": unread[0],
                "has_cover": cover_path is not None,
            })

    return render_template("index.html", recommendations=recommendations)


@bp.route("/manga")
def directory():
    manga_list = all_manga()
    covers = {m for m in manga_list if find_cover(m)[0] is not None}
    return render_template("directory.html", manga_list=manga_list, covers=covers)


@bp.route("/manga/<manga>")
def chapter_list(manga):
    if not safe_name(manga):
        abort(400)
    manga_dir = MANGA_ROOT / manga
    if not manga_dir.is_dir():
        abort(404)
    chapters = get_chapters(manga)
    read = get_read_chapters(manga)
    cover_path, _ = find_cover(manga)
    return render_template("chapters.html", manga=manga, chapters=chapters, read=read, has_cover=cover_path is not None)


@bp.route("/manga/<manga>/<chapter>")
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
    )


@bp.route("/manga/<manga>/<chapter>/read", methods=["POST"])
def mark_read_route(manga, chapter):
    if not safe_name(manga) or not safe_name(chapter):
        abort(400)
    mark_read(manga, chapter)
    return ("", 204)


@bp.route("/manga/<manga>/<chapter>/read", methods=["DELETE"])
def mark_unread_route(manga, chapter):
    if not safe_name(manga) or not safe_name(chapter):
        abort(400)
    mark_unread(manga, chapter)
    return ("", 204)


@bp.route("/img/<manga>/<chapter>/<int:page>")
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
