.PHONY: check up down

check:
	@bash scripts/check-deps.sh

up: check
	@bash scripts/deploy.sh

down:
	@bash scripts/teardown.sh
