"""Ingest katoličkih STRANIH udruga (Registar stranih udruga, data.gov.hr).

Strane udruge s podružnicom u RH: Pax Christi, Kolping, Comunità Papa
Giovanni XXIII… Registar je malen (~220 zapisa, 155 aktivnih) i ima drukčija
polja: nema ciljeva ni ciljanih skupina, opis djelatnosti je
OPIS_DJELATNOSTI_KOJE_OBAVLJA_U_RH, sjedište je SJEDISTE_U_RH plus
STRANO_SJEDISTE, a status "AKTIVNA" (ž. rod). Klasifikacija je ista.

  uv run python scripts/02_ingest_strane_udruge.py
"""
from __future__ import annotations

import logging
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.datagovhr import (STRANE_UDRUGE_CTS, STRANE_UDRUGE_DJEL,  # noqa: E402
                           STRANE_UDRUGE_OSOBE, fetch, split_sjediste, split_street)
from src.db import connect, merge_source, replace_osobe, upsert_udruga  # noqa: E402
from src.ingest import (assess, index_djelatnosti, index_osobe, iso_date,  # noqa: E402
                        pick_president)
from src.normalize import slugify, title_case_hr  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ingest-strane-udruge")

REGISTRY = "strane-udruge"
SOURCE = "datagovhr:strane-udruge"
REGISTRY_URL = "https://registri-npo-mpu.gov.hr/#!strane-udruge"


def run() -> None:
    cts = fetch(STRANE_UDRUGE_CTS)
    osobe = index_osobe(fetch(STRANE_UDRUGE_OSOBE))
    djel = index_djelatnosti(fetch(STRANE_UDRUGE_DJEL), code_key="DJELATNOSTI_KOJE_OBAVLJA_U_RH")
    log.info("strane udruge: %d zapisa", len(cts))

    stats: Counter = Counter()
    seen_ids: set[int] = set()
    with connect() as conn:
        for r in cts:
            name = (r.get("NAZIV") or "").strip()
            udr_id = r.get("UDR_ID")
            if not name or udr_id is None:
                continue
            desc = r.get("OPIS_DJELATNOSTI_KOJE_OBAVLJA_U_RH")
            a = assess(name, None, desc, None, djel.get(udr_id, []))
            if a is None:
                stats["nije_katolicka"] += 1
                continue
            oib = (r.get("OIB") or "").strip() or None
            street_full, city = split_sjediste(r.get("SJEDISTE_U_RH"))
            street, number = split_street(street_full)
            slug = slugify(name, city, suffix=oib[-4:] if oib else str(udr_id))
            existing = conn.execute(
                "SELECT slug, source FROM udruge WHERE registry = ? AND registry_id = ?",
                (REGISTRY, udr_id)).fetchone()
            if existing:
                slug = existing["slug"]
            persons = osobe.get(udr_id, [])
            president, role = pick_president(persons)
            status = (r.get("STATUS") or "").strip() or None
            uid = upsert_udruga(
                conn, slug, name, REGISTRY,
                short_name=(r.get("SKRACENI_NAZIV") or "").strip() or None,
                display_name=title_case_hr(name),
                registry_id=udr_id,
                registry_no=(r.get("REGISTARSKI_BROJ") or "").strip() or None,
                registry_url=REGISTRY_URL,
                oib=oib, status=status,
                status_date=iso_date(r.get("DATUM_STATUSA")),
                registered_at=iso_date(r.get("DATUM_UPISA")),
                legal_form="STRANA UDRUGA",
                activities_desc=(desc or "").strip() or None,
                address=(r.get("SJEDISTE_U_RH") or "").strip() or None,
                street=street, housenumber=number, city=city,
                county=(r.get("ZUPANIJA") or "").strip() or None,
                foreign_seat=(r.get("STRANO_SJEDISTE") or "").strip() or None,
                president=president, president_role=role,
                source=merge_source(existing["source"] if existing else None, SOURCE),
                **a,
            )
            conn.execute(
                "UPDATE udruge SET display_name=?, catholic_score=?, catholic_confidence=?, catholic_signals=?, "
                "category=?, status=?, president=?, president_role=? WHERE id=?",
                (title_case_hr(name), a["catholic_score"], a["catholic_confidence"], a["catholic_signals"],
                 a["category"], status, president, role, uid))
            replace_osobe(conn, uid, persons)
            seen_ids.add(udr_id)
            stats[a["catholic_confidence"]] += 1
        gone = [row["id"] for row in conn.execute(
            "SELECT id, registry_id FROM udruge WHERE registry = ?", (REGISTRY,))
            if row["registry_id"] not in seen_ids]
        for gid in gone:
            conn.execute("DELETE FROM udruge WHERE id = ?", (gid,))
        stats["obrisano_nepotvrdjeno"] = len(gone)
        conn.commit()
    log.info("gotovo: %s", dict(stats))


if __name__ == "__main__":
    run()
