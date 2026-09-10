"""Izvještaj o pokrivenosti — mjerni instrument projekta (README tablica,
data/exports/stats.json za frontend, i provjera da novi run nije nešto pokvario).

  uv run python scripts/40_stats.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.db import ACTIVE_SQL, connect  # noqa: E402
from src.katolicki import CATEGORIES  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stats")

OUT = ROOT / "data" / "exports" / "stats.json"

# "Katalog" = pouzdanost visoka ili srednja. Niska je red za pregled i broji se zasebno.
KATALOG = "catholic_confidence IN ('visoka','srednja')"


def run() -> None:
    with connect() as conn:
        q = lambda sql, *a: conn.execute(sql, a).fetchone()[0]  # noqa: E731
        grp = lambda sql: {(r[0] or "?"): r[1] for r in conn.execute(sql)}  # noqa: E731
        K, A = KATALOG, ACTIVE_SQL
        stats = {
            "udruge_katalog": q(f"SELECT COUNT(*) FROM udruge WHERE {K}"),
            "udruge_aktivne": q(f"SELECT COUNT(*) FROM udruge WHERE {K} AND {A}"),
            "udruge_ugasene": q(f"SELECT COUNT(*) FROM udruge WHERE {K} AND NOT ({A})"),
            "za_pregled_niska": q("SELECT COUNT(*) FROM udruge WHERE catholic_confidence = 'niska'"),
            "po_pouzdanosti": grp("SELECT catholic_confidence, COUNT(*) FROM udruge GROUP BY 1"),
            "po_registru": grp(f"SELECT registry, COUNT(*) FROM udruge WHERE {K} GROUP BY 1"),
            "po_registru_aktivne": grp(f"SELECT registry, COUNT(*) FROM udruge WHERE {K} AND {A} GROUP BY 1"),
            "s_koordinatama": q(f"SELECT COUNT(*) FROM udruge WHERE {K} AND lat IS NOT NULL"),
            "po_izvoru_koordinata": grp(f"SELECT geo_source, COUNT(*) FROM udruge WHERE {K} AND lat IS NOT NULL GROUP BY 1 ORDER BY 2 DESC"),
            "s_biskupijom": q(f"SELECT COUNT(*) FROM udruge WHERE {K} AND diocese IS NOT NULL"),
            "s_oib": q(f"SELECT COUNT(*) FROM udruge WHERE {K} AND oib IS NOT NULL"),
            "s_emailom": q(f"SELECT COUNT(*) FROM udruge WHERE {K} AND {A} AND email IS NOT NULL"),
            "s_webom": q(f"SELECT COUNT(*) FROM udruge WHERE {K} AND {A} AND website IS NOT NULL"),
            "s_telefonom": q(f"SELECT COUNT(*) FROM udruge WHERE {K} AND {A} AND phone IS NOT NULL"),
            "s_predsjednikom": q(f"SELECT COUNT(*) FROM udruge WHERE {K} AND {A} AND president IS NOT NULL"),
            "s_rno": q(f"SELECT COUNT(*) FROM udruge WHERE {K} AND rno_id IS NOT NULL"),
            "po_kategoriji_aktivne": {
                k: {"label": CATEGORIES.get(k, k), "n": n} for k, n in
                grp(f"SELECT category, COUNT(*) FROM udruge WHERE {K} AND {A} GROUP BY 1 ORDER BY 2 DESC").items()},
            "po_zupaniji_aktivne": grp(f"SELECT county, COUNT(*) FROM udruge WHERE {K} AND {A} GROUP BY 1 ORDER BY 2 DESC"),
            "po_biskupiji_aktivne": grp(f"SELECT diocese, COUNT(*) FROM udruge WHERE {K} AND {A} GROUP BY 1 ORDER BY 2 DESC"),
            "osobe": q("SELECT COUNT(*) FROM osobe"),
        }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(stats, ensure_ascii=False, indent=2))
    for k, v in stats.items():
        if isinstance(v, dict):
            log.info("%-24s %s", k, json.dumps(v, ensure_ascii=False)[:160])
        else:
            log.info("%-24s %s", k, v)


if __name__ == "__main__":
    run()
