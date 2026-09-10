import type { Category, Registry } from "./catalog";

/** Hrvatski nazivi kategorija iz `src/katolicki.py` CATEGORIES. Zatvoren skup. */
export const CATEGORY_LABEL: Record<Category, string> = {
  pokret: "Pokreti i laičke zajednice",
  molitvena: "Molitvene zajednice",
  karitativna: "Karitativne i humanitarne",
  obitelj: "Obitelj i život",
  mladi: "Mladi i studenti",
  glazba: "Zborovi i crkvena glazba",
  hodocasnicka: "Hodočašća",
  bratovstina: "Bratovštine",
  ministranti: "Ministranti",
  mediji: "Mediji i nakladništvo",
  obrazovanje: "Obrazovanje i kateheza",
  strukovna: "Strukovne udruge",
  sport: "Sport i rekreacija",
  kultura: "Kultura i baština",
  zupna: "Župne udruge",
  ostalo: "Ostalo",
};

export const CATEGORY_ORDER: Category[] = [
  "molitvena",
  "karitativna",
  "bratovstina",
  "glazba",
  "pokret",
  "mladi",
  "hodocasnicka",
  "kultura",
  "obitelj",
  "zupna",
  "sport",
  "strukovna",
  "obrazovanje",
  "mediji",
  "ministranti",
  "ostalo",
];

export const REGISTRY_LABEL: Record<Registry, string> = {
  "registar-udruga": "Registar udruga RH",
  "strane-udruge": "Registar stranih udruga",
  "evidencija-kc": "Evidencija pravnih osoba Katoličke Crkve",
};

export const CONFIDENCE_LABEL: Record<string, string> = {
  visoka: "visoka",
  srednja: "srednja",
  niska: "niska",
};

/** Sloj preciznosti koordinate — razlika je kilometri, a na karti izgleda isto. */
export const GEO_SOURCE_LABEL: Record<string, string> = {
  "dgu-adresa": "adresna točka kućnog broja (DGU)",
  "dgu-ulica-fuzzy": "adresna točka, ulica nađena približno (DGU)",
  "naselje-teziste": "težište naselja — točnost razine mjesta",
};

/** Signal klasifikatora → čitljivo. "naziv:katolic" → "u nazivu: katolički". */
export function signalLabel(s: string): string {
  const [where, what] = s.split(":", 2);
  const WHAT: Record<string, string> = {
    katolic: "„katolički”",
    zupa: "župa / župni",
    franjevci: "franjevci / FSR / Frama",
    caritas: "karitativno",
    red: "redovnički red ili zajednica",
    pokret: "crkveni pokret",
    hodocasce: "hodočašće",
    liturgija: "liturgija, molitva, sakramenti",
    klerik: "biskup, svećenik, župnik",
    stepinac: "Stepinac",
    vjernici: "vjernici, pastoral, kateheza, misije",
    marija: "marijanski zaziv",
    bratovstina: "bratovština / bratstvo",
    krscanski: "kršćanski, Krist, evanđelje",
    crkva: "crkva, kapela, svetište",
    fra: "fra / don / mons.",
    svetac: "svetac u nazivu",
    duhovnost: "duhovnost, vjera, blagdani",
    "jak-pojam": "jak pojam u nazivu (bonus)",
  };
  const WHERE: Record<string, string> = {
    naziv: "u nazivu",
    opis: "u opisu",
    djelatnost: "šifra djelatnosti",
    registar: "registar",
    sport: "sport",
  };
  const w = what ?? "";
  if (where === "djelatnost") return `šifra djelatnosti ${w}`;
  if (where === "registar") return "upisana u crkvenu evidenciju";
  if (w.startsWith("-"))
    return `${WHERE[where ?? ""] ?? where}: druga vjera ili ezoterija (${w.slice(1)}) — oduzima`;
  return `${WHERE[where ?? ""] ?? where}: ${WHAT[w] ?? w}`;
}

/**
 * Hrvatska sklonidba uz broj: 1 udruga, 2–4 udruge, 5+ udruga — po ZADNJOJ
 * znamenki, pa 21 ide u jedninu a 11 u množinu.
 */
export function sklon(n: number, one: string, few: string, many: string): string {
  const d1 = n % 10;
  const d2 = n % 100;
  if (d2 >= 11 && d2 <= 14) return many;
  if (d1 === 1) return one;
  if (d1 >= 2 && d1 <= 4) return few;
  return many;
}

export function broj(n: number, one: string, few: string, many: string): string {
  return `${num(n)} ${sklon(n, one, few, many)}`;
}

const NF = new Intl.NumberFormat("hr-HR");
export const num = (n: number) => NF.format(n);
export const pct = (n: number) => `${n.toFixed(1).replace(".", ",")} %`;

/** ISO datum → "12. studenoga 2004." */
export function datum(iso?: string): string | undefined {
  if (!iso) return undefined;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return new Intl.DateTimeFormat("hr-HR", { dateStyle: "long" }).format(d);
}

/** Za pretragu bez dijakritike: "Šibenik" i "Sibenik" pogađaju isto. */
export function foldHr(s: string): string {
  return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/đ/g, "d");
}
