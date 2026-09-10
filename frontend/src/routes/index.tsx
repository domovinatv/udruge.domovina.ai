import { createFileRoute, Link } from "@tanstack/react-router";

import { loadManifest, loadStats } from "@/lib/data";
import { pageHead } from "@/lib/seo";
import { num } from "@/lib/format";
import { Gap, PageHeading, Section, Stat } from "@/components/catalog/Bits";
import { site } from "@/data/site";

export const Route = createFileRoute("/")({
  loader: async () => ({ stats: await loadStats(), manifest: await loadManifest() }),
  head: () =>
    pageHead({
      title: "Katalog katoličkih udruga u Hrvatskoj — udruge.domovina.ai",
      description:
        "Katoličke udruge, bratovštine, molitvene zajednice, zborovi i pokreti u Hrvatskoj na jednom mjestu: OIB, sjedište na karti, biskupija, kontakt. Otvoreni podaci iz Registra udruga.",
      path: "/",
    }),
  component: Home,
});

function Home() {
  const { stats, manifest } = Route.useLoaderData();
  const cats = Object.entries(stats.po_kategoriji_aktivne).slice(0, 4);

  return (
    <>
      <Section className="pb-4">
        <PageHeading
          eyebrow="Otvoreni podaci"
          title="Katoličke udruge u Hrvatskoj"
          lead={
            <>
              Bratovštine, molitvene zajednice, karitativne udruge, zborovi, pokreti i župne udruge
              — iz <strong>Registra udruga</strong>, Registra stranih udruga i crkvene evidencije, s
              OIB-om, sjedištem na karti i kontaktom. Nijedan registar nema polje „vjera": katoličke
              udruge prepoznaje bodovanje, a svaki zapis pokazuje zašto je unutra.
            </>
          }
        >
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              to="/karta"
              className="inline-flex items-center rounded-full bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground"
            >
              Otvori kartu
            </Link>
            <Link
              to="/udruge"
              className="inline-flex items-center rounded-full border border-border px-5 py-2.5 text-sm font-semibold"
            >
              Pretraži {num(stats.udruge_katalog)} udruga
            </Link>
          </div>
        </PageHeading>
      </Section>

      <Section className="pt-0">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Stat
            value={stats.udruge_aktivne}
            label="Aktivnih udruga"
            hint={`Još ${num(stats.udruge_ugasene)} brisanih ili ugašenih ostaje u katalogu kao povijest.`}
          />
          <Stat
            value={stats.s_koordinatama}
            label="Sa sjedištem na karti"
            hint="Koordinate kućnog broja iz DGU registra; gdje adresa ne pogađa, težište naselja."
          />
          <Stat
            value={stats.s_emailom}
            label="Aktivnih s e-mailom"
            tone="verified"
            hint="Iz Registra neprofitnih organizacija Ministarstva financija i Registra udruga."
          />
          <Stat
            value={stats.za_pregled_niska}
            label="Kandidata za pregled"
            tone="gap"
            hint="Bodovanje ih je dotaklo, ali ne potvrdilo. Nisu u katalogu; čekaju ručni pregled."
          />
        </div>
      </Section>

      <Section className="pt-0">
        <h2 className="text-2xl">Tri registra, jedan katalog</h2>
        <p className="mt-3 max-w-3xl text-sm text-muted-foreground">
          Dio katoličkih udruženja nije u Registru udruga: Fokolari, bratstva Franjevačkog
          svjetovnog reda ili Omnia Deo registrirani su kao <em>crkvene</em> pravne osobe, u drugoj
          evidenciji istog ministarstva. Bez nje bi katalog propustio upravo one najkatoličkije.
        </p>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {(
            [
              ["registar-udruga", "Registar udruga RH", "Civilne udruge po Zakonu o udrugama."],
              [
                "evidencija-kc",
                "Crkvena evidencija",
                "Vjernička društva, pokreti i bratstva kao crkvene pravne osobe.",
              ],
              ["strane-udruge", "Strane udruge", "Podružnice stranih udruga u Hrvatskoj."],
            ] as const
          ).map(([key, label, hint]) => (
            <div key={key} className="surface-card p-6">
              <p className="eyebrow">{label}</p>
              <p className="mt-2 text-3xl font-extrabold tabular-nums">
                {num(stats.po_registru_aktivne[key] ?? 0)}
              </p>
              <p className="mt-2 text-sm text-muted-foreground">
                {hint} Aktivnih; ukupno {num(stats.po_registru[key] ?? 0)}.
              </p>
            </div>
          ))}
        </div>
      </Section>

      <Section className="pt-0">
        <h2 className="text-2xl">Najbrojnije kategorije</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {cats.map(([key, v]) => (
            <Link
              key={key}
              to="/udruge"
              search={{ kategorija: key }}
              className="surface-card block p-5 hover:shadow-[var(--shadow-lift)]"
            >
              <p className="text-3xl font-extrabold tabular-nums">{num(v.n)}</p>
              <p className="mt-1 text-sm font-semibold">{v.label}</p>
            </Link>
          ))}
        </div>
        <div className="mt-6 max-w-3xl">
          <Gap>
            Kategorija je naša prosudba iz naziva i opisa, ne podatak iz registra. Isto vrijedi za
            biskupiju: granice biskupija ne postoje kao javan podatak, pa se udruzi pridružuje ona
            čiji derivirani teritorij sadrži njezino sjedište.
          </Gap>
        </div>
        <Link to="/brojke" className="mt-6 inline-block text-sm font-semibold text-primary">
          Sve brojke i pokrivenost →
        </Link>
      </Section>

      <Section className="pt-0">
        <div className="surface-card flex flex-wrap items-center justify-between gap-4 p-6">
          <div>
            <h2 className="text-lg">Podaci su otvoreni</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Katalog je preuzimljiv kao JSON, a pipeline koji ga gradi je javan. Generirano{" "}
              {new Date(manifest.generated_at).toLocaleDateString("hr-HR", { dateStyle: "long" })}.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <a
              href="/data/udruge-index.json"
              className="rounded-full border border-border px-4 py-2 text-sm font-semibold"
            >
              udruge-index.json
            </a>
            <a
              href={site.repo}
              target="_blank"
              rel="noreferrer noopener"
              className="rounded-full border border-border px-4 py-2 text-sm font-semibold"
            >
              Izvorni kod
            </a>
          </div>
        </div>
      </Section>
    </>
  );
}
