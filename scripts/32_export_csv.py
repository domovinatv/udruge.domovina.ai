"""Eksport u CSV (data/exports/) — ljudski čitljiv otvoreni podatak.

  udruge.csv             katalog: pouzdanost visoka + srednja, svi statusi
  udruge-za-pregled.csv  pouzdanost niska — kandidati koje je bodovanje
                         dotaklo ali ne potvrdilo; red za ručni pregled

UTF-8 s BOM-om jer Excel inače krivo prikaže č/ć/š/ž.

  uv run python scripts/32_export_csv.py
"""
from __future__ import annotations

import csv
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.db import connect  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("export-csv")

OUT_DIR = ROOT / "data" / "exports"

_COLS = """
    id, slug, name AS naziv, display_name AS naziv_prikaz, short_name AS kratki_naziv,
    registry AS registar, registry_id AS id_u_registru, registry_no AS registarski_broj,
    oib, status, status_date AS datum_statusa, registered_at AS datum_upisa,
    founded_at AS datum_osnivanja, legal_form AS pravni_oblik,
    category AS kategorija, catholic_confidence AS pouzdanost, catholic_score AS bodovi,
    catholic_signals AS signali,
    address AS sjediste, street AS ulica, housenumber AS kucni_broj, city AS mjesto,
    settlement AS naselje, municipality AS opcina_grad, county AS zupanija,
    postal_code AS postanski_broj, foreign_seat AS strano_sjediste,
    lat, lng, geo_source AS izvor_koordinata, diocese AS biskupija, diocese_source AS izvor_biskupije,
    email, website AS web, phone AS telefon, phone_e164 AS telefon_e164, iban,
    president AS predsjednik, president_role AS uloga_predsjednika,
    goals AS ciljevi, target_groups AS ciljane_skupine, activities AS djelatnosti,
    rno_url, source AS izvori
"""

EXPORTS = {
    "udruge.csv": f"SELECT {_COLS} FROM udruge WHERE catholic_confidence IN ('visoka','srednja') "
                  "ORDER BY county, city, name",
    "udruge-za-pregled.csv": f"SELECT {_COLS} FROM udruge WHERE catholic_confidence = 'niska' "
                             "ORDER BY catholic_score DESC, name",
}


def run() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        for fname, sql in EXPORTS.items():
            rows = conn.execute(sql).fetchall()
            path = OUT_DIR / fname
            with path.open("w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                if rows:
                    w.writerow(rows[0].keys())
                    w.writerows([tuple(r) for r in rows])
            log.info("%s: %d redaka", fname, len(rows))


if __name__ == "__main__":
    run()
