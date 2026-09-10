import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";

import { UdrugaBrowser } from "@/components/catalog/UdrugaBrowser";
import { Gap, PageHeading, Section } from "@/components/catalog/Bits";
import { loadStats } from "@/lib/data";
import { breadcrumbLd, pageHead } from "@/lib/seo";
import { num } from "@/lib/format";
import type { Category } from "@/lib/catalog";

const searchSchema = z.object({
  kategorija: z.string().optional(),
  zupanija: z.string().optional(),
});

export const Route = createFileRoute("/udruge")({
  validateSearch: searchSchema,
  loader: async () => ({ stats: await loadStats() }),
  head: () => ({
    ...pageHead({
      title: "Popis katoličkih udruga u Hrvatskoj — pretraga po nazivu, mjestu i kategoriji",
      description:
        "Pretraživ popis katoličkih udruga, bratovština, molitvenih zajednica, zborova i pokreta u Hrvatskoj, s OIB-om, sjedištem, biskupijom i kontaktom. Filtri po kategoriji i županiji.",
      path: "/udruge",
    }),
    scripts: [
      breadcrumbLd([
        { name: "Naslovnica", path: "/" },
        { name: "Udruge", path: "/udruge" },
      ]),
    ],
  }),
  component: Udruge,
});

function Udruge() {
  const { stats } = Route.useLoaderData();
  const { kategorija, zupanija } = Route.useSearch();

  return (
    <Section>
      <PageHeading
        eyebrow="Katalog"
        title="Katoličke udruge"
        lead={
          <>
            {num(stats.udruge_aktivne)} aktivnih i {num(stats.udruge_ugasene)} ugašenih udruga iz
            tri javna registra. Pretraga radi bez dijakritike.
          </>
        }
      />
      <div className="mt-6 max-w-3xl">
        <Gap>
          Katalog sadrži udruge s pouzdanosti „visoka" i „srednja". Još{" "}
          {num(stats.za_pregled_niska)} kandidata s niskom pouzdanosti nije uključeno — dostupni su
          u izvornom repozitoriju kao red za ručni pregled.
        </Gap>
      </div>
      <div className="mt-8">
        <UdrugaBrowser
          initialCategory={kategorija as Category | undefined}
          initialCounty={zupanija}
        />
      </div>
    </Section>
  );
}
