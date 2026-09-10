"""SQLite shema + upsert helperi za katalog katoličkih udruga.

Prilagođeno iz ../crkve.domovina.ai/src/db.py (isti obrazac: slug je prirodni
ključ, upsert je idempotentan, `source` je JSON array pa se zna odakle je što
došlo, a `COALESCE(excluded.x, table.x)` čuva ono što je raniji korak upisao).

Jedna glavna tablica, `udruge`, jer su sve tri vrste zapisa ista stvar —
pravna osoba koja okuplja katolike — samo iz tri registra:

  registry = 'registar-udruga'   civilna udruga po Zakonu o udrugama
  registry = 'strane-udruge'     strana udruga s podružnicom u RH (Pax Christi…)
  registry = 'evidencija-kc'     vjerničko društvo / pokret / zajednica upisana
                                 kao crkvena pravna osoba, ne kao udruga
                                 (Fokolari, Omnia Deo, RINO). Nije u Registru
                                 udruga i bez ovog izvora bi nedostajala.

Sve što je NAŠA prosudba, a ne podatak iz registra, nosi vlastite kolone:
`catholic_*` (je li katolička i zašto), `category`, `geo_source`,
`diocese_source`. Potrošač mora moći razlikovati "država kaže" od "mi mislimo".
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "udruge.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS udruge (
  id              INTEGER PRIMARY KEY,
  slug            TEXT UNIQUE NOT NULL,
  name            TEXT NOT NULL,       -- NAZIV kako stoji u registru
  short_name      TEXT,                -- SKRACENI_NAZIV
  display_name    TEXT,                -- naziv u čitljivom obliku (title case)

  -- Registar iz kojeg zapis dolazi
  registry        TEXT NOT NULL,       -- registar-udruga | strane-udruge | evidencija-kc
  registry_id     INTEGER,             -- UDR_ID / SBT_ID
  registry_no     TEXT,                -- REGISTARSKI_BROJ / EVIDENCIJSKI_BROJ
  registry_url    TEXT,                -- link na javni pregled zapisa
  oib             TEXT,
  status          TEXT,                -- AKTIVAN | BRISAN | PRESTANAK DJELOVANJA
  status_date     TEXT,
  registered_at   TEXT,                -- DATUM_UPISA
  founded_at      TEXT,                -- DATUM_OSNIVACKE_SKUPSTINE
  legal_form      TEXT,                -- OBLIK_UDRUZIVANJA (udruga / savez udruga…)

  -- Što radi (iz registra)
  goals           TEXT,                -- CILJEVI
  activities_desc TEXT,                -- OPIS_DJELATNOSTI
  target_groups   TEXT,                -- CILJANE_SKUPINE
  activities      TEXT,                -- JSON: ["3.1.1. Promicanje religijske etike", …]
  areas           TEXT,                -- JSON: ["3. DUHOVNOST", …]

  -- Sjedište
  address         TEXT,                -- SJEDISTE kako stoji u registru
  street          TEXT,
  housenumber     TEXT,
  city            TEXT,
  county          TEXT,
  postal_code     TEXT,
  foreign_seat    TEXT,                -- STRANO_SJEDISTE (samo strane udruge)
  lat             REAL,
  lng             REAL,
  geo_source      TEXT,                -- dgu-adresa | dgu-ulica-fuzzy | naselje-teziste
  settlement      TEXT,                -- naselje (prostorno, iz DGU granica)
  municipality    TEXT,                -- općina/grad (prostorno)
  diocese         TEXT,                -- (nad)biskupija, prostorno iz deriviranih granica
  diocese_source  TEXT,

  -- Kontakt
  email           TEXT,
  website         TEXT,
  phone           TEXT,
  phone_kind      TEXT,
  phone_e164      TEXT,
  iban            TEXT,
  rno_id          TEXT,                -- Registar neprofitnih organizacija (MFIN)
  rno_url         TEXT,
  president       TEXT,                -- osoba ovlaštena za zastupanje (javno)
  president_role  TEXT,

  -- NAŠA prosudba
  catholic_score       REAL,
  catholic_confidence  TEXT,           -- visoka | srednja | niska
  catholic_signals     TEXT,           -- JSON: ["naziv:katolic", "djelatnost:3.1.1", …]
  category             TEXT,           -- src/katolicki.CATEGORIES

  source          TEXT,                -- JSON array izvora
  notes           TEXT,
  created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at      TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_udruge_oib ON udruge(oib);
CREATE INDEX IF NOT EXISTS idx_udruge_registry ON udruge(registry, registry_id);
CREATE INDEX IF NOT EXISTS idx_udruge_status ON udruge(status);
CREATE INDEX IF NOT EXISTS idx_udruge_county ON udruge(county);
CREATE INDEX IF NOT EXISTS idx_udruge_category ON udruge(category);

-- Osobe ovlaštene za zastupanje. Registar ih objavljuje javno (čl. 24 Zakona
-- o udrugama); mi ih preuzimamo kakve jesu i ne obogaćujemo ničim.
CREATE TABLE IF NOT EXISTS osobe (
  id          INTEGER PRIMARY KEY,
  udruga_id   INTEGER NOT NULL REFERENCES udruge(id) ON DELETE CASCADE,
  ime         TEXT,
  prezime     TEXT,
  funkcija    TEXT,                    -- OSOBA OVLAŠTENA ZA ZASTUPANJE | LIKVIDATOR
  svojstvo    TEXT,                    -- PREDSJEDNIK | TAJNIK | …
  vrsta       TEXT,                    -- FIZICKA | PRAVNA
  UNIQUE(udruga_id, ime, prezime, funkcija, svojstvo)
);
"""


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path = DB_PATH) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def merge_source(existing: str | None, new: str) -> str:
    """Dodaj izvor u JSON array bez duplikata, stabilnim redoslijedom."""
    try:
        cur = json.loads(existing) if existing else []
    except (json.JSONDecodeError, TypeError):
        cur = []
    if new not in cur:
        cur.append(new)
    return json.dumps(cur, ensure_ascii=False)


