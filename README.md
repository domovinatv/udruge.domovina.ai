# DOMOVINA Udruge — katoličke udruge u Hrvatskoj

**Code license:** [MIT](LICENSE) &nbsp;·&nbsp; **Data license:** [CC-BY 4.0](LICENSE-DATA)
&nbsp;·&nbsp; **Network:** part of [DOMOVINA](https://domovina.ai)

---

## English summary

Open catalog of **Catholic associations in Croatia**: lay associations
registered under the Associations Act, foreign associations with a Croatian
branch, and lay societies/movements registered as Church legal entities.
Every record carries its OIB (tax id), registry status, authorised
representative, geocoded seat (official DGU address points), diocese and —
where the Ministry of Finance registry has them — phone, e-mail and website.

There is no "religion" field in any Croatian registry. Catholic associations
are identified by a **scored classifier** over name, goals, activity
description and activity codes, with exclusions for other denominations and
esoteric groups; every record exports the signals that fired, so the
judgement is auditable. The pipeline is fully reproducible from public open
data without any API key.

---

## Hrvatski

Sustavna javna baza **katoličkih udruga u Hrvatskoj** — s OIB-om, statusom,
predsjednikom, koordinatama sjedišta, biskupijom i kontaktima gdje ih javni
registri imaju. Ni jedan hrvatski registar nema polje „vjera", pa je
katolička udruga **prosudba ovog projekta**, izvedena bodovanjem i objavljena
zajedno s razlozima (`signali`) — tako da se svaki zapis može provjeriti.

## Trenutno stanje (2026-09-10)

| Pokazatelj | Brojka |
|---|---:|
| Udruga u katalogu (pouzdanost visoka + srednja) | **864** |
| od toga aktivnih | **602** |
| od toga ugašenih / brisanih (povijest) | 262 |
| Kandidata za ručni pregled (pouzdanost niska) | 333 |
| S koordinatama sjedišta | 861 (99,7 %) |
| — na razini kućnog broja (DGU adresna točka) | 733 |
| — na razini naselja (težište) | 128 |
| S biskupijom | 861 |
| S OIB-om | 840 |
| Aktivnih s osobom ovlaštenom za zastupanje | 591 |
| Aktivnih s e-mailom / telefonom / webom (nakon `make rno`) | 462 / 485 / 126 |

| Registar | U katalogu | Aktivnih |
|---|---:|---:|
| Registar udruga RH | 835 | 581 |
| Evidencija pravnih osoba Katoličke Crkve (vjernička društva, pokreti) | 22 | 17 |
| Registar stranih udruga | 7 | 4 |

Kategorije (aktivne): molitvene zajednice 108, karitativne i humanitarne 87, bratovštine 82, zborovi i crkvena glazba 78, pokreti i laičke zajednice 52, mladi i studenti 36, hodočašća 31, kultura i baština 28, obitelj i život 22, župne udruge 20, sport i rekreacija 18, strukovne (liječnici, učitelji…) 15, obrazovanje i kateheza 11, mediji i nakladništvo 10, ostalo 4.

## Izvori podataka (svi javni, bez ključa)

| Izvor | Što daje | Napomena |
|---|---|---|
| **Registar udruga RH** (data.gov.hr, MPUDT) | naziv, OIB, status, sjedište, županija, ciljevi, opis djelatnosti, šifre djelatnosti, osobe ovlaštene za zastupanje, ponekad e-mail/web | 70 828 zapisa, osvježava se **dnevno** |
| **Registar stranih udruga** (data.gov.hr) | isto, za strane udruge s podružnicom u RH | ~220 zapisa |
| **Evidencija pravnih osoba Katoličke Crkve** (data.gov.hr) | vjernička društva, pokreti, bratstva FSR-a registrirani kao crkvene pravne osobe | isti dataset kao u [crkve.domovina.ai](https://github.com/domovinatv/crkve.domovina.ai); ovdje samo laička udruženja |
| **DGU INSPIRE WFS** (Registar prostornih jedinica) | koordinate kućnog broja sjedišta | 1,68 mil. adresnih točaka, bez ključa; fallback je težište naselja |
| **Granice** naselja/JLS/županija/biskupija | naselje, općina, županija i **biskupija** prostorno | iz [karta-hrvatske](https://github.com/domovinatv/karta-hrvatske); biskupije su **derivirane** u crkve.domovina.ai |
| **Registar neprofitnih organizacija** (banovac.mfin.hr) | telefon, e-mail, web, IBAN po OIB-u | `make rno`, zaseban korak |

## Kako se prepoznaje katolička udruga

Izmjereno na cijelom registru: područje djelovanja „3. DUHOVNOST" ima 1858
udruga, ali pola su joga, reiki i „osobni razvoj"; ključne riječi u nazivu
(„sv.", „sveti", „crkva") daju 4217 pogodaka, velikim dijelom sportske klubove
nazvane po svecima i mjesta. Ni jedno nije filtar.

Zato `src/katolicki.py` **boduje**: naziv punom težinom („katolički", „župni",
„franjevački", „bratovština", „hodočasnička", „molitvena", redovi i pokreti…),
opis pola težine, šifre djelatnosti 3.1.x (religijske) do 3 boda, a druge
vjere i ezoterija u nazivu isključuju. Pouzdanost:

- **visoka** — u katalogu; „katolički" u nazivu ili zbroj ≥ 6 s jakim pojmom u nazivu
- **srednja** — u katalogu; zbroj ≥ 4
- **niska** — NIJE u katalogu; `data/exports/udruge-za-pregled.csv`, red za ručni pregled

Svaki zapis ima kolonu `signali` (npr. `naziv:katolic, opis:hodocasce,
djelatnost:3.1.1.`). Mjerenja i iteracije: `docs/2026-09-10-izgradnja-kataloga.md`.

## Pokretanje

```bash
uv sync
make all        # init → ingest (3 registra) → geocode (DGU) → export → stats; ~10 min, bez ključeva
make rno        # kontakti iz RNO-a (MFIN), ~5 min, mrežno
make export stats
make test
```

Sirovi odgovori se kešraju u `data/raw/` (220 MB; gitignored). `make
clean-cache && make all` daje aktualno stanje registra.

## Izlazi (`data/exports/`)

| Datoteka | Sadržaj |
|---|---|
| `udruge.csv` | katalog (visoka + srednja), svi statusi, sve kolone, UTF-8 s BOM-om |
| `udruge.geojson` | isto, kao točke sjedišta — za kartu |
| `udruge-za-pregled.csv` | kandidati s pouzdanosti niska |
| `stats.json` | brojke iz tablice gore, po kategoriji/županiji/biskupiji |

Kolone koje su **naša prosudba**, a ne podatak iz registra: `pouzdanost`,
`bodovi`, `signali`, `kategorija`, `izvor_koordinata`, `biskupija` +
`izvor_biskupije`. Sve ostalo je preslikano iz registra.

## Repozitorij

```
src/
  datagovhr.py   CKAN klijent (data.gov.hr), keš, re-resolve resursa
  katolicki.py   KLASIFIKATOR + kategorije — najrizičniji dio, sve ima test
  ingest.py      zajednička logika 01/02 (osobe, datumi, e-mail/web čišćenje)
  db.py          SQLite shema (udruge, osobe) + idempotentni upsert
  dgu.py         DGU WFS geokoder (iz oou.domovina.ai)
  geo_hr.py      naselje/JLS/županija/biskupija point-in-polygon (iz crkve.domovina.ai)
  normalize.py   slug, dijakritika, title-case
  phones.py      HR telefoni → mobitel/fiksni + E.164
scripts/
  00_init_db.py                  shema
  01_ingest_registar_udruga.py   Registar udruga → klasifikacija → udruge + osobe
  02_ingest_strane_udruge.py     Registar stranih udruga
  03_ingest_evidencija_kc.py     vjernička društva iz crkvene evidencije
  10_geocode.py                  DGU adresa → težište naselja; naselje/županija/biskupija
  20_enrich_rno.py               RNO kontakti (fill-if-empty)
  30_build_fts.py  31_export_geojson.py  32_export_csv.py  40_stats.py
```

Sestrinski projekti istog obrasca: [klubovi.domovina.ai](https://github.com/domovinatv/klubovi.domovina.ai),
[crkve.domovina.ai](https://github.com/domovinatv/crkve.domovina.ai),
karta na [gis.domovina.ai](https://gis.domovina.ai).
