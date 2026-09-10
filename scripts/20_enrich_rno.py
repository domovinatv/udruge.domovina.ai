"""Kontakti iz Registra neprofitnih organizacija (RNO, Ministarstvo financija).

banovac.mfin.hr/rnoprt je običan ASP.NET Razor — bez captche, bez tokena —
za razliku od Vaadin SPA-a Registra udruga. Po OIB-u daje telefon, e-mail,
web, IBAN i osobu za kontakt: sve ono što Registar udruga NEMA (on ima samo
MAIL i WEB_STRANICA, i to rijetko popunjeno). Preneseno iz
../klubovi.domovina.ai/scripts/25_ingest_rno.py.

Puni SAMO PRAZNA polja (Registar udruga ima prednost jer je primarni izvor),
a `rno_id`/`rno_url` uvijek osvježava. Sirovi odgovori u data/raw/rno/.
Nije u `make all` nego u `make rno`: ~2 zahtjeva po udruzi, pristojan tempo.

  uv run python scripts/20_enrich_rno.py            # sve s OIB-om bez rno_id
  uv run python scripts/20_enrich_rno.py --limit 20
  uv run python scripts/20_enrich_rno.py --refresh
"""
from __future__ import annotations

import argparse
import html
import json
import logging
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.db import connect  # noqa: E402
from src.ingest import clean_email, clean_website, person_name  # noqa: E402
from src.phones import classify, to_e164  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("rno")
logging.getLogger("httpx").setLevel(logging.WARNING)

BASE = "https://banovac.mfin.hr/rnoprt/"
CACHE = ROOT / "data" / "raw" / "rno"
SEARCH_BODY = ('{"draw":1,"start":0,"length":10,"order":[{"column":0,"dir":"asc"}],'
               '"columns":[],"search":{"value":"","regex":false}}')
FIELD_LABELS = {
    "13": ("adresa", "Adresa sjedišta"),
    "17": ("iban", "Račun (IBAN)"),
    "19": ("kontakt", "Osoba za kontakt"),
    "21": ("telefon", "Telefon"),
    "23": ("email", "e-mail"),
    "24": ("web", "Web stranica"),
    "25": ("zastupnik", "Ime i prezime"),
}
SECTION_CUT = re.compile(r"\s+(PODACI O |OSNOVNI PODACI|IZVJE|POVEZANI|OPCIJE)", re.I)


def session() -> httpx.Client:
    contact = os.environ.get("CONTACT_EMAIL", "stepanic.matija@gmail.com")
    return httpx.Client(headers={
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": f"udruge-domovina-ai/0.1 (open catalog; {contact})",
    }, timeout=30.0, follow_redirects=True)


def _req(s: httpx.Client, method: str, url: str, **kw):
    for attempt in range(4):
        try:
            r = s.request(method, url, **kw)
            if r.status_code == 200:
                return r
            log.warning("HTTP %s %s (pokušaj %d)", r.status_code, url, attempt + 1)
        except httpx.HTTPError as e:
            log.warning("%s (pokušaj %d)", e, attempt + 1)
        time.sleep(0.6 * (attempt + 1))
    return None


def search_oib(s: httpx.Client, oib: str, refresh: bool) -> list[dict]:
    cache = CACHE / f"{oib}.search.json"
    if cache.exists() and not refresh:
        return json.loads(cache.read_text()).get("data", [])
    r = _req(s, "POST", BASE + "Index",
             params={"Organizacija.OsobniIdentifikacijskiBrojOrganizacije": oib},
             content=SEARCH_BODY, headers={"Content-Type": "application/json; charset=utf-8"})
    if r is None:
        return []
    try:
        j = r.json()
    except ValueError:
        return []
    cache.write_text(json.dumps(j, ensure_ascii=False))
    time.sleep(0.15)
    return j.get("data", [])


