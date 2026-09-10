"""Ingest vjerničkih društava, pokreta i zajednica iz Evidencije pravnih
osoba Katoličke Crkve (data.gov.hr).

Dio katoličkih laičkih udruženja NIJE u Registru udruga: upisani su kao
crkvene pravne osobe (kan. 298–329 ZKP — javna i privatna vjernička
društva) u evidenciju koju vodi isto Ministarstvo. Fokolari, Omnia Deo,
RINO, Marijina legija… Bez ovog izvora katalog bi ih propustio, a upravo
su to udruge koje su "najkatoličkije" — Crkva im je sama dala pravnu
osobnost.

Iz evidencije se uzimaju SAMO zapisi koji su udruženja vjernika: naziv
odaje DRUŠTVO / POKRET / ZAJEDNICA / BRATOVŠTINA / UDRUGA / LEGIJA / DJELO,
a ne župa, samostan, biskupija, provincija, škola, dom, centar ili ustanova
(to je ../crkve.domovina.ai). Klasifikacija je trivijalna — evidencija je
katolička po definiciji — pa je pouzdanost 'visoka' sa signalom
'registar:evidencija-kc'.

  uv run python scripts/03_ingest_evidencija_kc.py
"""
from __future__ import annotations

import json
import logging
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.datagovhr import KATOLICKE_PRAVNE_OSOBE, fetch, split_street  # noqa: E402
from src.db import connect, merge_source, upsert_udruga  # noqa: E402
from src.ingest import iso_date  # noqa: E402
from src.katolicki import categorize  # noqa: E402
from src.normalize import slugify, title_case_hr  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ingest-evidencija-kc")

REGISTRY = "evidencija-kc"
SOURCE = "datagovhr:katolicke-pravne-osobe"
REGISTRY_URL = "https://registri-npo-mpu.gov.hr/#!vjerske-zajednice"

# Što JEST udruženje vjernika (u nazivu)…
_INCLUDE = re.compile(
    r"\b(DRUŠTVO|DRUŠTVA|POKRET|ZAJEDNICA|BRATOVŠTINA|UDRUGA|UDRUŽENJE|LEGIJA|DJELO|"
    r"SAVEZ|ZBOR|KRUG|BRATSTVO|FRAMA|FRANJEVAČKI SVJETOVNI RED|SVJETOVNI RED|TREĆI RED|"
    r"ODRED|SKAUTI|MLADEŽ|MLADI|OBITELJI|VJERNIKA|VJERNICI)\b", re.I)
# …a što nije, ma što u nazivu pisalo.
_EXCLUDE = re.compile(
    r"^\s*(ŽUPA|NADBISKUPIJA|BISKUPIJA|SAMOSTAN|PROVINCIJA|KUSTODIJA|CARITAS|SVETIŠTE|"
    r"REZIDENCIJA|KARMEL|OPATIJA|DRUŽBA|KONGREGACIJA|RED |REDOVNIČKA|SESTRE|KĆERI|SLUŽBENICE|"
    r"KLANJATELJICE|MILOSRDNICE|BRAĆA|MISIONARI|MISIONARKE)\b|"
    r"\b(ŠKOLA|GIMNAZIJA|VRTIĆ|UČILIŠTE|FAKULTET|SVEUČILIŠTE|SJEMENIŠTE|BOGOSLOVIJA|KOLEGIJ|"
    r"SAMOSTAN|PROVINCIJA|SESTRE|SESTARA|DRUŽBA|LAZARIST\w*|PREBENDAR\w*|POPOVSKI|KANONI[KC]\w*|"
    r"SALEZIJANSKA ZAJEDNICA|ISUSOVAČKA ZAJEDNICA|REDOVNIČKA ZAJEDNICA|"
    r"INSTITUT|CENTAR|DOM\b|ZAKLADA|NAKLADA|GLASNIK|RADIO|TISKARA|KAPTOL|ORDINARIJAT|"
    r"VIKARIJAT|DEKANAT|ŽUPNI URED|SAMOSTANA|PROVINCIJE|BISKUPIJE|NADBISKUPIJE|ŽUPE\b)",
    re.I)


