import { createFileRoute, Link } from "@tanstack/react-router";

import { loadManifest, loadStats } from "@/lib/data";
import { breadcrumbLd, pageHead } from "@/lib/seo";
import { GEO_SOURCE_LABEL, REGISTRY_LABEL, num } from "@/lib/format";
import { Gap, PageHeading, Section, Stat } from "@/components/catalog/Bits";
import type { Registry } from "@/lib/catalog";

export const Route = createFileRoute("/brojke")({
  loader: async () => ({ stats: await loadStats(), manifest: await loadManifest() }),
  head: () => ({
    ...pageHead({
      title: "Brojke i pokrivenost kataloga katoličkih udruga",
      description:
        "Koliko udruga katalog ima, koliko ih je aktivnih, s koordinatama, kontaktom i biskupijom, po kategoriji, županiji i registru — i koliko kandidata čeka pregled.",
      path: "/brojke",
    }),
    scripts: [
      breadcrumbLd([
        { name: "Naslovnica", path: "/" },
        { name: "Brojke", path: "/brojke" },
      ]),
    ],
  }),
  component: Brojke,
});

function Bar({ label, value, max }: { label: string; value: number; max: number }) {
  return (
    <li className="grid grid-cols-[minmax(0,12rem)_1fr_auto] items-center gap-3 text-sm">
      <span className="truncate" title={label}>
        {label}
      </span>
      <span className="h-2 rounded-full bg-secondary">
        <span
          className="block h-2 rounded-full bg-primary"
          style={{ width: `${Math.max(2, (value / max) * 100)}%` }}
        />
      </span>
      <span className="tabular-nums text-muted-foreground">{num(value)}</span>
    </li>
  );
}

function Distribution({
  title,
  data,
  labelFn,
  limit,
}: {
  title: string;
  data: Record<string, number>;
  labelFn?: (key: string) => string;
  limit?: number;
}) {
  const rows = Object.entries(data)
    .filter(([k]) => k !== "?")
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit);
  const max = rows[0]?.[1] ?? 1;
  return (
    <div>
      <h3 className="text-base font-bold">{title}</h3>
      <ul className="mt-3 space-y-1.5">
        {rows.map(([k, v]) => (
          <Bar key={k} label={labelFn ? labelFn(k) : k} value={v} max={max} />
        ))}
      </ul>
    </div>
  );
}

function Brojke() {
  const { stats, manifest } = Route.useLoaderData();
  const cats: Record<string, number> = {};
  for (const [k, v] of Object.entries(stats.po_kategoriji_aktivne)) cats[v.label || k] = v.n;

  return (
    <Section>
      <PageHeading
        eyebrow="Pokrivenost"
        title="Brojke"
        lead={
          <>
            Sve je izmjereno nad bazom, ne procijenjeno. Podaci su generirani{" "}
            {new Date(manifest.generated_at).toLocaleDateString("hr-HR", { dateStyle: "long" })}.
          </>
        }
      />

      <h2 className="mt-10 text-lg">Katalog</h2>
      <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat
          value={stats.udruge_katalog}
          label="Udruga u katalogu"
          hint="Pouzdanost visoka + srednja, svi statusi."
        />
        <Stat value={stats.udruge_aktivne} label="Aktivnih" />
        <Stat
          value={stats.udruge_ugasene}
          label="Brisanih ili ugašenih"
          hint="Ostaju kao povijest; stranica kaže da su ugašene."
        />
        <Stat value={stats.s_oib} label="S OIB-om" />
        <Stat value={stats.s_koordinatama} label="S koordinatama sjedišta" />
        <Stat
          value={stats.s_biskupijom}
          label="S biskupijom"
          hint="Prostorno, iz deriviranih granica biskupija."
        />
        <Stat value={stats.s_predsjednikom} label="Aktivnih s osobom koja zastupa" />
        <Stat
          value={stats.osobe}
          label="Osoba ovlaštenih za zastupanje"
          hint="Kako ih objavljuje registar."
        />
      </div>

      <h2 className="mt-12 text-lg">Kontakt (aktivne)</h2>
      <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat value={stats.s_emailom} label="S e-mailom" tone="verified" />
        <Stat value={stats.s_telefonom} label="S telefonom" tone="verified" />
        <Stat value={stats.s_webom} label="S webom" tone="verified" />
        <Stat
          value={stats.s_rno}
          label="Nađenih u RNO-u"
          hint="Registar neprofitnih organizacija, po OIB-u — izvor telefona i e-maila."
        />
      </div>

      <h2 className="mt-12 text-lg">Prosudba</h2>
      <div className="mt-4 max-w-3xl">
        <Gap>
          Nijedan registar nema polje „vjera". Udruga je katolička ako <strong>bodovanje</strong>{" "}
          naziva, opisa i šifri djelatnosti prijeđe prag; niska pouzdanost nije katalog nego red za
          pregled.
        </Gap>
      </div>
      <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat
          value={stats.po_pouzdanosti["visoka"] ?? 0}
          label="Visoka pouzdanost"
          tone="verified"
          hint={"„Katolički” u nazivu ili jak pojam plus zbroj."}
        />
        <Stat
          value={stats.po_pouzdanosti["srednja"] ?? 0}
          label="Srednja pouzdanost"
          hint="Kombinacija opisa i šifri djelatnosti."
        />
        <Stat
          value={stats.za_pregled_niska}
          label="Niska — za pregled"
          tone="gap"
          hint="Nisu u katalogu."
        />
      </div>

      <div className="mt-12 grid gap-10 md:grid-cols-2">
        <Distribution title="Po kategoriji (aktivne)" data={cats} />
        <Distribution title="Po županiji (aktivne)" data={stats.po_zupaniji_aktivne} />
        <Distribution title="Po biskupiji (aktivne)" data={stats.po_biskupiji_aktivne} />
        <Distribution
          title="Po registru"
          data={stats.po_registru}
          labelFn={(k) => REGISTRY_LABEL[k as Registry] ?? k}
        />
        <Distribution
          title="Odakle koordinata sjedišta"
          data={stats.po_izvoru_koordinata}
          labelFn={(k) => GEO_SOURCE_LABEL[k] ?? k}
        />
      </div>

      <p className="mt-12 text-sm text-muted-foreground">
        Sve brojke dolaze iz{" "}
        <a href="/data/stats.json" className="underline">
          stats.json
        </a>
        , koji nastaje u pipelineu — stranica ih ne računa ponovo. Više o postupku:{" "}
        <Link to="/o-projektu" className="underline">
          o projektu
        </Link>
        .
      </p>
    </Section>
  );
}
