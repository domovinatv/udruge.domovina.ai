# frontend — udruge.domovina.ai

Web kataloga katoličkih udruga u Hrvatskoj. TanStack Start + Nitro →
Cloudflare Worker, shadcn/ui + Tailwind v4.

Podaci nisu u ovom folderu: generira ih Python pipeline iz korijena repoa u
`public/data/` (gitignorano).

```sh
cd .. && make all            # baza, exporti, export-web
cd frontend && bun install && bun run dev
```

| URL             | Što                                                            |
| --------------- | -------------------------------------------------------------- |
| `/`             | naslovnica s brojkama                                          |
| `/karta`        | MapLibre karta sjedišta, filtri po kategoriji                  |
| `/udruge`       | pretraga i popis (kategorija, županija, aktivne)               |
| `/udruga/$slug` | detalj udruge: registar, kontakt, osobe, signali klasifikatora |
| `/brojke`       | pokrivenost iz stats.json                                      |
| `/o-projektu`   | izvori, postupak, licenca                                      |

Deploy: `./scripts/deploy.sh`. Konvencije i zamke: `CLAUDE.md`.
