import { useEffect, useMemo, useState } from "react";
import { Link } from "@tanstack/react-router";
import { Search } from "lucide-react";

import type { Category, UdrugaIndexItem } from "@/lib/catalog";
import { CATEGORY_LABEL, CATEGORY_ORDER, broj, foldHr, num } from "@/lib/format";
import { Chip } from "@/components/catalog/Bits";

const PAGE = 60;

/**
 * Pretraga i popis udruga. KLIJENTSKI: indeks (~280 KB) se dohvaća ovdje, ne
 * u loaderu rute — TanStack serijalizira loader podatke u HTML pa bi ga
 * posjetitelj dobio dvaput.
 */
export function UdrugaBrowser({
  initialCategory,
  initialCounty,
}: {
  initialCategory?: Category | undefined;
  initialCounty?: string | undefined;
}) {
  const [items, setItems] = useState<UdrugaIndexItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [category, setCategory] = useState<string>(initialCategory ?? "");
  const [county, setCounty] = useState(initialCounty ?? "");
  const [onlyActive, setOnlyActive] = useState(true);
  const [limit, setLimit] = useState(PAGE);

  useEffect(() => {
    const ctrl = new AbortController();
    fetch("/data/udruge-index.json", { signal: ctrl.signal })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d: { items: UdrugaIndexItem[] }) => setItems(d.items))
      .catch((e: Error) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => ctrl.abort();
  }, []);

  const counties = useMemo(() => {
    const set = new Set<string>();
    for (const u of items ?? []) if (u.county) set.add(u.county);
    return [...set].sort((a, b) => a.localeCompare(b, "hr"));
  }, [items]);

  const results = useMemo(() => {
    if (!items) return [];
    const needle = foldHr(q.trim());
    return items.filter((u) => {
      if (onlyActive && u.active !== 1) return false;
      if (category && u.category !== category) return false;
      if (county && u.county !== county) return false;
      if (!needle) return true;
      return (
        foldHr(u.name).includes(needle) ||
        (u.city ? foldHr(u.city).includes(needle) : false) ||
        (u.diocese ? foldHr(u.diocese).includes(needle) : false)
      );
    });
  }, [items, q, category, county, onlyActive]);

  useEffect(() => setLimit(PAGE), [q, category, county, onlyActive]);

  if (error) {
    return (
      <p className="text-sm text-muted-foreground">
        Popis se nije učitao ({error}). Pokušajte osvježiti stranicu.
      </p>
    );
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-3 lg:grid-cols-[1fr_auto_auto]">
        <label className="relative">
          <span className="sr-only">Pretraga po nazivu, mjestu ili biskupiji</span>
          <Search
            className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden="true"
          />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Naziv, mjesto ili biskupija — npr. bratovština, Šolta"
            className="h-11 w-full rounded-full border border-input bg-card pl-9 pr-4 text-sm"
          />
        </label>
        <label>
          <span className="sr-only">Kategorija</span>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="h-11 w-full rounded-full border border-input bg-card px-4 text-sm lg:w-64"
          >
            <option value="">Sve kategorije</option>
            {CATEGORY_ORDER.map((c) => (
              <option key={c} value={c}>
                {CATEGORY_LABEL[c]}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span className="sr-only">Županija</span>
          <select
            value={county}
            onChange={(e) => setCounty(e.target.value)}
            className="h-11 w-full rounded-full border border-input bg-card px-4 text-sm lg:w-60"
          >
            <option value="">Sve županije</option>
            {counties.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
      </div>

      <label className="flex w-fit items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={onlyActive}
          onChange={(e) => setOnlyActive(e.target.checked)}
          className="size-4 rounded border-input"
        />
        Samo aktivne (bez brisanih i ugašenih)
      </label>

      <p className="text-sm text-muted-foreground" aria-live="polite">
        {items ? (
          <>
            {broj(results.length, "udruga", "udruge", "udruga")}
            {results.length !== items.length && <> od ukupno {num(items.length)} u katalogu</>}
          </>
        ) : (
          "Učitavam katalog…"
        )}
      </p>

      <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {results.slice(0, limit).map((u) => (
          <li key={u.slug}>
            <Link
              to="/udruga/$slug"
              params={{ slug: u.slug }}
              className="surface-card block h-full p-4 transition-shadow hover:shadow-[var(--shadow-lift)]"
            >
              <p className="font-semibold leading-snug">{u.name}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {[u.city, u.diocese].filter(Boolean).join(" · ")}
              </p>
              <div className="mt-2.5 flex flex-wrap gap-1.5">
                <Chip>{CATEGORY_LABEL[u.category] ?? u.category}</Chip>
                {u.active === 0 && <Chip tone="gap">Ugašena</Chip>}
                {u.confidence === "srednja" && (
                  <Chip title="Bodovanje je dalo srednju pouzdanost — provjerite signale na stranici">
                    srednja pouzdanost
                  </Chip>
                )}
                {u.contact === 1 && <Chip tone="verified">Kontakt</Chip>}
              </div>
            </Link>
          </li>
        ))}
      </ul>

      {results.length > limit && (
        <div className="flex justify-center">
          <button
            type="button"
            onClick={() => setLimit((l) => l + PAGE * 2)}
            className="rounded-full border border-border px-5 py-2.5 text-sm font-semibold"
          >
            Prikaži još ({num(results.length - limit)})
          </button>
        </div>
      )}

      {items && results.length === 0 && (
        <p className="text-sm text-muted-foreground">Nijedna udruga ne odgovara upitu.</p>
      )}
    </div>
  );
}
