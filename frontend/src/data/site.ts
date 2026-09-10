/**
 * Središnji podaci o projektu. Sve što se pojavljuje u headeru, footeru,
 * meta tagovima i structured dataju čita se odavde — nikad hardkodirano
 * u komponenti. Katalog otvorenih podataka, ne poslovni subjekt.
 */
export const site = {
  name: "udruge.domovina.ai",
  fullName: "Katalog katoličkih udruga u Hrvatskoj",
  slogan:
    "Katoličke udruge, bratovštine, molitvene zajednice i pokreti u Hrvatskoj — s OIB-om, sjedištem i kontaktom, iz javnih registara",

  /** Produkcijski origin, bez završnog "/". Canonical i og:url. */
  url: "https://udruge.domovina.ai",

  repo: "https://github.com/domovinatv/udruge.domovina.ai",
  karta: "https://gis.domovina.ai",
  crkve: "https://crkve.domovina.ai",
  email: "",

  licence: "CC-BY 4.0 (izvori: Otvorena dozvola RH, DGU, MFIN)",
} as const;

/** Glavna navigacija. Svaka ruta mora postojati u src/routes/. */
export const nav = [
  { label: "Karta", to: "/karta" },
  { label: "Udruge", to: "/udruge" },
  { label: "Brojke", to: "/brojke" },
  { label: "O projektu", to: "/o-projektu" },
] as const;

/** Izvori podataka — ispisuju se na /o-projektu. */
export const izvori = [
  {
    naziv: "Registar udruga Republike Hrvatske",
    sto: "Naziv, OIB, status, sjedište, ciljevi, djelatnosti i osobe ovlaštene za zastupanje. Nema polja „vjera” — katoličke se prepoznaju bodovanjem.",
    licenca: "Otvorena dozvola RH",
    url: "https://data.gov.hr/ckan/dataset/registar-udruga",
  },
  {
    naziv: "Registar stranih udruga",
    sto: "Strane udruge s podružnicom u Hrvatskoj (Pax Christi, Kolping…).",
    licenca: "Otvorena dozvola RH",
    url: "https://data.gov.hr/ckan/dataset/registar-stranih-udruga-u-republici-hrvatskoj",
  },
  {
    naziv: "Evidencija pravnih osoba Katoličke Crkve",
    sto: "Vjernička društva, pokreti i bratstva koja nisu u Registru udruga jer su registrirana kao crkvene pravne osobe.",
    licenca: "Otvorena dozvola RH",
    url: "https://data.gov.hr/ckan/dataset/evidencija-pravnih-osoba-katolicke-crkve-u-republici-hrvatskoj",
  },
  {
    naziv: "Državna geodetska uprava — Registar prostornih jedinica",
    sto: "Koordinate kućnog broja sjedišta (INSPIRE WFS). Gdje adresa ne pogađa, težište naselja.",
    licenca: "Otvoreni podaci uz navođenje izvora",
    url: "https://geoportal.dgu.hr/",
  },
  {
    naziv: "Registar neprofitnih organizacija (Ministarstvo financija)",
    sto: "Telefon, e-mail i web po OIB-u — ono što Registar udruga nema.",
    licenca: "Javni podaci",
    url: "https://banovac.mfin.hr/rnoprt/",
  },
] as const;
