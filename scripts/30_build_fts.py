"""FTS5 indeks za pretragu bez dijakritike (naziv, mjesto, županija, kategorija, ciljevi).

Bez `content=`: indeksiraju se normalizirane (bez dijakritike) kopije, koje se
razlikuju od izvornih stupaca, pa external-content tablica ne bi bila
konzistentna. Rebuild svaki put — 1–2 tisuće redaka, trenutačno.

  uv run python scripts/30_build_fts.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.db import connect  # noqa: E402
from src.normalize import strip_diacritics  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("fts")


def run() -> None:
    with connect() as conn:
        conn.execute("DROP TABLE IF EXISTS udruge_fts")
        conn.execute(
            "CREATE VIRTUAL TABLE udruge_fts USING fts5("
            "slug UNINDEXED, name, short_name, city, county, category, goals, "
            "tokenize='unicode61')")
        rows = conn.execute(
            "SELECT slug, name, short_name, city, county, category, goals FROM udruge").fetchall()
        conn.executemany(
            "INSERT INTO udruge_fts VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(r["slug"], strip_diacritics(r["name"] or ""), strip_diacritics(r["short_name"] or ""),
              strip_diacritics(r["city"] or ""), strip_diacritics(r["county"] or ""),
              r["category"] or "", strip_diacritics((r["goals"] or "")[:2000])) for r in rows])
        conn.commit()
    log.info("FTS: %d zapisa", len(rows))


if __name__ == "__main__":
    run()
