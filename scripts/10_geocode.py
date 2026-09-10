"""Koordinate sjedišta: DGU adresna točka → težište naselja. Plus naselje,
općina, županija i biskupija prostorno.

Tri sloja preciznosti, svaki pošteno označen u `geo_source`:

  dgu-adresa        točka kućnog broja iz Registra prostornih jedinica (DGU WFS)
  dgu-ulica-fuzzy   ista ulica nađena fuzzy usporedbom naziva (RPJ piše
                    "Splitski put", registar "Splitska")
  naselje-teziste   nema pogotka na adresi → težište naselja iz DGU granica
                    (../karta-hrvatske); točnost razine mjesta

Zatim se za svaku točku odredi naselje/JLS/županija (`geo_hr.locate`) i
biskupija (`geo_hr.diocese_at`, iz DERIVIRANIH granica crkve.domovina.ai).
Županija iz registra se ne gazi — samo popunjava gdje je prazna (strane
udruge i evidencija KC je nemaju).

Bez ključa i bez kvote; ~1 s po adresi, keširano po upitu u data/raw/dgu/.

  uv run python scripts/10_geocode.py            # samo one bez koordinata
  uv run python scripts/10_geocode.py --refresh  # sve ponovno
"""
from __future__ import annotations

import argparse
import logging
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import dgu, geo_hr  # noqa: E402
from src.db import connect  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("geocode")
logging.getLogger("httpx").setLevel(logging.WARNING)

DIOCESE_SOURCE = "derivirano-crkve.domovina.ai"


def _settlement_variants(city: str | None) -> list[str]:
    """'Rovinj - Rovigno' → ['Rovinj - Rovigno', 'Rovinj']; 'Sv. Filip i Jakov' → + 'Sveti …'."""
    if not city:
        return []
    out = [city]
    if " - " in city:
        out.append(city.split(" - ")[0].strip())
    if city.lower().startswith("sv. "):
        out.append("Sveti " + city[4:])
    return out


def geocode_one(row: dict) -> tuple[int, dict | None]:
    for settlement in _settlement_variants(row["city"]):
        hit = dgu.geocode(settlement, row["street"], row["housenumber"])
        if hit:
            return row["id"], {"lat": hit.lat, "lng": hit.lng, "geo_source": hit.source,
                               "postal_code": hit.postal_code}
    for settlement in _settlement_variants(row["city"]):
        c = geo_hr.settlement_centroid(settlement, row["county"])
        if c:
            return row["id"], {"lat": c[0], "lng": c[1], "geo_source": "naselje-teziste",
                               "postal_code": None}
    return row["id"], None


def run(refresh: bool, workers: int) -> None:
    with connect() as conn:
        where = "" if refresh else "WHERE lat IS NULL"
        rows = [dict(r) for r in conn.execute(
            f"SELECT id, name, street, housenumber, city, county FROM udruge {where}")]
        log.info("za geokodirati: %d (refresh=%s)", len(rows), refresh)

        stats: Counter = Counter()
        with ThreadPoolExecutor(max_workers=workers) as ex:
            for i, (uid, res) in enumerate(ex.map(geocode_one, rows), 1):
                if res:
                    conn.execute(
                        "UPDATE udruge SET lat=?, lng=?, geo_source=?, "
                        "postal_code=COALESCE(?, postal_code), updated_at=CURRENT_TIMESTAMP WHERE id=?",
                        (res["lat"], res["lng"], res["geo_source"], res["postal_code"], uid))
                    stats[res["geo_source"]] += 1
                else:
                    stats["bez_koordinata"] += 1
                if i % 100 == 0:
                    conn.commit()
                    log.info("  %d/%d %s", i, len(rows), dict(stats))
        conn.commit()

        # Prostorni atributi za sve s koordinatama (jeftino, offline).
        loc_stats: Counter = Counter()
        for r in conn.execute("SELECT id, lat, lng, county, diocese FROM udruge WHERE lat IS NOT NULL").fetchall():
            place = geo_hr.locate(r["lat"], r["lng"])
            diocese = geo_hr.diocese_at(r["lat"], r["lng"])
            conn.execute(
                "UPDATE udruge SET settlement=?, municipality=?, county=COALESCE(county, ?), "
                "diocese=COALESCE(diocese, ?), "
                "diocese_source=CASE WHEN diocese IS NULL AND ? IS NOT NULL THEN ? ELSE diocese_source END "
                "WHERE id=?",
                (place.settlement, place.municipality, place.county,
                 diocese, diocese, DIOCESE_SOURCE, r["id"]))
            loc_stats["naselje" if place.settlement else "bez_naselja"] += 1
            loc_stats["biskupija" if (diocese or r["diocese"]) else "bez_biskupije"] += 1
        conn.commit()
    log.info("geokodiranje: %s", dict(stats))
    log.info("prostorni atributi: %s", dict(loc_stats))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    run(a.refresh, a.workers)
