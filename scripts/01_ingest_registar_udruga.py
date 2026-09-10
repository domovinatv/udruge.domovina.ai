"""Ingest katoličkih udruga iz Registra udruga RH (data.gov.hr).

Registar ima ~71 000 udruga i nikakvo polje "vjera". U katalog ulaze samo one
koje `src/katolicki.classify` ocijeni kao katoličke (pouzdanost visoka /
srednja / niska); ostale se ne pamte. Zato je ovaj korak i FILTAR i ingest,
i zato se na kraju BRIŠU zapisi ovog registra koje ovaj run nije potvrdio —
promjena pravila klasifikacije mora se odraziti na katalog, ne samo dodavati.

Osobe ovlaštene za zastupanje pišu se u `osobe` (zamjenom, ne spajanjem) i
predsjednik se izvlači u `udruge.president`.

  uv run python scripts/01_ingest_registar_udruga.py
"""
from __future__ import annotations

import logging
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.datagovhr import (REGISTAR_UDRUGA_CTS, REGISTAR_UDRUGA_DJEL,  # noqa: E402
                           REGISTAR_UDRUGA_OSOBE, fetch, split_sjediste, split_street)
from src.db import connect, merge_source, replace_osobe, upsert_udruga  # noqa: E402
from src.ingest import (REGISTRY_URL, assess, clean_email, clean_website,  # noqa: E402
                        index_djelatnosti, index_osobe, iso_date, pick_president)
from src.normalize import slugify, title_case_hr  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ingest-registar-udruga")

REGISTRY = "registar-udruga"
SOURCE = "datagovhr:registar-udruga"


def run() -> None:
    cts = fetch(REGISTAR_UDRUGA_CTS)
    osobe = index_osobe(fetch(REGISTAR_UDRUGA_OSOBE))
    djel = index_djelatnosti(fetch(REGISTAR_UDRUGA_DJEL))
    log.info("registar: %d udruga, %d s osobama, %d s djelatnostima", len(cts), len(osobe), len(djel))

    stats: Counter = Counter()
    seen_ids: set[int] = set()
    with connect() as conn:
        for r in cts:
            name = (r.get("NAZIV") or "").strip()
            udr_id = r.get("UDR_ID")
            if not name or udr_id is None:
                stats["bez_naziva"] += 1
                continue
            acts = djel.get(udr_id, [])
            a = assess(name, r.get("CILJEVI"), r.get("OPIS_DJELATNOSTI"),
                       r.get("CILJANE_SKUPINE"), acts)
            if a is None:
                stats["nije_katolicka"] += 1
                continue

            oib = (r.get("OIB") or "").strip() or None
            street_full, city = split_sjediste(r.get("SJEDISTE"))
            street, number = split_street(street_full)
            slug = slugify(name, city, suffix=oib[-4:] if oib else str(udr_id))
            existing = conn.execute(
                "SELECT slug, source FROM udruge WHERE registry = ? AND registry_id = ?",
                (REGISTRY, udr_id),
            ).fetchone()
            if existing:
                slug = existing["slug"]

            persons = osobe.get(udr_id, [])
            president, role = pick_president(persons)

            uid = upsert_udruga(
                conn, slug, name, REGISTRY,
                short_name=(r.get("SKRACENI_NAZIV") or "").strip() or None,
                display_name=title_case_hr(name),
                registry_id=udr_id,
                registry_no=(r.get("REGISTARSKI_BROJ") or "").strip() or None,
                registry_url=REGISTRY_URL,
                oib=oib,
                status=(r.get("STATUS") or "").strip() or None,
                status_date=iso_date(r.get("DATUM_STATUSA")),
                registered_at=iso_date(r.get("DATUM_UPISA")),
                founded_at=iso_date(r.get("DATUM_OSNIVACKE_SKUPSTINE")),
                legal_form=(r.get("OBLIK_UDRUZIVANJA") or "").strip() or None,
                goals=(r.get("CILJEVI") or "").strip() or None,
                activities_desc=(r.get("OPIS_DJELATNOSTI") or "").strip() or None,
                target_groups=(r.get("CILJANE_SKUPINE") or "").strip() or None,
                address=(r.get("SJEDISTE") or "").strip() or None,
                street=street, housenumber=number, city=city,
                county=(r.get("ZUPANIJA") or "").strip() or None,
                email=clean_email(r.get("MAIL")),
                website=clean_website(r.get("WEB_STRANICA")),
                president=president, president_role=role,
                source=merge_source(existing["source"] if existing else None, SOURCE),
                **a,
            )
            # Prosudba se UVIJEK prepisuje (COALESCE bi zadržao staru ocjenu).
            conn.execute(
                "UPDATE udruge SET catholic_score=?, catholic_confidence=?, catholic_signals=?, "
                "category=?, status=?, status_date=?, president=?, president_role=? WHERE id=?",
                (a["catholic_score"], a["catholic_confidence"], a["catholic_signals"],
                 a["category"], (r.get("STATUS") or "").strip() or None,
                 iso_date(r.get("DATUM_STATUSA")), president, role, uid),
            )
            replace_osobe(conn, uid, persons)
            seen_ids.add(udr_id)
            stats[a["catholic_confidence"]] += 1

        # Zapisi ovog registra koje ovaj run nije potvrdio — van. Inače bi
        # svaka ispravka klasifikatora ostavljala "duhove" iz prijašnjih runova.
        gone = [row["id"] for row in conn.execute(
            "SELECT id, registry_id FROM udruge WHERE registry = ?", (REGISTRY,))
            if row["registry_id"] not in seen_ids]
        for gid in gone:
            conn.execute("DELETE FROM udruge WHERE id = ?", (gid,))
        stats["obrisano_nepotvrdjeno"] = len(gone)
        conn.commit()
        n = conn.execute("SELECT COUNT(*) FROM udruge WHERE registry = ?", (REGISTRY,)).fetchone()[0]

    log.info("gotovo: %s", dict(stats))
    log.info("katoličkih udruga iz Registra udruga u bazi: %d", n)


if __name__ == "__main__":
    run()
