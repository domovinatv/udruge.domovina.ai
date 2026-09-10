# Kako je nastao katalog katoličkih udruga (2026-09-10)

Zapis odluka i mjerenja iz prvog dana. Za orijentaciju u kodu vidi
`CLAUDE.md`; ovdje je *zašto*.

## Polazište

Pitanje je bilo jednostavno: „popis svih katoličkih udruga u Hrvatskoj".
Prije nego što je išta napisano, provjereno je gdje takav popis već postoji.
Ne postoji. Tri stvari postoje:

1. **Registar udruga RH** (Ministarstvo pravosuđa, uprave i digitalne
   transformacije) — 70 828 udruga, otvoreni podaci, osvježava se dnevno.
   Nema polja „vjera".
2. **Evidencija pravnih osoba Katoličke Crkve** — 2117 zapisa; 1563 župe,
   samostani, biskupije… i **22 laička udruženja** koja su registrirana kao
   crkvene pravne osobe (Fokolari, Omnia Deo, RINO, bratstva FSR-a). Ta
   udruženja **nisu** u Registru udruga (0 zajedničkih OIB-a).
3. `../klubovi.domovina.ai` je već imao pipeline nad Registrom udruga
   (spajanje nogometnih klubova na registar, RNO scraper). Odatle su
   preuzeti obrasci; klasifikator je nov.

## Mjerenje prije rješavanja: što u registru izdvaja katoličku udrugu?

Prva pretpostavka: područje djelovanja „3. DUHOVNOST". Izmjereno:

| signal | pogodaka | što je unutra |
|---|---:|---|
| područje „3. DUHOVNOST" | 1858 | pola joga, reiki, transpersonalna psihologija, „osobni razvoj" (3.2.2 je najbrojnija šifra) |
| ključna riječ u nazivu (sv., sveti, crkva, molitva…) | 4217 | sportski klubovi po svecima, ulice, mjesta (Sveti Ivan Zelina) |
| presjek | 411 | |

Ni jedno ni drugo nije filtar. Odluka: **bodovanje** s težinama, s
isključenjima za druge vjere i ezoteriju, i s pouzdanošću u tri razine —
od kojih najniža ne ide u katalog nego u red za pregled.

## Iteracije klasifikatora (tri kruga, svaki s uzorkom od 25 po tieru)

**Krug 1** (naivni regexi): 1649 u katalogu. Uzorak je pokazao:
- `žup` hvata *županiju* → svaki županijski sportski savez „župna udruga";
- šifra `14.` hvata novu nomenklaturu „14. ZAŠTITA ZDRAVLJA", ne samo staru
  „14. DUHOVNA" → svaki Crveni križ „srednja";
- `križ` = Crveni križ;
- `evanđe` hvata *evanđeoski* (protestanti) i *evanđelje* (svi).

**Krug 2**: 1381 u katalogu. Uzorak:
- `skaut|izviđač` kao jak pojam → svaki odred izviđača „visoka" → izbačeno;
- `biskup\w*` → selo Biskupija kod Knina i Biškupci → eksplicitni nastavci;
- „Župa dubrovačka" je općina → `_PLACE_NEUTRAL`;
- „Iglesia ni Cristo", „Međunarodna Kristova crkva", „Ellel" — u tieru
  „visoka" → isključenja.

**Krug 3**: 1122 u katalogu (783 aktivnih), tier „srednja" na uzorku čist
uz 2–3 neodlučiva („Bogumilski centar" → isključen).

Nakon toga: „katolički" u nazivu je definicija, ne indicija → visoka bez
obzira na zbroj; „bratovština" je jak pojam (u Hrvatskoj gotovo isključivo
katolička); druga vjera u *opisu* oduzima najviše 2 (dijalog s islamom je i
katolička djelatnost).

## Što je namjerno NAŠE, a ne iz registra

Sve što je prosudba nosi vlastite kolone i izvozi se s oznakom:
`catholic_score/confidence/signals`, `category`, `geo_source`,
`diocese_source`. Biskupija posebno: **granice biskupija ne postoje kao
javan podatak**; koristimo one koje `../crkve.domovina.ai` derivira iz
sjedišta župa (slaganje s 3 OSM relacije 96,6–98,6 %).

## Što je odbačeno

- **Registar udruga kao jedini izvor** — propušta 22 crkveno registrirana
  laička udruženja.
- **Google Places / Nominatim za koordinate** — DGU WFS radi besplatno i
  bolje za hrvatske adrese (vidi memoriju sestrinskih repoa).
- **Firecrawl za kontakte** — RNO (banovac.mfin.hr) daje telefon i e-mail
  po OIB-u bez scrapinga weba; na probnih 15: 12 pogodaka, 12 telefona,
  7 e-mailova.
