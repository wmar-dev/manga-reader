#!/usr/bin/env python3
"""CLI utilities for manga-reader."""

import argparse
import os
import sys

from dotenv import load_dotenv

load_dotenv()

import db
from helpers import MANGA_ROOT, natural_key

db.set_db_path(os.environ.get("DB_PATH", "manga.db"))


def cmd_mark_read(args: argparse.Namespace) -> None:
    manga = args.manga
    if not (MANGA_ROOT / manga).is_dir():
        print(f"error: manga not found: {manga}", file=sys.stderr)
        sys.exit(1)
    chapters = sorted(
        (p.stem for p in (MANGA_ROOT / manga).glob("*.zip") if not p.name.startswith(".")),
        key=natural_key,
    )
    if not chapters:
        print(f"No chapters found for {manga!r}.")
        return
    db.init_db()
    for chapter in chapters:
        db.mark_read(manga, chapter)
    print(f"Marked {len(chapters)} chapter(s) read for {manga!r}.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="cli.py", description="manga-reader CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_mark = sub.add_parser("mark-read", help="Mark all chapters of a manga as read")
    p_mark.add_argument("manga", help="Manga folder name (as it appears in MANGA_ROOT)")
    p_mark.set_defaults(func=cmd_mark_read)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
