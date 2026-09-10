import { createIsomorphicFn } from "@tanstack/react-start";
import { getRequest } from "@tanstack/react-start/server";
import { notFound } from "@tanstack/react-router";

import type { IndexFile, Manifest, Stats, Udruga, UdrugaIndexItem } from "./catalog";

/**
 * Podaci su statičke datoteke u `public/data/` (scripts/34_export_static.py).
 *
 * ZAMKA (naslijeđena iz crkve.domovina.ai, koštala jedan deploy): na
 * Cloudflareu `fetch` na vlastiti origin NE dolazi do assetâ nego se vrati u
 * sam Worker → 404 za svaku stranicu s loaderom, dok one bez loadera rade.
 * Ispravan put je `env.ASSETS.fetch()`; Nitro ga zakači na
 * `request.runtime.cloudflare`. Bez bindinga (vite dev) pada se na fetch.
 */
type CloudflareRequest = Request & {
  runtime?: { cloudflare?: { env?: { ASSETS?: { fetch: (req: Request) => Promise<Response> } } } };
};

const fetchData = createIsomorphicFn()
  .client((path: string) => fetch(path))
  .server((path: string) => {
    const req = getRequest() as CloudflareRequest;
    const url = new URL(path, req.url);
    const assets = req.runtime?.cloudflare?.env?.ASSETS;
    return assets ? assets.fetch(new Request(url)) : fetch(url);
  });

async function loadJson<T>(path: string): Promise<T> {
  const res = await fetchData(path);
  if (res.status === 404) throw notFound();
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return (await res.json()) as T;
}

export const loadManifest = () => loadJson<Manifest>("/data/manifest.json");
export const loadStats = () => loadJson<Stats>("/data/stats.json");
export const loadIndex = () => loadJson<IndexFile<UdrugaIndexItem>>("/data/udruge-index.json");
export const loadUdruga = (slug: string) =>
  loadJson<Udruga>(`/data/udruga/${encodeURIComponent(slug)}.json`);
