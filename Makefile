# udruge.domovina.ai — orkestracija pipelinea. `make help` za popis.
# `make all` radi bez ijednog API ključa. `make rno` ide na mrežu (MFIN), pa je zaseban.

.PHONY: help init ingest geocode rno export stats all all-rno test clean-cache

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

init: ## kreiraj SQLite shemu
	uv run python scripts/00_init_db.py

ingest: ## dohvati registre s data.gov.hr i klasificiraj (Registar udruga, strane udruge, evidencija KC)
	uv run python scripts/01_ingest_registar_udruga.py
	uv run python scripts/02_ingest_strane_udruge.py
	uv run python scripts/03_ingest_evidencija_kc.py

geocode: ## koordinate sjedišta (DGU) + naselje/županija/biskupija prostorno
	uv run python scripts/10_geocode.py $(ARGS)

rno: ## kontakti iz Registra neprofitnih organizacija (MFIN) — mrežno, ~2 req/udruzi
	uv run python scripts/20_enrich_rno.py $(ARGS)

export: ## FTS + GeoJSON + CSV
	uv run python scripts/30_build_fts.py
	uv run python scripts/31_export_geojson.py
	uv run python scripts/32_export_csv.py

stats: ## izvještaj o pokrivenosti (+ data/exports/stats.json)
	uv run python scripts/40_stats.py

all: init ingest geocode export stats ## cijeli pipeline od nule (bez ključeva)

all-rno: init ingest geocode rno export stats ## kao `all` + RNO kontakti

test: ## pytest
	uv run pytest -q

clean-cache: ## obriši keš sirovih odgovora (prisili ponovni dohvat)
	rm -rf data/raw
