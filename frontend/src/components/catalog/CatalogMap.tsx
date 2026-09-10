import { useEffect, useMemo, useRef, useState } from "react";
import type { Map as MlMap, GeoJSONSource, MapLayerMouseEvent } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

import type { Category, UdrugaIndexItem } from "@/lib/catalog";
import { CATEGORY_LABEL, CATEGORY_ORDER, num } from "@/lib/format";
import { loadMapLibre } from "@/lib/maplibre";

/**
 * Karta cijelog kataloga. MapLibre GL, isti basemap kao gis.domovina.ai
 * (openfreemap positron) — bez ključa. KLIJENTSKA komponenta: MapLibre traži
 * `window`, a indeks ne smije u SSR payload.
 */

const STYLE_LIGHT = "https://tiles.openfreemap.org/styles/positron";
const HR_BOUNDS: [number, number, number, number] = [13.2, 42.3, 19.5, 46.6];

/** Boje žive u styles.css (`--map-<kategorija>`); ovdje se samo čitaju. */
function cssColor(name: string): string {
  if (typeof window === "undefined") return "#666666";
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || "#666666";
}

function escapeHtml(s: string): string {
  return s.replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c] ?? c,
  );
}

type PointFC = {
  type: "FeatureCollection";
  features: {
    type: "Feature";
    geometry: { type: "Point"; coordinates: [number, number] };
    properties: Record<string, string | boolean>;
  }[];
};

function toFeatureCollection(items: UdrugaIndexItem[]): PointFC {
  return {
    type: "FeatureCollection",
    features: items
      .filter((u) => u.lat !== undefined && u.lng !== undefined)
      .map((u) => ({
        type: "Feature",
        geometry: { type: "Point", coordinates: [u.lng as number, u.lat as number] },
        properties: {
          slug: u.slug,
          name: u.name,
          category: u.category,
          city: u.city ?? "",
          // MapLibreov `case` traži BOOLEAN — broj 0/1 obori cijeli sloj bez greške.
          active: u.active === 1,
          contact: u.contact === 1,
        },
      })),
  };
}

