import { createFileRoute } from "@tanstack/react-router";

import { loadIndex } from "@/lib/data";

/** Sitemap se GENERIRA iz indeksa. Ručne su samo statične rute — ako dodaješ rutu, dodaj je ovdje. */
const STATIC_PATHS = ["/", "/karta", "/udruge", "/brojke", "/o-projektu"];

function xmlEscape(s: string) {
  return s.replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;" })[c] ?? c,
  );
}

export const Route = createFileRoute("/sitemap.xml")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const origin = new URL(request.url).origin;
        // Isti loader kao rute — dijeli ispravak s ASSETS bindingom.
        const index = await loadIndex();
        const urls = [
          ...STATIC_PATHS.map((p) => ({ loc: `${origin}${p}`, priority: "0.9" })),
          ...index.items.map((u) => ({
            loc: `${origin}/udruga/${encodeURIComponent(u.slug)}`,
            priority: u.active ? "0.7" : "0.4",
          })),
        ];
        const body = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.map((u) => `  <url><loc>${xmlEscape(u.loc)}</loc><priority>${u.priority}</priority></url>`).join("\n")}
</urlset>`;
        return new Response(body, {
          headers: {
            "Content-Type": "application/xml; charset=utf-8",
            "Cache-Control": "public, max-age=3600",
          },
        });
      },
    },
  },
});
