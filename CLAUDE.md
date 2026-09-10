# CLAUDE.md — udruge.domovina.ai

Orijentacija za agente koji rade u ovom repozitoriju. Drži je aktualnom.

## Što je ovo
**Katalog katoličkih udruga u Hrvatskoj** — civilne udruge iz Registra
udruga RH, strane udruge s podružnicom u RH i vjernička društva/pokreti iz
Evidencije pravnih osoba Katoličke Crkve. S OIB-om, statusom, osobom
ovlaštenom za zastupanje, koordinatama sjedišta, biskupijom i (gdje ih ima)
kontaktima. Otvoreni podaci, reproducibilno iz javnih izvora, **bez ijednog
API ključa**.

Sestrinski repoi istog obrasca: `../klubovi.domovina.ai` (uzor za Registar
udruga i RNO), `../crkve.domovina.ai` (uzor za data.gov.hr klijent, normalize,
geo_hr, frontend). Kod se kopira i prilagođava, ne dijeli kroz paket.

## Repo layout
```
src/         datagovhr (CKAN), katolicki (KLASIFIKATOR), ingest (zajedničko
             za 01/02), db, normalize, dgu (geokoder), geo_hr (naselja/
             županije/biskupije), phones
scripts/     00 init → 01–03 ingest → 10 geocode → 20 rno → 30–32 export → 40 stats
tests/       pytest — klasifikator je najrizičniji dio, sve njegove ispravke
             imaju test s pravim nazivom iz registra
data/        udruge.db (gitignored), raw/ keš (220 MB, gitignored), exports/
docs/        zašto je što tako, s mjerenjima
```

## Model podataka — jedna tablica, tri registra
`udruge.registry` kaže odakle zapis dolazi:

| registry | što je | izvor | ~aktivnih |
|---|---|---|---|
| `registar-udruga` | civilna udruga (Zakon o udrugama) | data.gov.hr, MPUDT | ~780 |
| `strane-udruge` | strana udruga s podružnicom u RH | data.gov.hr, MPUDT | ~10 |
| `evidencija-kc` | vjerničko društvo / pokret / zajednica kao **crkvena** pravna osoba | data.gov.hr, MPUDT | ~20 |

Treći izvor postoji jer dio laičkih udruženja (Fokolari, Omnia Deo, RINO,
FSR bratstva) NIJE u Registru udruga — Crkva im je dala pravnu osobnost po
kanonskom pravu i država ih vodi u drugoj evidenciji. Bez toga bi katalog
propustio upravo one koje su "najkatoličkije".

**Nema OIB preklapanja** između Registra udruga i Evidencije KC (izmjereno:
0 od ~2100) — jedna pravna osoba je ili jedno ili drugo.

Tablica `osobe` drži osobe ovlaštene za zastupanje kako ih registar javno
objavljuje; zamjenjuju se pri svakom ingestu, ne spajaju.

## Klasifikator (`src/katolicki.py`) — pročitaj prije nego što ga "popraviš"
Registar udruga **nema polje vjera**. Katoličke se izdvajaju BODOVANJEM
naziva, ciljeva, opisa djelatnosti, ciljanih skupina i šifri djelatnosti.
Izmjereno na 70 828 zapisa (dump svibanj 2026):

- područje **"3. DUHOVNOST" ima 1858 udruga, a pola su joga/reiki/osobni
  razvoj** (šifra 3.2.2 najbrojnija) — samo po sebi ne znači ništa;
- **"sv./sveti" u nazivu daje 4217 pogodaka**, velik dio su sportski klubovi
  (MNK Sv. Jakov) i mjesta (Sveti Ivan Zelina);
- presjek to dvoje: 411.

