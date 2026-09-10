import { createFileRoute, Link } from "@tanstack/react-router";

import { izvori, site } from "@/data/site";
import { breadcrumbLd, pageHead } from "@/lib/seo";
import { PageHeading, Section } from "@/components/catalog/Bits";

export const Route = createFileRoute("/o-projektu")({
  head: () => ({
    ...pageHead({
      title: "O projektu — kako nastaje katalog katoličkih udruga",
      description:
        "Izvori, postupak bodovanja i licenca kataloga katoličkih udruga u Hrvatskoj. Sve se gradi reproducibilno iz javnih registara, bez API ključa, a prosudbe su označene.",
      path: "/o-projektu",
    }),
    scripts: [
      breadcrumbLd([
        { name: "Naslovnica", path: "/" },
        { name: "O projektu", path: "/o-projektu" },
      ]),
    ],
  }),
  component: OProjektu,
});

function OProjektu() {
  return (
    <Section>
      <PageHeading
        eyebrow="O projektu"
        title="Katalog katoličkih udruga u Hrvatskoj"
        lead="Popis koji nigdje nije postojao: država vodi udruge, ali ne po vjeri; Crkva vodi svoje pravne osobe, ali ne civilne udruge. Ovdje su spojeni."
      />

      <div className="mt-10 grid gap-10 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="max-w-3xl space-y-8">
          <div>
            <h2 className="text-lg">Kako se prepoznaje katolička udruga</h2>
            <p className="mt-2 text-sm leading-relaxed text-foreground/85">
              Registar udruga ima 70-ak tisuća zapisa i nikakvo polje „vjera". Izmjereno je da ni
              područje djelovanja „duhovnost" (pola su joga i osobni razvoj) ni svetac u nazivu
              (sportski klubovi, mjesta) sami ne izdvajaju katoličke udruge. Zato se{" "}
              <strong>boduje</strong>: naziv punom težinom, opis djelatnosti pola, šifre religijskih
              djelatnosti do tri boda; druge vjere i ezoterija u nazivu isključuju. Svaki zapis nosi
              popis signala koji su se okinuli — to je jedini pošten način da se prosudba objavi kao
              otvoreni podatak.
            </p>
          </div>

          <div>
            <h2 className="text-lg">Tri razine pouzdanosti</h2>
            <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-foreground/85">
              <li>
                <strong>visoka</strong> — „katolički" u nazivu, ili jak pojam u nazivu (župni,
                franjevački, bratovština, molitvena…) i dovoljan zbroj;
              </li>
              <li>
                <strong>srednja</strong> — kombinacija opisa i šifri djelatnosti; u katalogu je,
                stranica to kaže;
              </li>
              <li>
                <strong>niska</strong> — nije u katalogu; red za ručni pregled u izvornom
                repozitoriju.
              </li>
            </ul>
          </div>

          <div>
            <h2 className="text-lg">Što je naša prosudba, a što podatak</h2>
            <p className="mt-2 text-sm leading-relaxed text-foreground/85">
              Naziv, OIB, status, sjedište, osobe i djelatnosti su preslikani iz registra.{" "}
              <strong>Naše</strong> su: ocjena „je li katolička", kategorija, koordinate izabrane
              između više kandidata (uz oznaku sloja preciznosti) i biskupija — pridružena
              prostorno, iz granica koje{" "}
              <a href={site.crkve} className="underline" target="_blank" rel="noreferrer noopener">
                crkve.domovina.ai
              </a>{" "}
              računa iz sjedišta župa, jer službene granice ne postoje kao javan podatak.
            </p>
          </div>

          <div>
            <h2 className="text-lg">Što nedostaje</h2>
            <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-foreground/85">
              <li>Veza na župu: mnoge udruge su župne, a link na stranicu župe još nije spojen.</li>
              <li>
                Kontakti: Registar udruga ih gotovo nema; Registar neprofitnih organizacija daje
                telefon i e-mail za oko dvije trećine aktivnih.
              </li>
              <li>Ručni pregled kandidata s niskom pouzdanosti.</li>
            </ul>
            <p className="mt-3 text-sm">
              <Link to="/brojke" className="underline">
                Sve brojke i pokrivenost →
              </Link>
            </p>
          </div>

          <div>
            <h2 className="text-lg">Licenca</h2>
            <p className="mt-2 text-sm leading-relaxed text-foreground/85">
              Podaci su CC-BY 4.0. Izvori su pod Otvorenom dozvolom Republike Hrvatske (registri),
              otvoreni podaci DGU-a i javni podaci Ministarstva financija — navedite ih uz katalog.
              Prosudbe (pouzdanost, kategorija, biskupija) su naše i tako ih treba i navoditi.
            </p>
          </div>
        </div>

        <aside className="space-y-4">
          <div className="surface-card p-5">
            <p className="eyebrow">Izvori</p>
            <ul className="mt-3 space-y-4">
              {izvori.map((i) => (
                <li key={i.naziv}>
                  <a
                    href={i.url}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="text-sm font-semibold underline"
                  >
                    {i.naziv}
                  </a>
                  <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{i.sto}</p>
                  <p className="mt-1 text-xs text-muted-foreground">Licenca: {i.licenca}</p>
                </li>
              ))}
            </ul>
          </div>

          <div className="surface-card p-5">
            <p className="eyebrow">Preuzimanje</p>
            <ul className="mt-2 space-y-1.5 text-sm">
              <li>
                <a href="/data/udruge-index.json" className="underline">
                  udruge-index.json
                </a>
              </li>
              <li>
                <a href="/data/stats.json" className="underline">
                  stats.json
                </a>
              </li>
              <li>
                <a
                  href={`${site.repo}/tree/main/data/exports`}
                  className="underline"
                  target="_blank"
                  rel="noreferrer noopener"
                >
                  CSV i GeoJSON u repozitoriju
                </a>
              </li>
            </ul>
          </div>

          <div className="surface-card p-5">
            <p className="eyebrow">Kod</p>
            <a
              href={site.repo}
              target="_blank"
              rel="noreferrer noopener"
              className="mt-2 block text-sm underline"
            >
              Pipeline i izvorni kod
            </a>
            <a
              href={site.karta}
              target="_blank"
              rel="noreferrer noopener"
              className="mt-1.5 block text-sm underline"
            >
              Sloj na gis.domovina.ai
            </a>
          </div>
        </aside>
      </div>
    </Section>
  );
}
