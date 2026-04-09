# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the server
python main.py

# Run with a custom manga directory or port
MANGA_ROOT=/path/to/manga PORT=5001 python main.py
```

## Architecture

Single-file Flask app ([main.py](main.py)) with Jinja2 templates in [templates/](templates/) and CSS in [static/style.css](static/style.css).

**Routes:**
- `GET /` — manga list (directories under `MANGA_ROOT`)
- `GET /manga/<manga>` — chapter list (`.zip` files in the manga directory)
- `GET /manga/<manga>/<chapter>` — scroll reader (all pages stacked vertically)
- `GET /img/<manga>/<chapter>/<int:page>` — streams a single image out of the zip without extracting to disk
- `POST /manga/<manga>/<chapter>/read` — marks chapter read in SQLite
- `DELETE /manga/<manga>/<chapter>/read` — marks chapter unread

**Content discovery:** `MANGA_ROOT/{manga_name}/{chapter}.zip`. Pages inside each zip are sorted with `natural_key()` (handles `page2 < page10`). All names are validated through `safe_name()` to prevent path traversal.

**Read tracking:** SQLite database (default `manga.db`, configurable via `DB_PATH` env var). The DB is initialized at startup via `init_db()`. Flask's `g` object holds the per-request connection. A chapter is marked read client-side via `fetch POST` when the user scrolls within 200px of the bottom of the reader page.

**Configuration** (all via `.env` or environment variables):
- `MANGA_ROOT` — path to manga directory (default: `manga/`)
- `PORT` — server port (default: `5000`)
- `HOST` — bind address (default: `0.0.0.0`)
- `DB_PATH` — SQLite database path (default: `manga.db`)
