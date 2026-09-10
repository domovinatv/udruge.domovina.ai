"""Eksportiraj katalog u statički JSON za vlastiti frontend (udruge.domovina.ai).

Piše u `frontend/public/data/`, odakle ga Worker poslužuje kao asset — bez
baze, bez bindinga, bez ključa. Isti obrazac kao ../crkve.domovina.ai/scripts/34.

    udruga/<slug>.json     detalj jedne udruge (katalog: pouzdanost visoka +
                           srednja, SVI statusi — ugašena udruga je i dalje
                           podatak, stranica kaže da je ugašena)
    udruge-index.json      slim zapis po udruzi — karta, popis, pretraga
    stats.json             kopija mjere iz `make stats` (brojke se NE računaju ovdje)
    manifest.json          generated_at, brojke, schema_version

Pouzdanost "niska" NEMA stranicu: to je red za pregled, ne nalaz. Izvozi se
samo kao `udruge-za-pregled.csv` (scripts/32).

TRAŽI PRETHODNI `make stats` i provjerava svježinu — dvije brojke koje se
računaju na dva mjesta uvijek se raziđu.

    uv run python scripts/34_export_static.py
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.db import connect  # noqa: E402
from src.katolicki import CATEGORIES  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("export-static")

OUT_DIR = ROOT / "frontend" / "public" / "data"
STATS_SRC = ROOT / "data" / "exports" / "stats.json"
SCHEMA_VERSION = 1

SQL = """
SELECT u.id, u.slug, u.name, u.display_name, u.short_name, u.registry, u.registry_id,
       u.registry_no, u.registry_url, u.oib, u.status, u.status_date, u.registered_at,
       u.founded_at, u.legal_form, u.goals, u.activities_desc, u.target_groups,
       u.activities, u.areas, u.address, u.street, u.housenumber, u.city, u.settlement,
       u.municipality, u.county, u.postal_code, u.foreign_seat, u.lat, u.lng, u.geo_source,
       u.diocese, u.diocese_source, u.email, u.website, u.phone, u.phone_e164, u.iban,
       u.rno_url, u.president, u.president_role, u.catholic_score, u.catholic_confidence,
       u.catholic_signals, u.category, u.source
FROM udruge u
WHERE u.catholic_confidence IN ('visoka', 'srednja')
ORDER BY u.name
"""

OSOBE_SQL = """
SELECT udruga_id, ime, prezime, funkcija, svojstvo FROM osobe
WHERE funkcija IS NULL OR funkcija NOT LIKE '%LIKVIDATOR%'
ORDER BY udruga_id, id
"""

_JSON_COLS = {"activities", "areas", "catholic_signals", "source"}


def _clean(row) -> dict:
    out = {}
    for k in row.keys():
        v = row[k]
        if v is None or v == "":
            continue
        if k in _JSON_COLS and isinstance(v, str):
            try:
                v = json.loads(v)
            except json.JSONDecodeError:
                pass
        out[k] = v
    return out


def _write(path: Path, payload) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    path.write_text(body, encoding="utf-8")
    return len(body.encode("utf-8"))


def _purge_stale(dirname: str, keep: set[str]) -> int:
    """Obriši per-slug datoteke kojih više nema — inače obrisan slug ostavlja
    živu stranicu koju nitko ne linka, a Worker je i dalje poslužuje."""
    d = OUT_DIR / dirname
    if not d.exists():
        return 0
    removed = 0
    for f in d.glob("*.json"):
        if f.stem not in keep:
            f.unlink()
            removed += 1
    return removed


def _name_case(ime: str | None, prezime: str | None) -> str:
    def cap(t: str) -> str:
        return "-".join(p[:1].upper() + p[1:].lower() for p in t.split("-"))
    return " ".join(cap(t) for t in f"{ime or ''} {prezime or ''}".split())


def run() -> None:
    if not STATS_SRC.exists():
        raise SystemExit(f"{STATS_SRC} ne postoji — pokreni `make stats` prije ovog koraka.")
    stats = json.loads(STATS_SRC.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with connect() as conn:
        live = conn.execute(
            "SELECT COUNT(*) FROM udruge WHERE catholic_confidence IN ('visoka','srednja')"
        ).fetchone()[0]
        if stats.get("udruge_katalog") != live:
            raise SystemExit(
                f"stats.json je zastario ({stats.get('udruge_katalog')}) naspram baze ({live}) "
                "— pokreni `make stats` pa ponovo ovo."
            )
        rows = conn.execute(SQL).fetchall()
        osobe: dict[int, list[dict]] = {}
        for o in conn.execute(OSOBE_SQL):
            osobe.setdefault(o["udruga_id"], []).append({
                "name": _name_case(o["ime"], o["prezime"]),
                **({"role": (o["svojstvo"] or o["funkcija"]).capitalize()} if (o["svojstvo"] or o["funkcija"]) else {}),
            })

    index: list[dict] = []
    for r in rows:
        d = _clean(r)
        d.pop("id", None)
        d["active"] = 1 if (r["status"] or "").upper().startswith("AKTIV") else 0
        d["category_label"] = CATEGORIES.get(r["category"] or "ostalo", "Ostalo")
        people = osobe.get(r["id"], [])
        if people:
            d["people"] = people
        _write(OUT_DIR / "udruga" / f"{r['slug']}.json", d)

        item = {
            "slug": r["slug"],
            "name": r["display_name"] or r["name"],
            "category": r["category"] or "ostalo",
            "active": d["active"],
            "confidence": r["catholic_confidence"],
            "registry": r["registry"],
        }
        for key in ("city", "county", "diocese"):
            if r[key]:
                item[key] = r[key]
        if r["lat"] is not None:
            item["lat"], item["lng"] = round(r["lat"], 6), round(r["lng"], 6)
        if r["email"] or r["phone"] or r["website"]:
            item["contact"] = 1
        index.append(item)

    stale = _purge_stale("udruga", {r["slug"] for r in rows})
    if stale:
        log.info("udruga/: obrisano %d zaostalih datoteka", stale)

    sizes = {
        "udruge-index.json": _write(OUT_DIR / "udruge-index.json", {"count": len(index), "items": index}),
        "stats.json": _write(OUT_DIR / "stats.json", stats),
        "kategorije.json": _write(OUT_DIR / "kategorije.json", CATEGORIES),
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "counts": {
            "udruge": len(index),
            "aktivne": sum(i["active"] for i in index),
            "s_koordinatama": sum(1 for i in index if "lat" in i),
        },
    }
    sizes["manifest.json"] = _write(OUT_DIR / "manifest.json", manifest)
    log.info("udruga/: %d datoteka", len(rows))
    for name, size in sizes.items():
        log.info("%-20s %6.1f KB", name, size / 1024)


if __name__ == "__main__":
    run()
