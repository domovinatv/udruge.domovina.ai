import { createFileRoute } from "@tanstack/react-router";

import { CatalogMap } from "@/components/catalog/CatalogMap";
import { PageHeading, Section } from "@/components/catalog/Bits";
import { breadcrumbLd, pageHead } from "@/lib/seo";

export const Route = createFileRoute("/karta")({
  head: () => ({
    ...pageHead({
      title: "Karta katoličkih udruga u Hrvatskoj",
      description:
        "Interaktivna karta sjedišta katoličkih udruga, bratovština, molitvenih zajednica i pokreta u Hrvatskoj. Filtriranje po kategoriji, oznaka udruga s kontaktom.",
      path: "/karta",
    }),
    scripts: [
      breadcrumbLd([
        { name: "Naslovnica", path: "/" },
        { name: "Karta", path: "/karta" },
      ]),
    ],
  }),
  component: Karta,
});

function Karta() {
  return (
    <Section>
      <PageHeading
        eyebrow="Karta"
        title="Sjedišta katoličkih udruga"
        lead="Točka je sjedište iz registra. Klik na točku otvara stranicu udruge."
      />
      <div className="mt-6">
        <CatalogMap />
      </div>
    </Section>
  );
}
