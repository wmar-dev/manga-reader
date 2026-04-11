# Manga Reader

A minimal self-hosted manga reader. Serves manga from a local directory of zip files with a scroll reader, read tracking, and a recommendations feed.

## Setup

Requires Python 3.14+ and [uv](https://github.com/astral-sh/uv).

```bash
uv sync
python main.py
```

Open [http://localhost:5000](http://localhost:5000).

## Content structure

Organize manga as zip files under a root directory:

```
manga/
  My Manga/
    cover.webp          # optional cover image (also cover.png / cover.jpg)
    My Manga - 001.zip
    My Manga - 002.zip
  Another Series/
    Another Series 1.zip
    ...
```

Each zip contains image files (`.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`). Pages are sorted with natural ordering so `page2` comes before `page10`.

## Configuration

Set via environment variables or a `.env` file:

| Variable    | Default     | Description                      |
|-------------|-------------|----------------------------------|
| `MANGA_ROOT` | `manga/`   | Path to manga directory          |
| `PORT`      | `5000`      | Server port                      |
| `HOST`      | `0.0.0.0`   | Bind address                     |
| `DB_PATH`   | `manga.db`  | SQLite database for read tracking |

## Features

- **Scroll reader** — pages stacked vertically; auto-marks chapter read when you reach the bottom
- **Read tracking** — stored in SQLite; chapters show read/unread status
- **Recommendations** — home page surfaces the next unread chapter for each in-progress series, ordered by most recently read
- **Directory** — browse all manga at `/manga`
- **Keyboard shortcuts** — navigate between chapters from the reader
- **Cover images** — place `cover.webp`, `cover.png`, or `cover.jpg` in a manga folder to show a cover thumbnail
- **Custom titles** — store a display title for any manga in the `manga_titles` DB table; falls back to the humanized folder name
- **Caching** — zip scans and directory listings are cached in memory to avoid redundant disk reads

## Downloading covers

`download_cover.py` fetches a cover image from MangaDex by manga title and saves it as `cover.<ext>` in a directory of your choice.

```bash
uv run python download_cover.py "My Manga" "manga/My Manga"
```

`output_dir` is optional and defaults to the current directory. Run with `--help` for usage.
