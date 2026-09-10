"""Zajednički dijelovi ingesta iz Registra udruga i Registra stranih udruga.

Skripte 01 i 02 rade isto nad dva registra istog oblika (CTS + osobe +
djelatnosti), pa logika živi ovdje — i zato što se modul čije ime počinje
brojkom ne može importati u testove.
"""
from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from typing import Any

from src.katolicki import categorize, classify
from src.normalize import title_case_hr

log = logging.getLogger(__name__)

REGISTRY_URL = "https://registri-npo-mpu.gov.hr/#!udruge"

# Rang osobe za polje `president`: predsjednik prije "ovlaštene za zastupanje",
# a likvidator nikad — on je znak da udruga umire, ne tko je vodi.
_ROLE_RANK = [
    (re.compile(r"PREDSJEDNI"), 0),
    (re.compile(r"PREDSTOJNI|VODITELJ|UPRAVITELJ|GLAVNI TAJNIK|NADSTOJNI"), 1),
    (re.compile(r"ZAMJENI|DOPREDSJEDNI|POTPREDSJEDNI"), 3),
    (re.compile(r"TAJNI"), 4),
]


def iso_date(s: str | None) -> str | None:
    """'2015-02-23T00:00:00' ili '2/23/2015 12:00:00 AM' → '2015-02-23'."""
    if not s:
        return None
    s = str(s).strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        return f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return None


def person_name(ime: str | None, prezime: str | None) -> str | None:
    def cap(token: str) -> str:
        return "-".join(p[:1].upper() + p[1:].lower() for p in token.split("-"))
    parts = [cap(t) for t in (ime or "").split()] + [cap(t) for t in (prezime or "").split()]
    return " ".join(p for p in parts if p) or None


def pick_president(osobe: list[dict]) -> tuple[str | None, str | None]:
    """(ime i prezime, uloga) osobe koja udrugu vodi, ili (None, None)."""
    best: tuple[int, str, str] | None = None
    for o in osobe:
        funk = (o.get("funkcija") or "").upper()
        svoj = (o.get("svojstvo") or "").upper()
        if "LIKVIDATOR" in funk or "LIKVIDATOR" in svoj:
            continue
        name = person_name(o.get("ime"), o.get("prezime"))
        if not name:
            continue
        rank = 9
        for pat, r in _ROLE_RANK:
            if pat.search(svoj) or pat.search(funk):
                rank = r
                break
        role = svoj or funk or "OSOBA OVLAŠTENA ZA ZASTUPANJE"
        if best is None or rank < best[0]:
            best = (rank, name, title_case_hr(role))
    return (best[1], best[2]) if best else (None, None)


def index_osobe(rows: list[dict]) -> dict[Any, list[dict]]:
    out: dict[Any, list[dict]] = defaultdict(list)
    for r in rows:
        out[r.get("UDR_ID")].append({
            "ime": (r.get("IME") or "").strip() or None,
            "prezime": (r.get("PREZIME") or "").strip() or None,
            "funkcija": (r.get("FUNKCIJA") or "").strip() or None,
            "svojstvo": (r.get("SVOJSTVO") or "").strip() or None,
            "vrsta": (r.get("VRSTA_OSOBE") or "").strip() or None,
        })
    return out


def index_djelatnosti(rows: list[dict], code_key: str = "DJELATNOSTI") -> dict[Any, list[tuple[str, str]]]:
    out: dict[Any, list[tuple[str, str]]] = defaultdict(list)
    for r in rows:
        code = (r.get(code_key) or "").strip()
        area = (r.get("PODRUCJA_DJELOVANJA") or "").strip()
        if code:
            out[r.get("UDR_ID")].append((code, area))
    return out


def assess(name: str, goals: str | None, desc: str | None, target: str | None,
           activities: list[tuple[str, str]]) -> dict | None:
    """Klasificiraj; None ako nije katolička. Vraća polja za upsert."""
    res = classify(name, goals, desc, target, activities)
    if res.confidence is None:
        return None
    return {
        "catholic_score": res.score,
        "catholic_confidence": res.confidence,
        "catholic_signals": json.dumps(res.signals, ensure_ascii=False),
        "category": categorize(name, goals, desc),
        "activities": json.dumps([c for c, _ in activities], ensure_ascii=False) if activities else None,
        "areas": json.dumps(sorted({a for _, a in activities if a}), ensure_ascii=False) if activities else None,
    }


def clean_email(s: str | None) -> str | None:
    s = (s or "").strip().lower().strip(";, ")
    s = re.split(r"[;,\s]+", s)[0] if s else ""
    return s if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", s) else None


def clean_website(s: str | None) -> str | None:
    s = (s or "").strip().rstrip("/").strip()
    if not s or "." not in s or "@" in s:
        return None
    if not re.match(r"^https?://", s, re.I):
        s = "https://" + s
    return s
