PY ?= python3
RAW_RUNS ?=
.PHONY: help test inventory reproduce figures kb-seed data up down
help:
	@echo "make test       - regression tests (not performance evidence)"
	@echo "make inventory  - read-only local capability inventory"
	@echo "See evaluation/README.md for raw-data analysis"
test:
	$(PY) -B -m unittest discover -s tests -v
	$(PY) -B -m unittest reproduce.test_run_all -v
inventory:
	$(PY) evaluation/inventory.py
reproduce:
	@test -n "$(RAW_RUNS)" || (echo "RAW_RUNS is required" >&2; exit 2)
	$(PY) -B -m reproduce.run_all "$(RAW_RUNS)"
figures kb-seed data:
	@echo "Withdrawn target-matching synthetic workflow; see legacy/README.md" >&2
	@exit 1
up:
	docker compose up -d --build
down:
	docker compose down
