"""Download a manga cover from MangaDex by title."""
import argparse
import difflib
import logging
import sys
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

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
        matched_title = (
            manga.attributes.title.get("en") or next(iter(manga.attributes.title.values()), "")
            if manga.attributes and manga.attributes.title
            else ""
        )
        ratio = difflib.SequenceMatcher(None, title.lower(), matched_title.lower()).ratio()
        if ratio < 0.95:
            logger.warning(
                "Skipping cover download: %r matched %r with similarity %.2f (below 0.95)",
                title, matched_title, ratio,
            )
            raise ValueError(f"Title match too weak: {title!r} vs {matched_title!r} (ratio {ratio:.2f})")
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("title", help="Manga title to search for")
    parser.add_argument("output_dir", nargs="?", type=Path, default=Path("."), help="Directory to save the cover (default: current directory)")
    args = parser.parse_args()
    try:
        path = download_cover(args.title, args.output_dir)
        print(f"Saved: {path}")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)