# Nazivi koji su udruženje vjernika unatoč riječi iz _EXCLUDE ("Roditeljski
# INSTITUT" je vjerničko društvo; FSR "mjesno bratstvo KAPTOL" je mjesto).
_FORCE = re.compile(
    r"VJERNIČKO DRUŠTVO|FRANJEVAČKI SVJETOVNI RED|SVJETOVNI RED|KURSILJ|POKRET FOKOLARA|"
    r"SALEZIJANACA SURADNIKA|MARIJINA LEGIJA|LEGIJA MARIJINA", re.I)


def is_lay_association(name: str) -> bool:
    if _FORCE.search(name):
        return True
    if _EXCLUDE.search(name):
        return False
    return bool(_INCLUDE.search(name))


def _split_kc_sjediste(s: str | None) -> tuple[str | None, str | None]:
    """Evidencija KC piše 'MJESTO, Ulica broj' — obrnuto od Registra udruga."""
    if not s:
        return None, None
    parts = [p.strip() for p in s.split(",")]
    if len(parts) == 1:
        return None, parts[0] or None
    return ", ".join(parts[1:]).strip() or None, parts[0] or None


def run() -> None:
    rows = fetch(KATOLICKE_PRAVNE_OSOBE)
    stats: Counter = Counter()
    seen: set[int] = set()
    with connect() as conn:
        for r in rows:
            name = (r.get("NAZIV") or "").strip()
            sbt = r.get("SBT_ID")
            if not name or not is_lay_association(name):
                stats["preskoceno"] += 1
                continue
            oib = (r.get("OIB") or "").strip() or None
            street_full, city = _split_kc_sjediste(r.get("SJEDISTE"))
            street, number = split_street(street_full)
            rid = int(sbt) if sbt is not None else None
            slug = slugify(name, city, suffix=oib[-4:] if oib else str(rid))
            existing = None
            if rid is not None:
                existing = conn.execute(
                    "SELECT slug, source FROM udruge WHERE registry = ? AND registry_id = ?",
                    (REGISTRY, rid)).fetchone()
            if existing:
                slug = existing["slug"]
            status = (r.get("STATUS") or "").strip() or None
            diocese = (r.get("BISKUPIJA_NADBISKUPIJA") or "").strip() or None
            uid = upsert_udruga(
                conn, slug, name, REGISTRY,
                display_name=title_case_hr(name),
                registry_id=rid,
                registry_no=(r.get("EVIDENCIJSKI_BROJ") or "").strip() or None,
                registry_url=REGISTRY_URL,
                oib=oib, status=status,
                registered_at=iso_date(r.get("DATUM_UPISA")),
                legal_form="VJERNIČKO DRUŠTVO (crkvena pravna osoba)",
                address=(r.get("SJEDISTE") or "").strip() or None,
                street=street, housenumber=number, city=city,
                diocese=title_case_hr(diocese) if diocese else None,
                diocese_source="evidencija-kc" if diocese else None,
                president_role=(r.get("SLUZBA_OSOBE") or "").strip() or None,
                catholic_score=10.0, catholic_confidence="visoka",
                catholic_signals=json.dumps(["registar:evidencija-kc"]),
                category=categorize(name),
                source=merge_source(existing["source"] if existing else None, SOURCE),
            )
            conn.execute("UPDATE udruge SET status=?, category=? WHERE id=?",
                         (status, categorize(name), uid))
            if rid is not None:
                seen.add(rid)
            stats["ok"] += 1
            log.info("  + %s | %s", name, city)
        gone = [row["id"] for row in conn.execute(
            "SELECT id, registry_id FROM udruge WHERE registry = ?", (REGISTRY,))
            if row["registry_id"] not in seen]
        for gid in gone:
            conn.execute("DELETE FROM udruge WHERE id = ?", (gid,))
        stats["obrisano_nepotvrdjeno"] = len(gone)
        conn.commit()
    log.info("gotovo: %s", dict(stats))


if __name__ == "__main__":
    run()
