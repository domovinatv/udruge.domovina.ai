import { Link } from "@tanstack/react-router";

import type { Udruga } from "@/lib/catalog";
import {
  CATEGORY_LABEL,
  GEO_SOURCE_LABEL,
  REGISTRY_LABEL,
  datum,
  num,
  signalLabel,
} from "@/lib/format";
import { Chip, Crumbs, Gap, Row, Section } from "@/components/catalog/Bits";
import { MiniMap } from "@/components/catalog/MiniMap";
import { site } from "@/data/site";

export function UdrugaDetail({ u }: { u: Udruga }) {
  const path = `/udruga/${u.slug}`;
  const title = u.display_name ?? u.name;

  return (
    <Section>
      <Crumbs
        items={[
          { name: "Naslovnica", path: "/" },
          { name: "Udruge", path: "/udruge" },
          { name: title, path },
        ]}
      />

      <div className="mt-4 grid gap-8 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="min-w-0">
          <h1 className="text-3xl md:text-4xl">{title}</h1>
          {u.display_name && u.display_name !== u.name && (
            <p className="mt-1 text-sm text-muted-foreground">{u.name}</p>
          )}

          <div className="mt-4 flex flex-wrap gap-2">
            <Chip tone="primary">{CATEGORY_LABEL[u.category] ?? u.category_label}</Chip>
            {u.diocese && <Chip>{u.diocese}</Chip>}
            {u.active === 0 && <Chip tone="gap">{u.status ?? "Ugašena"}</Chip>}
            <Chip tone={u.catholic_confidence === "visoka" ? "verified" : "default"}>
              pouzdanost: {u.catholic_confidence}
            </Chip>
          </div>

          {u.active === 0 && (
            <div className="mt-6 max-w-2xl">
              <Gap>
                Udruga u registru nosi status „{u.status}"
                {u.status_date ? ` od ${datum(u.status_date)}` : ""}. Ostaje u katalogu kao
                povijesni podatak; kontakti i osobe vrijede za vrijeme kad je djelovala.
              </Gap>
            </div>
          )}

          {u.goals && (
            <>
              <h2 className="mt-8 text-lg">Ciljevi</h2>
              <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-foreground/85">
                {u.goals}
              </p>
            </>
          )}

          {u.activities_desc && (
            <>
              <h2 className="mt-8 text-lg">Djelatnosti</h2>
              <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-foreground/85">
                {u.activities_desc}
              </p>
            </>
          )}

          <h2 className="mt-8 text-lg">Podaci iz registra</h2>
          <dl className="mt-3">
            <Row label="Registar">{REGISTRY_LABEL[u.registry] ?? u.registry}</Row>
            <Row label="Pravni oblik">{u.legal_form}</Row>
            <Row label="OIB">{u.oib}</Row>
            <Row label="Registarski broj">{u.registry_no}</Row>
            <Row label="Status">{u.status}</Row>
            <Row label="Datum upisa">{datum(u.registered_at)}</Row>
            <Row label="Osnivačka skupština">{datum(u.founded_at)}</Row>
            <Row label="Sjedište">{u.address}</Row>
            <Row label="Strano sjedište">{u.foreign_seat}</Row>
            <Row label="Mjesto">{u.city}</Row>
            <Row label="Naselje / općina">
              {[u.settlement, u.municipality].filter(Boolean).join(", ") || undefined}
            </Row>
            <Row label="Županija">{u.county}</Row>
            <Row label="Ciljane skupine">{u.target_groups}</Row>
            <Row label="Šifre djelatnosti">
              {u.activities?.length ? (
                <ul className="space-y-0.5">
                  {u.activities.map((a) => (
                    <li key={a}>{a}</li>
                  ))}
                </ul>
              ) : undefined}
            </Row>
            <Row label={u.president_role ?? "Zastupa"}>{u.president}</Row>
            <Row label="Telefon">
              {u.phone ? <a href={`tel:${u.phone_e164 ?? u.phone}`}>{u.phone}</a> : undefined}
            </Row>
            <Row label="E-mail">
              {u.email ? <a href={`mailto:${u.email}`}>{u.email}</a> : undefined}
            </Row>
            <Row label="Web">
              {u.website ? (
                <a href={u.website} target="_blank" rel="noreferrer noopener" className="underline">
                  {u.website.replace(/^https?:\/\//, "")}
                </a>
              ) : undefined}
            </Row>
            <Row label="IBAN">{u.iban}</Row>
            <Row label="Koordinate">
              {u.lat !== undefined && u.lng !== undefined ? (
                <>
                  <span className="tabular-nums">
                    {u.lat.toFixed(5)}, {u.lng.toFixed(5)}
                  </span>
                  {u.geo_source && (
                    <span className="text-muted-foreground">
                      {" "}
                      · {GEO_SOURCE_LABEL[u.geo_source] ?? u.geo_source}
                    </span>
                  )}
                </>
              ) : undefined}
            </Row>
          </dl>

          {u.people && u.people.length > 0 && (
            <>
              <h2 className="mt-8 text-lg">Osobe ovlaštene za zastupanje</h2>
              <p className="mt-1 text-xs text-muted-foreground">
                Kako ih objavljuje registar (javno po Zakonu o udrugama). Ne obogaćujemo ih ničim.
              </p>
              <ul className="mt-3 grid gap-2 sm:grid-cols-2">
                {u.people.map((p) => (
                  <li key={`${p.name}-${p.role ?? ""}`} className="surface-card p-3.5 text-sm">
                    <span className="font-semibold">{p.name}</span>
                    {p.role && (
                      <span className="mt-0.5 block text-xs text-muted-foreground">{p.role}</span>
                    )}
                  </li>
                ))}
              </ul>
            </>
          )}

          <h2 className="mt-8 text-lg">Zašto je u katalogu</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Nijedan registar nema polje „vjera". Ova udruga je ušla bodovanjem
            {u.catholic_score !== undefined && u.catholic_score < 10 ? (
              <>
                {" "}
                ({num(u.catholic_score)} bodova, pouzdanost {u.catholic_confidence})
              </>
            ) : null}
            . Signali koji su se okinuli:
          </p>
          <ul className="mt-3 flex flex-wrap gap-1.5">
            {(u.catholic_signals ?? []).map((s) => (
              <li key={s}>
                <Chip tone={s.includes(":-") ? "gap" : "default"} title={s}>
                  {signalLabel(s)}
                </Chip>
              </li>
            ))}
          </ul>
          {u.catholic_confidence === "srednja" && (
            <div className="mt-4 max-w-2xl">
              <Gap>
                Srednja pouzdanost znači da naziv sam ne odlučuje — u katalog ju je dovela
                kombinacija opisa i šifri djelatnosti. Ako je prosudba kriva, to je greška
                bodovanja, ne registra.
              </Gap>
            </div>
          )}
        </div>

        <aside className="space-y-5">
          {u.lat !== undefined && u.lng !== undefined && (
            <MiniMap
              lat={u.lat}
              lng={u.lng}
              label={title}
              zoom={u.geo_source === "naselje-teziste" ? 12 : 15}
            />
          )}

          {u.diocese && (
            <div className="surface-card p-5">
              <p className="eyebrow">Biskupija</p>
              <p className="mt-1.5 font-semibold">{u.diocese}</p>
              <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                {u.diocese_source === "evidencija-kc"
                  ? "Iz crkvene evidencije."
                  : "Izvedeno iz položaja sjedišta nad granicama biskupija koje crkve.domovina.ai računa iz sjedišta župa — granice nisu službene."}
              </p>
              <a
                href={`${site.crkve}/biskupije`}
                target="_blank"
                rel="noreferrer noopener"
                className="mt-2 inline-block text-sm text-primary"
              >
                Biskupije na crkve.domovina.ai →
              </a>
            </div>
          )}

          <div className="surface-card p-5">
            <p className="eyebrow">Izvori</p>
            <p className="mt-2 text-sm text-muted-foreground">
              {REGISTRY_LABEL[u.registry] ?? u.registry}, preko data.gov.hr.
              {u.rno_url ? " Kontakti iz Registra neprofitnih organizacija." : ""}
            </p>
            <ul className="mt-2 space-y-1 text-sm">
              {u.registry_url && (
                <li>
                  <a
                    href={u.registry_url}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="underline"
                  >
                    Registar (pretraga po OIB-u)
                  </a>
                </li>
              )}
              {u.rno_url && (
                <li>
                  <a
                    href={u.rno_url}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="underline"
                  >
                    Zapis u RNO-u
                  </a>
                </li>
              )}
            </ul>
            {u.source && (
              <p className="mt-3 text-xs text-muted-foreground">
                Zapis nastao iz: {u.source.join(", ")}.
              </p>
            )}
          </div>

          <div className="surface-card p-5">
            <p className="eyebrow">Sirovi podatak</p>
            <a href={`/data/udruga/${u.slug}.json`} className="mt-2 block text-sm underline">
              udruga/{u.slug}.json
            </a>
            <Link to="/udruge" className="mt-2 block text-sm text-primary">
              Natrag na popis →
            </Link>
          </div>
        </aside>
      </div>
    </Section>
  );
}

/** Opis za <meta name="description">. */
export function udrugaDescription(u: Udruga): string {
  const bits = [
    CATEGORY_LABEL[u.category] ?? u.category_label,
    u.city ?? "",
    u.diocese ?? "",
    u.active === 1 ? "aktivna" : `status: ${u.status ?? "ugašena"}`,
  ].filter(Boolean);
  return `${u.display_name ?? u.name} — ${bits.join(", ")}. OIB, sjedište, kontakt i osobe ovlaštene za zastupanje u katalogu katoličkih udruga udruge.domovina.ai.`;
}