Zato: naziv nosi punu težinu, opis pola (kapa 4), šifre 3.1.x do 3 boda a
3.2.x/3.3 zajedno najviše 1; druge vjere i ezoterija **u nazivu isključuju**,
u opisu oduzimaju (dijalog s islamom je i katolička djelatnost). Pragovi:
visoka ≥ 6 (ili „katolički" u nazivu), srednja ≥ 4, niska ≥ 2.5. **Niska
nije katalog nego red za pregled** (`udruge-za-pregled.csv`); u GeoJSON i
`udruge.csv` ide samo visoka + srednja.

Svaki zapis nosi `catholic_signals` — koje pravilo se okinulo. To je jedini
pošten način da se prosudba objavi kao otvoreni podatak.

Zamke koje su koštale mjerenja (svaka ima test):
- **„župa" ≠ „županija"** — regex mora zahtijevati kraj riječi iza
  `zup(a|e|i|u|n…)`, inače svaki županijski savez postaje župna udruga.
- **„Župa dubrovačka" je općina** (Judo klub Župa dubrovačka), „Sveti Ivan
  Zelina" je grad — `_PLACE_NEUTRAL` ih spaja u jednu riječ prije bodovanja.
- **„Biskupija" je i selo kod Knina**, Biškupci/Biškupec također — `biskup`
  bez `\w*`, s eksplicitnim nastavcima.
- **Šifra „14." postoji u dvije nomenklature**: stara „14. DUHOVNA", nova
  „14. ZAŠTITA ZDRAVLJA". Gledaj naziv područja, ne samo šifru. Bez toga je
  svaki Crveni križ bio „srednja".
- **„križ" je Crveni križ**, ne križni put — nije signal.
- **„evanđeoski" je protestantski**, „evanđelje" nije. „Kristova crkva",
  „Iglesia ni Cristo", „Ellel" — isključenja koja su ušla tek nakon što su
  se pojavila u tieru „visoka".
- **Skauti/izviđači nisu katolički** sami po sebi (Odred izviđača Borongaj);
  „katolički skauti" hvata `katolic`.

## Pipeline
`make all` = `init → ingest (01–03) → geocode (10) → export (30–32) → stats (40)`.
Sve idempotentno; sirovi odgovori u `data/raw/<izvor>/`. `make rno` (20) je
zaseban jer ide na banovac.mfin.hr (~2 zahtjeva po udruzi) — bez ključa, ali
pristojno; `make all-rno` uključuje ga.

- **01/02/03 BRIŠU zapise svog registra koje taj run nije potvrdio.** Bez
  toga bi svaka ispravka klasifikatora ostavljala „duhove" iz prošlih runova.
- **10 piše `geo_source`** uz svaku koordinatu: `dgu-adresa` (kućni broj iz
  RPJ-a), `dgu-ulica-fuzzy`, `naselje-teziste` (razina mjesta). Na karti
  izgledaju isto, a razlika je kilometri — potrošač mora znati.
- **Biskupija je DERIVIRANA** (`diocese_source = derivirano-crkve.domovina.ai`)
  iz granica koje `../crkve.domovina.ai` izračunava iz sjedišta župa; za
  zapise iz Evidencije KC dolazi iz same evidencije. Križevačka eparhija nije
  u particiji, pa grkokatoličke udruge dobiju latinsku biskupiju mjesta.
- **Registar se osvježava dnevno** (CKAN `metadata_modified` pomiče se svaki
  dan); `make clean-cache && make all` daje jučerašnje stanje.
- `data.gov.hr` JSON za CTS ima 131 MB; `fetch` streama i **ne kešira prazan
  odgovor** (prazan JSON s HTTP 200 je kako portal javlja kvar).

## Izvori (svi javni, bez ključa)
- **Registar udruga RH** (CTS + Osobe + Djelatnosti) i **Registar stranih
  udruga** — data.gov.hr, resource UUID-i u `src/datagovhr.py`, `resolve()`
  ih ponovno nađe ako Ministarstvo re-uploada. Registar udruga NEMA telefon,
  MAIL/WEB su rijetko popunjeni.
- **Evidencija pravnih osoba Katoličke Crkve** — isti dataset koji koristi
  crkve.domovina.ai; ovdje samo filtar `is_lay_association` (scripts/03).
- **DGU INSPIRE AD.Address WFS** — geokoder, vidi `src/dgu.py` docstring.
  Naselje mora biti točno RPJ ime; „Rovinj - Rovigno" → i „Rovinj".
- **Granice** naselja/JLS/županija/biskupija iz `../karta-hrvatske/apps/
  karta-web/public/data/` (`KARTA_DATA_DIR`). Bez njih pipeline radi, ali
  bez težišta naselja i bez biskupije.
- **RNO** (banovac.mfin.hr/rnoprt) — telefon, e-mail, web, IBAN po OIB-u.
  Obični ASP.NET, bez captche. Puni samo prazna polja.

## Otvoreno / sljedeći koraci
- Frontend (`frontend/`) po uzoru na `../crkve.domovina.ai/frontend`
  (TanStack Start → Cloudflare Worker) i sloj na gis.domovina.ai.
- Veza na župu (`../crkve.domovina.ai`): mnoge udruge su župne („zbor župe
  sv. Ante") — spajanje po titularu + mjestu bi dalo link na `/zupa/$slug`.
- Ručni pregled tiera „niska" (`data/exports/udruge-za-pregled.csv`).
- Registar udruga ima i `#!udruga-detalji/<token>` stranice, ali token je
  opaque (Vaadin) — link vodi na pretragu, ne na zapis.
