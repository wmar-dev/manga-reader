.PHONY: test clear-cache serve debug docker-build docker-up docker-down docker-logs mark-read

test:
	uv run pytest test_helpers.py -v

PORT ?= 5000

serve:
	uv run python main.py

debug:
	DEBUG=true uv run python main.py

clear-cache:
	curl -sf -X POST http://localhost:$(PORT)/manga/cache/clear && echo "Cache cleared." || echo "Server not running or request failed."

docker-build:
	docker compose build

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

mark-read:
	uv run python cli.py mark-read $(MANGA)
