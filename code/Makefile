# SemantOS — convenience targets.
PY ?= python3

.PHONY: help reproduce figures kb-seed data clean-results services-build up down

help:
	@echo "make reproduce   - run offline harness (all paper tables/figures) + PASS/FAIL"
	@echo "make figures     - render fig1/fig3/tau-sweep/drift PNGs from results CSVs"
	@echo "make kb-seed     - induce typed dependency edges -> kb/seed_edges.json"
	@echo "make data        - generate the 1000 workload x hardware training pairs"
	@echo "make up / down   - start / stop the live Docker services"

reproduce:
	$(PY) -m reproduce.run_all

figures:
	$(PY) -m reproduce.figures

kb-seed:
	$(PY) kb/induce_edges.py --out kb/seed_edges.json

data:
	$(PY) data/generate_pairs.py --n 1000 --out data/pairs.jsonl

clean-results:
	rm -f reproduce/results/*.csv reproduce/results/*.png reproduce/results/*.json

up:
	docker compose up -d --build

down:
	docker compose down
