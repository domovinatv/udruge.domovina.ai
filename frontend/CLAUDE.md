# CLAUDE.md — frontend/ (udruge.domovina.ai)

Web kataloga katoličkih udruga. Kopija `../../crkve.domovina.ai/frontend`
(koji je nastao iz `stepanic/hr-site-starter`), svedena na jednu jedinicu
stranice — udrugu. Pipeline i model podataka: `../CLAUDE.md`. **Sve zamke iz
`../../crkve.domovina.ai/frontend/CLAUDE.md` vrijede i ovdje** (ASSETS
binding, MapLibre worker, `case` traži boolean, brojke iz stats.json).

## Stack

TanStack Start + Nitro (`preset: cloudflare-module`) → Cloudflare **Worker**
`udruge-domovina`. shadcn/ui + Tailwind v4, React 19, bun.

```sh
bun run dev          # vite dev, port 5173
bun run typecheck && bun run lint && bun run build
./scripts/deploy.sh  # export podataka → provjere → build → wrangler deploy → smoke
```

## Podaci su generirani, ne pisani

`public/data/` piše `../scripts/34_export_static.py` (`make export-web`,
POSLIJE `make stats`). Gitignoran je.

| Datoteka                           | Što                                                     |
| ---------------------------------- | ------------------------------------------------------- |
| `udruge-index.json`                | slim zapis po udruzi — karta, popis, pretraga (~280 KB) |
| `udruga/<slug>.json`               | detalj; samo pouzdanost visoka + srednja, svi statusi   |
| `stats.json`                       | mjera iz `scripts/40` — brojke se NE računaju ovdje     |
| `kategorije.json`, `manifest.json` | kategorije, `generated_at` i brojke                     |

Tipovi u `src/lib/catalog.ts` prate export. Loaderi u `src/lib/data.ts`.

## Rute

`/`, `/karta`, `/udruge?kategorija=&zupanija=`, `/udruga/$slug`, `/brojke`,
`/o-projektu`, `/sitemap.xml`. Ako dodaješ rutu, dodaj je u `STATIC_PATHS`
u sitemapu i u `nav` u `src/data/site.ts`.

## Tvrda pravila (uz naslijeđena)

- **Prosudba se ispisuje.** Svaka stranica udruge ima sekciju „Zašto je u
  katalogu" sa signalima klasifikatora (`signalLabel` u `format.ts`) i
  napomenu kad je pouzdanost srednja. Ne skrivaj to.
- **Ugašena udruga ostaje**, s `<Gap>` koji kaže status i datum. Nula/brisano
  je nalaz.
- Sloj preciznosti koordinate se ispisuje (`GEO_SOURCE_LABEL`); MiniMap ide
  na zoom 12 za težište naselja, 15 za adresu — inače bi točka usred sela
  izgledala kao kućni broj.
- Biskupija uvijek ide uz napomenu da je izvedena (osim iz crkvene evidencije).
- Boje karte: `--map-<kategorija>` u `styles.css`, hex (MapLibre parser).
  Kategorije su zatvoren skup iz `src/katolicki.py` — dodaš li kategoriju,
  dodaj boju, labelu (`CATEGORY_LABEL`) i redoslijed (`CATEGORY_ORDER`).