def fetch_detail(s: httpx.Client, idorg: int, refresh: bool) -> dict:
    cache = CACHE / f"{idorg}.detail.html"
    if cache.exists() and not refresh:
        text = cache.read_text(encoding="utf-8")
    else:
        r = _req(s, "GET", BASE + "Details", params={"handler": "Details", "id": idorg})
        if r is None:
            return {}
        text = r.text
        cache.write_text(text, encoding="utf-8")
        time.sleep(0.15)
    return parse_detail(text)


def parse_detail(page: str) -> dict:
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", page, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    t = re.sub(r"\s+", " ", t).strip()
    parts = re.split(r"(?<!\d)(\d{2})\.\s", t)
    bodies: dict[str, str] = {}
    for i in range(1, len(parts) - 1, 2):
        bodies[parts[i]] = parts[i + 1].strip()
    out: dict[str, str] = {}
    for num, (key, label) in FIELD_LABELS.items():
        body = bodies.get(num, "")
        if not body:
            continue
        if body.startswith(label):
            body = body[len(label):].strip()
        m = SECTION_CUT.search(body)
        if m:
            body = body[: m.start()].strip()
        if body:
            out[key] = body
    return out


def run(limit: int | None, refresh: bool, workers: int) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT id, name, oib, phone, email, website, iban, president, rno_id "
            "FROM udruge WHERE oib IS NOT NULL AND oib != ''")]
        if not refresh:
            rows = [r for r in rows if not r["rno_id"]]
        if limit:
            rows = rows[:limit]
        log.info("za obraditi: %d (refresh=%s)", len(rows), refresh)
        s = session()

        def work(u: dict) -> tuple[dict, dict]:
            data = search_oib(s, u["oib"], refresh)
            if len(data) != 1:
                return u, {"_n": len(data)}
            top = data[0]
            det = fetch_detail(s, top["idOrganizacije"], refresh)
            det["_id"] = top["idOrganizacije"]
            return u, det

        results = []
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(work, u) for u in rows]
            for i, f in enumerate(as_completed(futs), 1):
                results.append(f.result())
                if i % 50 == 0:
                    log.info("  dohvaćeno %d/%d", i, len(rows))

        stat = {k: 0 for k in ("matched", "no_match", "ambiguous", "phone", "email", "website", "iban", "president")}
        for u, det in results:
            if det.get("_id") is None:
                stat["ambiguous" if det.get("_n", 0) > 1 else "no_match"] += 1
                continue
            stat["matched"] += 1
            sets, vals = ["rno_id=?", "rno_url=?"], [str(det["_id"]), f"{BASE}Details?handler=Details&id={det['_id']}"]
            if det.get("telefon") and not (u["phone"] or "").strip():
                ph = re.split(r"[,;]", det["telefon"])[0].strip()
                if ph:
                    sets += ["phone=?", "phone_kind=?", "phone_e164=?"]
                    vals += [ph, classify(ph), to_e164(ph)]
                    stat["phone"] += 1
            if det.get("email") and not (u["email"] or "").strip():
                em = clean_email(det["email"])
                if em:
                    sets.append("email=?"); vals.append(em); stat["email"] += 1
            if det.get("web") and not (u["website"] or "").strip():
                w = clean_website(det["web"])
                if w:
                    sets.append("website=?"); vals.append(w); stat["website"] += 1
            if det.get("iban") and not (u["iban"] or "").strip():
                iban = re.sub(r"\s", "", det["iban"]).upper()
                if re.match(r"^HR\d{19}$", iban):
                    sets.append("iban=?"); vals.append(iban); stat["iban"] += 1
            if det.get("zastupnik") and not (u["president"] or "").strip():
                pres = person_name(*det["zastupnik"].split(" ", 1)) if " " in det["zastupnik"] else None
                if pres and 3 <= len(pres) <= 60:
                    sets += ["president=?", "president_role=?"]
                    vals += [pres, "Osoba ovlaštena za zastupanje"]
                    stat["president"] += 1
            vals.append(u["id"])
            conn.execute(f"UPDATE udruge SET {', '.join(sets)}, updated_at=CURRENT_TIMESTAMP WHERE id=?", vals)
        conn.commit()
    log.info("RNO: %s", stat)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    run(a.limit, a.refresh, a.workers)