def _upsert(conn: sqlite3.Connection, table: str, key: str, key_val, fields: dict) -> int:
    """INSERT … ON CONFLICT(key) DO UPDATE … RETURNING id.

    None vrijednosti NE brišu postojeće: ingest (registar) ide prije geokodera
    i RNO-a, a ponovni ingest ne smije obrisati koordinate i telefon koje su
    kasniji koraci upisali. Zato `COALESCE(excluded.x, table.x)`.
    """
    cols = [key, *fields.keys()]
    vals = [key_val, *fields.values()]
    placeholders = ", ".join(["?"] * len(cols))
    updates = ", ".join(
        f"{c}=COALESCE(excluded.{c}, {table}.{c})" for c in cols if c != key
    )
    sql = (
        f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT({key}) DO UPDATE SET {updates}, updated_at=CURRENT_TIMESTAMP "
        "RETURNING id"
    )
    return conn.execute(sql, vals).fetchone()["id"]


def upsert_udruga(conn: sqlite3.Connection, slug: str, name: str, registry: str, **fields) -> int:
    return _upsert(conn, "udruge", "slug", slug, {"name": name, "registry": registry, **fields})


def replace_osobe(conn: sqlite3.Connection, udruga_id: int, osobe: list[dict]) -> None:
    """Osobe se ne spajaju nego zamjenjuju — registar je jedini izvor i
    likvidator koji je jučer bio upisan danas više nije."""
    conn.execute("DELETE FROM osobe WHERE udruga_id = ?", (udruga_id,))
    for o in osobe:
        conn.execute(
            "INSERT OR IGNORE INTO osobe (udruga_id, ime, prezime, funkcija, svojstvo, vrsta) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (udruga_id, o.get("ime"), o.get("prezime"), o.get("funkcija"),
             o.get("svojstvo"), o.get("vrsta")),
        )


# Uvjet "aktivna" — ista fraza u exportu, statistici i frontendu, da se brojke
# ne raziđu. Registar stranih udruga piše "AKTIVNA" (ž. rod), domaći "AKTIVAN".
ACTIVE_SQL = "status LIKE 'AKTIV%'"
