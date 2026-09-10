import { createFileRoute } from "@tanstack/react-router";

import { loadUdruga } from "@/lib/data";
import { breadcrumbLd, organizationLd, pageHead } from "@/lib/seo";
import { UdrugaDetail, udrugaDescription } from "@/components/catalog/UdrugaDetail";

export const Route = createFileRoute("/udruga/$slug")({
  loader: ({ params }) => loadUdruga(params.slug),
  head: ({ loaderData }) => {
    const u = loaderData;
    if (!u) return {};
    const path = `/udruga/${u.slug}`;
    const title = u.display_name ?? u.name;
    return {
      ...pageHead({
        title: `${title}${u.city ? `, ${u.city}` : ""} — katolička udruga`,
        description: udrugaDescription(u),
        path,
        type: "article",
      }),
      scripts: [
        breadcrumbLd([
          { name: "Naslovnica", path: "/" },
          { name: "Udruge", path: "/udruge" },
          { name: title, path },
        ]),
        organizationLd({
          name: u.name,
          path,
          oib: u.oib,
          address: u.address,
          city: u.city,
          phone: u.phone_e164 ?? u.phone,
          email: u.email,
          website: u.website,
          parent: u.diocese,
        }),
      ],
    };
  },
  component: UdrugaPage,
});

function UdrugaPage() {
  return <UdrugaDetail u={Route.useLoaderData()} />;
}