export function CatalogMap({ className = "h-[70vh] min-h-[420px]" }: { className?: string }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MlMap | null>(null);
  const [items, setItems] = useState<UdrugaIndexItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [hidden, setHidden] = useState<Set<Category>>(() => new Set());
  const [showInactive, setShowInactive] = useState(false);

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

  const counts = useMemo(() => {
    const m = new Map<Category, number>();
    for (const u of items ?? []) {
      if (!showInactive && u.active !== 1) continue;
      m.set(u.category, (m.get(u.category) ?? 0) + 1);
    }
    return m;
  }, [items, showInactive]);

  const visible = useMemo(
    () =>
      (items ?? []).filter(
        (u) => !hidden.has(u.category) && (showInactive || u.active === 1) && u.lat !== undefined,
      ),
    [items, hidden, showInactive],
  );

  useEffect(() => {
    if (!items || !containerRef.current || mapRef.current) return;
    let cancelled = false;

    void (async () => {
      const maplibregl = await loadMapLibre();
      if (cancelled || !containerRef.current) return;

      const map = new maplibregl.Map({
        container: containerRef.current,
        style: STYLE_LIGHT,
        bounds: HR_BOUNDS,
        fitBoundsOptions: { padding: 24 },
        attributionControl: { compact: true },
        dragRotate: false,
        pitchWithRotate: false,
        touchPitch: false,
      });
      mapRef.current = map;
      (window as unknown as { __udrugeMap?: MlMap }).__udrugeMap = map;
      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
      map.addControl(new maplibregl.ScaleControl({ maxWidth: 120, unit: "metric" }));

      const colorExpr: unknown[] = ["match", ["get", "category"]];
      for (const c of CATEGORY_ORDER) colorExpr.push(c, cssColor(`--map-${c}`));
      colorExpr.push(cssColor("--map-ostalo"));

      map.on("load", () => {
        map.addSource("udruge", {
          type: "geojson",
          data: toFeatureCollection(
            items.filter((u) => !hidden.has(u.category) && (showInactive || u.active === 1)),
          ),
          cluster: true,
          clusterRadius: 46,
          clusterMaxZoom: 11,
        });
        map.addLayer({
          id: "udruge-clusters",
          type: "circle",
          source: "udruge",
          filter: ["has", "point_count"],
          paint: {
            "circle-color": cssColor("--map-cluster"),
            "circle-opacity": 0.85,
            "circle-radius": ["step", ["get", "point_count"], 14, 25, 19, 100, 25, 300, 32],
            "circle-stroke-width": 2,
            "circle-stroke-color": "#ffffff",
          },
        });
        map.addLayer({
          id: "udruge-cluster-count",
          type: "symbol",
          source: "udruge",
          filter: ["has", "point_count"],
          layout: {
            "text-field": ["get", "point_count_abbreviated"],
            "text-font": ["Noto Sans Regular"],
            "text-size": 12,
          },
          paint: { "text-color": "#ffffff" },
        });
        map.addLayer({
          id: "udruge-tocke",
          type: "circle",
          source: "udruge",
          filter: ["!", ["has", "point_count"]],
          paint: {
            "circle-color": colorExpr as never,
            "circle-opacity": ["case", ["get", "active"], 0.95, 0.45],
            "circle-radius": ["interpolate", ["linear"], ["zoom"], 6, 4, 12, 7, 16, 11],
            "circle-stroke-width": ["case", ["get", "contact"], 2, 1],
            "circle-stroke-color": "#ffffff",
          },
        });

        map.on("click", "udruge-clusters", (e: MapLayerMouseEvent) => {
          const f = e.features?.[0];
          if (!f) return;
          const src = map.getSource("udruge") as GeoJSONSource;
          void src.getClusterExpansionZoom(f.properties["cluster_id"] as number).then((zoom) =>
            map.easeTo({
              center: (f.geometry as { coordinates: [number, number] }).coordinates,
              zoom,
            }),
          );
        });
        map.on("click", "udruge-tocke", (e: MapLayerMouseEvent) => {
          const f = e.features?.[0];
          if (!f) return;
          const p = f.properties as Record<string, string | boolean | undefined>;
          const cat = (p["category"] as Category | undefined) ?? "ostalo";
          const meta = [CATEGORY_LABEL[cat] ?? cat, p["city"] as string | undefined]
            .filter(Boolean)
            .join(" · ");
          new maplibregl.Popup({ offset: 12, maxWidth: "260px" })
            .setLngLat((f.geometry as { coordinates: [number, number] }).coordinates)
            .setHTML(
              `<div style="font-size:0.875rem">` +
                `<a href="/udruga/${encodeURIComponent(String(p["slug"] ?? ""))}" style="font-weight:600;text-decoration:underline">${escapeHtml(String(p["name"] ?? ""))}</a>` +
                `<p style="margin-top:0.25rem;font-size:0.75rem;opacity:0.7">${escapeHtml(meta)}</p>` +
                `</div>`,
            )
            .addTo(map);
        });
        for (const layer of ["udruge-clusters", "udruge-tocke"]) {
          map.on("mouseenter", layer, () => (map.getCanvas().style.cursor = "pointer"));
          map.on("mouseleave", layer, () => (map.getCanvas().style.cursor = ""));
        }
      });
    })();

    return () => {
      cancelled = true;
      mapRef.current?.remove();
      mapRef.current = null;
    };
    // `hidden`/`showInactive` se ne prate: filtar mijenja podatke izvora, ne kartu.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items]);

  // Filtar mijenja PODATKE IZVORA (klasteri se grade iz izvora), ne setFilter.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !items) return;
    const src = map.getSource("udruge") as GeoJSONSource | undefined;
    if (src) src.setData(toFeatureCollection(visible) as never);
  }, [visible, items]);

  function toggle(c: Category) {
    setHidden((prev) => {
      const next = new Set(prev);
      if (next.has(c)) next.delete(c);
      else next.add(c);
      return next;
    });
  }

  return (
    <div className="space-y-3">
      <div
        ref={containerRef}
        className={`w-full overflow-hidden rounded-2xl border border-border bg-muted ${className}`}
        role="application"
        aria-label="Karta katoličkih udruga u Hrvatskoj"
      >
        {!items && (
          <div className="grid h-full place-items-center px-6 text-center text-sm text-muted-foreground">
            {error
              ? `Karta se nije učitala (${error}). Podaci su i dalje dostupni u popisu.`
              : "Učitavam katalog…"}
          </div>
        )}
      </div>

      {items && (
        <>
          <div className="flex flex-wrap gap-2">
            {CATEGORY_ORDER.filter((c) => counts.get(c)).map((c) => {
              const off = hidden.has(c);
              return (
                <button
                  key={c}
                  type="button"
                  onClick={() => toggle(c)}
                  aria-pressed={!off}
                  className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold transition-colors ${
                    off
                      ? "border-border text-muted-foreground opacity-60"
                      : "border-border bg-secondary text-secondary-foreground"
                  }`}
                >
                  <span
                    aria-hidden="true"
                    className="size-2.5 rounded-full"
                    style={{ background: `var(--map-${c})` }}
                  />
                  {CATEGORY_LABEL[c]}
                  <span className="tabular-nums opacity-70">{num(counts.get(c) ?? 0)}</span>
                </button>
              );
            })}
            <label className="inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-1 text-xs font-semibold">
              <input
                type="checkbox"
                checked={showInactive}
                onChange={(e) => setShowInactive(e.target.checked)}
                className="size-3.5"
              />
              i ugašene
            </label>
          </div>
          <p className="text-xs text-muted-foreground">
            Prikazano {num(visible.length)} udruga. Deblji obrub označava udrugu s kontaktom
            (e-mail, telefon ili web); blijeda točka je ugašena udruga. Točka je sjedište iz
            registra — kod dijela udruga na razini naselja, ne kućnog broja.
          </p>
        </>
      )}
    </div>
  );
}
