PY ?= python3
RAW_RUNS ?=

.PHONY: help reproduce test clean-results services-build up down
help:
	@echo "make reproduce RAW_RUNS=/path/to/raw_runs.csv - validate and aggregate hardware runs"
	@echo "make test - test provenance validation"
	@echo "make up / down - start / stop live Docker services"
reproduce:
	@test -n "$(RAW_RUNS)" || (echo "RAW_RUNS is required" >&2; exit 2)
	$(PY) -m reproduce.run_all "$(RAW_RUNS)"
test:
	$(PY) -m unittest reproduce.test_run_all
clean-results:
	rm -f reproduce/results/*.json
up:
	docker compose up -d --build
down:
	docker compose down
