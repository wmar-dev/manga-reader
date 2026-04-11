"""Download a manga cover from MangaDex by title.

Usage:
    python download_cover.py "Manga Title" [output_dir]

If output_dir is omitted, saves to the current directory.
"""
import sys
import urllib.request
from pathlib import Path

from mangadex_client.api_client import ApiClient
from mangadex_client.configuration import Configuration
from mangadex_client.api.manga_api import MangaApi
from mangadex_client.api.cover_api import CoverApi


def download_cover(title: str, dest_dir: Path = Path(".")) -> Path:
    config = Configuration()
    with ApiClient(config) as client:
        manga_api = MangaApi(client)
        results = manga_api.get_search_manga(
            title=title,
            limit=1,
            content_rating=["safe", "suggestive", "erotica", "pornographic"],
        )
        if not results.data:
            raise ValueError(f"No manga found for title: {title!r}")
        manga = results.data[0]
        manga_id = manga.id

        cover_api = CoverApi(client)
        covers = cover_api.get_cover(manga=[manga_id], limit=1)
        if not covers.data or not covers.data[0].attributes:
            raise ValueError(f"No cover found for manga id: {manga_id}")
        file_name = covers.data[0].attributes.file_name
        if not file_name:
            raise ValueError(f"Cover has no file name for manga id: {manga_id}")

    url = f"https://uploads.mangadex.org/covers/{manga_id}/{file_name}"
    ext = Path(file_name).suffix.lower()
    dest = dest_dir / f"cover{ext}"
    dest_dir.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)
    return dest


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    title = sys.argv[1]
    dest_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")
    try:
        path = download_cover(title, dest_dir)
        print(f"Saved: {path}")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)