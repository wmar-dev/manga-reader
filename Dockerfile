FROM python:3.14-slim AS builder

# git is required for uv to fetch the mangadex-client git dependency
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . .
RUN uv sync --frozen --no-dev


FROM python:3.14-slim

WORKDIR /app

RUN groupadd -r app && useradd -r -g app app \
    && mkdir -p /manga /data \
    && chown -R app:app /app /manga /data

COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    MANGA_ROOT=/manga \
    DB_PATH=/data/manga.db \
    HOST=0.0.0.0 \
    PORT=5000

USER app

EXPOSE 5000
VOLUME ["/manga", "/data"]

CMD ["python", "main.py"]
