"""Klijent za data.gov.hr (CKAN) — državni registri, bez API ključa.

Četiri dataseta nose cijeli katalog:

  REGISTAR_UDRUGA_CTS     Registar udruga RH — glavna tablica (~71 000 zapisa;
                          ~44 000 AKTIVAN). Polja: OIB, NAZIV, SKRACENI_NAZIV,
                          STATUS, UDR_ID, SJEDISTE, ZUPANIJA, CILJEVI,
                          OPIS_DJELATNOSTI, CILJANE_SKUPINE, MAIL, WEB_STRANICA,
                          DATUM_UPISA, DATUM_OSNIVACKE_SKUPSTINE, REGISTARSKI_BROJ.
  REGISTAR_UDRUGA_OSOBE   Osobe ovlaštene za zastupanje (IME, PREZIME, FUNKCIJA,
                          SVOJSTVO) po UDR_ID — javno po Zakonu o udrugama.
  REGISTAR_UDRUGA_DJEL    Djelatnosti po UDR_ID: šifra + naziv + područje
                          (npr. "3.1.1. Promicanje religijske etike").
  STRANE_UDRUGE_*         Registar stranih udruga (~1 000; Pax Christi,
                          Kolping…), ista tri oblika.
  KATOLICKE_PRAVNE_OSOBE  Evidencija pravnih osoba Katoličke Crkve — odavde
                          uzimamo samo vjernička društva, pokrete i zajednice
                          (ne župe, ne samostane; to je ../crkve.domovina.ai).

Sve to Ministarstvo pravosuđa, uprave i digitalne transformacije osvježava
DNEVNO (metadata_modified na CKAN-u pomiče se svaki dan), pa `make clean-cache`
pa `make all` daje jučerašnje stanje registra.

Resource UUID-i su hardkodirani jer CKAN `package_show` zna promijeniti
redoslijed resursa; `resolve()` ih po potrebi ponovno otkrije po datasetu i
nazivu, pa link ne trune ako Ministarstvo re-uploada.

Odgovori se kešraju pod data/raw/datagovhr/. CTS JSON ima 131 MB.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "data" / "raw" / "datagovhr"
CKAN = "https://data.gov.hr/ckan/api/3/action"
DOWNLOAD = "https://data.gov.hr/ckan/dataset/{pkg}/resource/{res}/download/data.json"


def _user_agent() -> str:
    contact = os.environ.get("CONTACT_EMAIL", "stepanic.matija@gmail.com")
    return f"udruge-domovina-ai/0.1 (open catalog of catholic associations; {contact})"


HEADERS = {"User-Agent": _user_agent(), "Accept": "application/json"}


class Dataset:
    """(dataset-name, package-uuid, resource-uuid) za jedan JSON resurs."""

    def __init__(self, key: str, name: str, pkg: str, res: str, label: str,
                 match: str | None = None):
        self.key = key
        self.name = name      # CKAN `name` slug — koristi se za re-resolve
        self.pkg = pkg
        self.res = res
        self.label = label
        self.match = match    # podniz naziva resursa za re-resolve ("CTS")

    @property
    def url(self) -> str:
        return DOWNLOAD.format(pkg=self.pkg, res=self.res)


_RU = ("registar-udruga", "b04f3da4-d2b6-4789-9e5f-dc4cc18ae6fe")
_SU = ("registar-stranih-udruga-u-republici-hrvatskoj", "31b17b2f-1f78-41a5-9d3c-6314821be954")

REGISTAR_UDRUGA_CTS = Dataset(
    "registar-udruga-cts", *_RU, "030a7bf0-2d07-422d-851b-4f2df2ddc45d",
    "Registar udruga RH — CTS", match="CTS")
REGISTAR_UDRUGA_OSOBE = Dataset(
    "registar-udruga-osobe", *_RU, "58498c44-ddfd-4acd-b4d9-02739d8c9275",
    "Registar udruga RH — Osobe", match="Osobe")
REGISTAR_UDRUGA_DJEL = Dataset(
    "registar-udruga-djelatnosti", *_RU, "6f33ddad-4ed8-450c-8768-d37e8e1d05eb",
    "Registar udruga RH — Djelatnosti", match="Djelatnosti")

STRANE_UDRUGE_CTS = Dataset(
    "strane-udruge-cts", *_SU, "68ca80db-f9af-4f92-a22d-979a0cdab371",
    "Registar stranih udruga — CTS", match="CTS")
STRANE_UDRUGE_OSOBE = Dataset(
    "strane-udruge-osobe", *_SU, "6043891d-3fcd-4c7b-98b6-3e5357b157b2",
    "Registar stranih udruga — Osobe", match="Osobe")
STRANE_UDRUGE_DJEL = Dataset(
    "strane-udruge-djelatnosti", *_SU, "e2168b59-a8ac-408a-9762-cd293b4eabbd",
    "Registar stranih udruga — Djelatnosti", match="Djelatnosti")

KATOLICKE_PRAVNE_OSOBE = Dataset(
    "katolicke-pravne-osobe",
    "evidencija-pravnih-osoba-katolicke-crkve-u-republici-hrvatskoj",
    "6d975f94-bcf2-484f-a3d6-25d953807efa",
    "de8fc36b-44e9-400d-9330-58f478c4fb4f",
    "Evidencija pravnih osoba Katoličke Crkve u RH",
)


def _cache_path(ds: Dataset) -> Path:
    h = hashlib.sha256(ds.url.encode()).hexdigest()[:12]
    return CACHE_DIR / f"{ds.key}-{h}.json"


def resolve(ds: Dataset) -> list[str]:
    """Vrati JSON download URL-ove dataseta (fallback ako hardkodirani padne)."""
    try:
        r = httpx.get(f"{CKAN}/package_show", params={"id": ds.name},
                      headers=HEADERS, timeout=30, follow_redirects=True)
        r.raise_for_status()
        res = r.json()["result"]["resources"]
    except (httpx.HTTPError, KeyError, json.JSONDecodeError) as e:
        logger.warning("CKAN package_show(%s) pao: %s", ds.name, e)
        return []
    out = []
    for x in res:
        if (x.get("format") or "").upper() != "JSON":
            continue
        if ds.match and ds.match.lower() not in (x.get("name") or "").lower():
            continue
        out.append(x["url"])
    return out


def _probe_fails(ds: Dataset) -> bool:
    """HEAD na hardkodirani URL — ako ne prolazi, vrijedi platiti CKAN lookup."""
    try:
        r = httpx.head(ds.url, headers=HEADERS, timeout=20, follow_redirects=True)
        return r.status_code >= 400
    except httpx.HTTPError:
        return True


def fetch(ds: Dataset, force: bool = False) -> list[dict[str, Any]]:
    """Dohvati dataset kao listu dictova. Keširano; `force` zaobilazi keš.

    Prazan odgovor se NE kešira — prazan JSON s HTTP 200 je način na koji
    ovakvi portali javljaju kvar, i keširanjem bi drugi run tiho ostao bez
    podataka.
    """
    cache = _cache_path(ds)
    if cache.exists() and not force:
        return json.loads(cache.read_text())

    last_err: Exception | None = None
    tried: set[str] = set()
    for url in [ds.url, *(resolve(ds) if _probe_fails(ds) else [])]:
        if url in tried:
            continue
        tried.add(url)
        try:
            with httpx.stream("GET", url, headers=HEADERS, timeout=300,
                              follow_redirects=True) as r:
                r.raise_for_status()
                raw = b"".join(r.iter_bytes())
            data = json.loads(raw)
        except (httpx.HTTPError, json.JSONDecodeError) as e:
            last_err = e
            logger.warning("data.gov.hr %s pao (%s), pokušavam sljedeći URL", ds.key, e)
            continue
        if not isinstance(data, list):
            data = next((v for v in data.values() if isinstance(v, list)), [])
        if not data:
            continue
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(data, ensure_ascii=False))
        logger.info("%s: %d zapisa (keš zapisan)", ds.label, len(data))
        return data
    raise RuntimeError(f"data.gov.hr nedostupan za {ds.key}: {last_err}")


def split_sjediste(sjediste: str | None) -> tuple[str | None, str | None]:
    """'Dunavski prilaz 2, Vukovar' → ('Dunavski prilaz 2', 'Vukovar').

    Registar udruga piše sjedište kao "Ulica broj, Mjesto" — obrnuto od
    crkvene evidencije ("MJESTO, Ulica broj"). ZADNJI zarez je granica, jer
    ulica zna imati zarez ("Trg bana J. Jelačića, 1"), a mjesto rijetko.
    Zapis bez zareza je samo mjesto (sela s "bb").
    """
    if not sjediste:
        return None, None
    s = " ".join(sjediste.split())
    if "," not in s:
        # "Tisovac5i", "Stubalj45a", "Crkveni Bok60" — selo s kućnim brojem
        # zalijepljenim na ime, bez zareza. Broj ide u ulicu, ime je mjesto.
        import re

        m = re.match(r"^(.*?[A-Za-zČĆŠŽĐčćšžđ])\s*(\d+\s*[A-Za-z]?)$", s)
        if m and len(m.group(1)) >= 3:
            return f"{m.group(1)} {m.group(2)}".strip(), m.group(1).strip()
        return None, s or None
    street, _, city = s.rpartition(",")
    city = city.strip()
    street = street.strip()
    # "Stubička Slatina 65, Stubička Slatina" — selo bez ulice: ulica == mjesto + broj.
    return (street or None), (city or None)


def split_street(street: str | None) -> tuple[str | None, str | None]:
    """'Dunavski prilaz 2' → ('Dunavski prilaz', '2'); 'Prizna bb' → ('Prizna', None)."""
    if not street:
        return None, None
    import re

    m = re.match(r"^(.*?)[\s,]+(\d+[\s/]*[A-Za-z]?(?:/\d+)?)\.?\s*$", street.strip())
    if not m:
        s = re.sub(r"\b(bb|b\.b\.|bez broja)\s*$", "", street, flags=re.I).strip()
        return (s or None), None
    return m.group(1).strip() or None, m.group(2).replace(" ", "")
