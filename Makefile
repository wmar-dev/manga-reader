.PHONY: test clear-cache serve

test:
	uv run pytest test_helpers.py -v

PORT ?= 5000

serve:
	uv run python main.py

clear-cache:
	curl -sf -X POST http://localhost:$(PORT)/manga/cache/clear && echo "Cache cleared." || echo "Server not running or request failed."
