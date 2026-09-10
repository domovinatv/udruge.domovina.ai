"""Eksport u GeoJSON (data/exports/udruge.geojson) — ulaz za kartu.

Jedan FeatureCollection: sve udruge u katalogu (pouzdanost visoka + srednja)
koje imaju koordinate, SVIH statusa — `status` je property pa karta može
prikazati samo aktivne, a ugašene ostaju vidljive kao povijest ako se
zatraži. Udruge s pouzdanosti "niska" ne idu na kartu: to je red za pregled,
ne nalaz.

  uv run python scripts/31_export_geojson.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.db import connect  # noqa: E402
from src.katolicki import CATEGORIES  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("export-geojson")

OUT = ROOT / "data" / "exports" / "udruge.geojson"

SQL = """
SELECT id, slug, name, display_name, short_name, registry, oib, status, category,
       address, city, settlement, municipality, county, postal_code,
       lat, lng, geo_source, diocese, diocese_source,
       email, website, phone_e164, president, president_role,
       founded_at, registered_at, catholic_confidence, catholic_score, source
FROM udruge
WHERE lat IS NOT NULL AND lng IS NOT NULL
  AND catholic_confidence IN ('visoka', 'srednja')
ORDER BY id
"""


def run() -> None:
    with connect() as conn:
        rows = conn.execute(SQL).fetchall()
    feats = []
    for r in rows:
        p = {k: r[k] for k in r.keys() if k not in ("lat", "lng") and r[k] is not None}
        p["category_label"] = CATEGORIES.get(r["category"] or "ostalo", "Ostalo")
        p["active"] = 1 if (r["status"] or "").upper().startswith("AKTIV") else 0
        try:
            p["source"] = json.loads(r["source"]) if r["source"] else []
        except json.JSONDecodeError:
            pass
        feats.append({"type": "Feature",
                      "geometry": {"type": "Point", "coordinates": [round(r["lng"], 6), round(r["lat"], 6)]},
                      "properties": p})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False))
    log.info("%s: %d točaka (%d aktivnih)", OUT.name, len(feats),
             sum(f["properties"]["active"] for f in feats))


if __name__ == "__main__":
    run()
