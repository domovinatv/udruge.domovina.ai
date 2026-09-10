/**
 * Tipovi za statički katalog iz `public/data/`, koji piše
 * `scripts/34_export_static.py`. Ako se export promijeni, promijeni i ovo.
 * Prazna polja se u exportu izostavljaju, pa je gotovo sve opcionalno.
 */

export type Category =
  | "pokret"
  | "molitvena"
  | "karitativna"
  | "obitelj"
  | "mladi"
  | "glazba"
  | "hodocasnicka"
  | "bratovstina"
  | "ministranti"
  | "mediji"
  | "obrazovanje"
  | "strukovna"
  | "sport"
  | "kultura"
  | "zupna"
  | "ostalo";

export type Registry = "registar-udruga" | "strane-udruge" | "evidencija-kc";
export type Confidence = "visoka" | "srednja";

/** Slim zapis iz udruge-index.json — dovoljno za kartu, popis i pretragu. */
export type UdrugaIndexItem = {
  slug: string;
  name: string;
  category: Category;
  /** 1 = AKTIVAN u registru; 0 = brisana ili prestanak djelovanja. */
  active: 0 | 1;
  confidence: Confidence;
  registry: Registry;
  city?: string;
  county?: string;
  diocese?: string;
  lat?: number;
  lng?: number;
  /** 1 = ima barem e-mail, telefon ili web. */
  contact?: 1;
};

/** udruga/<slug>.json */
export type Udruga = {
  slug: string;
  name: string;
  display_name?: string;
  short_name?: string;
  registry: Registry;
  registry_id?: number;
  registry_no?: string;
  registry_url?: string;
  oib?: string;
  status?: string;
  status_date?: string;
  registered_at?: string;
  founded_at?: string;
  legal_form?: string;
  goals?: string;
  activities_desc?: string;
  target_groups?: string;
  activities?: string[];
  areas?: string[];
  address?: string;
  street?: string;
  housenumber?: string;
  city?: string;
  settlement?: string;
  municipality?: string;
  county?: string;
  postal_code?: string;
  foreign_seat?: string;
  lat?: number;
  lng?: number;
  geo_source?: string;
  diocese?: string;
  diocese_source?: string;
  email?: string;
  website?: string;
  phone?: string;
  phone_e164?: string;
  iban?: string;
  rno_url?: string;
  president?: string;
  president_role?: string;
  catholic_score?: number;
  catholic_confidence: Confidence;
  catholic_signals?: string[];
  category: Category;
  category_label: string;
  active: 0 | 1;
  source?: string[];
  people?: { name: string; role?: string }[];
};

export type Manifest = {
  schema_version: number;
  generated_at: string;
  counts: { udruge: number; aktivne: number; s_koordinatama: number };
};

/** stats.json — mjera iz scripts/40, jedino mjesto gdje se brojke računaju. */
export type Stats = {
  udruge_katalog: number;
  udruge_aktivne: number;
  udruge_ugasene: number;
  za_pregled_niska: number;
  po_pouzdanosti: Record<string, number>;
  po_registru: Record<string, number>;
  po_registru_aktivne: Record<string, number>;
  s_koordinatama: number;
  po_izvoru_koordinata: Record<string, number>;
  s_biskupijom: number;
  s_oib: number;
  s_emailom: number;
  s_webom: number;
  s_telefonom: number;
  s_predsjednikom: number;
  s_rno: number;
  po_kategoriji_aktivne: Record<string, { label: string; n: number }>;
  po_zupaniji_aktivne: Record<string, number>;
  po_biskupiji_aktivne: Record<string, number>;
  osobe: number;
};

export type IndexFile<T> = { count: number; items: T[] };
