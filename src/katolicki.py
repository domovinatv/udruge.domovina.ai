"""Je li udruga katolička? Ocjena, pouzdanost, signali i kategorija.

Registar udruga NEMA polje "vjera". Ima naziv, ciljeve, opis djelatnosti,
ciljane skupine i šifre djelatnosti — i ništa od toga samo za sebe ne
izdvaja katoličke udruge. Izmjereno na dumpu od 70 828 zapisa (svibanj 2026):

  * područje "3. DUHOVNOST" ima 1858 udruga, ali pola su joga, reiki,
    transpersonalna psihologija i "osobni razvoj" (šifra 3.2.2 je najbrojnija);
  * ključna riječ u nazivu ("sv.", "sveti") daje 4217 pogodaka, od kojih je
    velik dio sportskih klubova nazvanih po svecu (MNK Sv. Jakov, KK Sveti
    Matej) i ulica/naselja;
  * presjek to dvoje je samo 411.

Zato je ovo BODOVANJE, ne filtar: svaki signal nosi težinu, naziv vrijedi
dvostruko od opisa, šifre djelatnosti dodaju, a druge vjere i ezoterija
oduzimaju ili isključuju. Prag i težine su izmjereni na uzorcima (vidi
docs/2026-09-10-izgradnja-kataloga.md); mijenjaj ih samo s novim mjerenjem.

Rezultat nosi `signals` — popis pravila koja su se okinula — pa se za svaku
udrugu u katalogu može vidjeti ZAŠTO je unutra. To je jedini pošten način da
se prosudba objavi kao otvoreni podatak.
"""
from __future__ import annotations

import re
from typing import NamedTuple

from src.normalize import norm_text

# --- Katolički signali: (oznaka, regex nad normaliziranim tekstom, težina) ---
# Težina 3 = sam po sebi dovoljan u nazivu; 2 = kršćanski općenito ili
# višeznačan; 1 = slab (svetac u imenu, "duhovni", "vjera").
_CATHOLIC: list[tuple[str, re.Pattern, float]] = [(k, re.compile(p), w) for k, p, w in [
    ("katolic",      r"\b(grko)?katoli\w*", 3),
    ("zupa",         r"\bzup(a|e|i|u|om|n\w*|ljan\w*)\b", 3),
    ("franjevci",    r"\bfranjev\w*|\bframa\b|\bfsr\b|\bofm\b", 3),
    ("caritas",      r"\bkaritat\w*|\bcaritas\b", 3),
    ("red",          r"\bisusov\w*|\bsalezijan\w*|\bdominikan\w*|\bkarmel\w*|\bbenediktin\w*|"
                     r"\bkapucin\w*|\bpavlin\w*|\bdon bosc\w*|\bmilosrdnic\w*|\bcasn\w* sestr\w*|"
                     r"\bkongregacij\w*|\bredovni[ck]\w*|\bsamostan\w*|\bopat\b", 3),
    ("pokret",       r"\bneokatekumen\w*|\bfokolar\w*|\bcursillo\w*|\bkolping\w*|\bmarijin\w*|"
                     r"\bmarijans\w*|\bhagioterap\w*|\bkarizmat\w*|\bobnov\w* u duhu\b|"
                     r"\bduhovn\w* obnov\w*|\bmalo srce\b|\bcenacolo\b|\bmaltes\w*|\bopus dei\b", 3),
    ("hodocasce",    r"\bhodocas\w*", 3),
    ("liturgija",    r"\bministran\w*|\beuharist\w*|\bsakrament\w*|\bklanjat\w*|\bkrunic\w*|"
                     r"\bmolitven\w*|\bmis[aeu]\b|\bliturgij\w*|\bkrizni put\w*", 3),
    # "biskup" namjerno bez `\\w*`: Biskupija je i selo kod Knina, Biškupci i
    # Biškupec također — pa oblici koji su samo mjesto (biskupci, biskupecki)
    # ne smiju bodovati. Kardinal je u "Dolini kardinala" (vinari, Krašić).
    ("klerik",       r"\bnadbiskup\w*|\bbiskup(a|u|om|i|e|sk\w*)\b|\bsvecenik\w*|\bsvecenic\w*|"
                     r"\bzupnik\w*|\bordinarijat\w*|\bpapinsk\w*|\bbogoslov\w*|\bsjemenist\w*", 3),
    ("stepinac",     r"\bstepin(ac|ca|cu|cem)\b", 3),
    ("vjernici",     r"\bvjernik\w*|\bvjernic\w*|\bvjeronau\w*|\bvjerouc\w*|\bkateh\w*|"
                     r"\bpastoral\w*|\bmisionar\w*|\bmisijsk\w*", 3),
    ("marija",       r"\bgosp[aeiu]\b|\bgospin\w*|\bmajk\w* bozj\w*|\bbdm\b|\bbogorodic\w*|"
                     r"\bmarij[aeu] (bistric|pomocnic|kraljic)\w*", 3),
    ("bratovstina",  r"\bbratovst\w*|\bbratstv\w*|\boratorij\w*", 3),
    ("krscanski",    r"\bkrscan\w*|\bkristov\w*|\bkrist(a|u|om|e)?\b|\bisus\w*|\bevandelj\w*|"
                     r"\bbiblij\w*|\bapostol\w*|\bekumen\w*|\bteolo\w*|\bpresvet\w*|"
                     r"\bblazen\w*|\bbl\b|\bevangeliz\w*|\bbiskupij\w*|\bkardinal\w*", 2),
    ("crkva",        r"\bcrkv\w*|\bkapel\w*|\bkatedral\w*|\bbazilik\w*|\bsvetist\w*", 2),
    ("fra",          r"\bfra\b|\bdon\b|\bpater\b|\bpadre\b|\bmons\b", 2),
    ("svetac",       r"\bsv\b|\bsvet(i|a|o|og|oga|e|om|ih|im)\b", 1),
    ("duhovnost",    r"\bduhovn\w*|\bvjer(a|e|i|u|om|sk\w*)\b|\bbozj\w*|\bbozic\w*|\buskrs\w*|"
                     r"\bblagdan\w*|\bandel\w*|\bandeo\b|\bmolitv\w*|"
                     r"\bpap[aeu]\b|\bpapin\w*|\bsinod\w*|\bkrst\w*|\bkrsten\w*", 1),
]]

# --- Isključenja: druge vjere, druge kršćanske zajednice, ezoterija ---------
# U NAZIVU isključuju bezuvjetno; u opisu oduzimaju bodove.
_OTHER: list[tuple[str, re.Pattern]] = [(k, re.compile(p)) for k, p in [
    ("islam",        r"\bislam\w*|\bmuslim\w*|\bdzemat\w*|\bmedzlis\w*|\bimam\w*|\bkuran\w*|\bsufi\w*"),
    ("pravoslavlje", r"\bpravoslav\w*|\beparh\w*|\bparohij\w*|\bmitropol\w*|\bspc\b"),
    ("protestant",   r"\bevandeosk\w*|\bevangelic\w*|\bevangeli[ck]k\w*|\bbaptist\w*|\bprotestant\w*|"
                     r"\bpentekost\w*|\breformir\w*|\breformat\w*|\bluteran\w*|\bkalvin\w*|"
                     r"\bmetodist\w*|\badventist\w*|\bkristova crkva\b|\bcrkva bozja\b|"
                     r"\brijec zivota\b|\bnovoapostol\w*|\bcrkva cjelovitog\b|\bmormon\w*|"
                     r"\bjehov\w*|\bstarokatol\w*|\bkrscanska zajednica\b|\bkristov\w* crkv\w*|"
                     r"\bcrkv\w* kristov\w*|\bgospodar crkve\b|\bellel\b|\bcrkva zivog\w*|"
                     r"\bkrscanski centar\b|\bkrscanska crkva\b|\biglesia\b|\bkrscansk\w* zajednic\w*|"
                     r"\bkrist je\b|\bcrkva rijeci\b|\bpuni evandelj\w*|\bbogumil\w*"),
    ("zidovstvo",    r"\bzidov\w*|\bjevrej\w*|\bhebrej\w*|\bjudaiz\w*|\bsinagog\w*|\bkabal\w*"),
    ("istok",        r"\bbudis\w*|\bbudiz\w*|\bhindu\w*|\bkrisn\w*|\bsikh\w*|\bbahai\w*|\bjog[aeiu]\b|"
                     r"\byoga\b|\bbhakti\w*|\bmantr\w*|\bcakr\w*|\bchakr\w*|\bved(ski|ant\w*|sk\w*)\b|"
                     r"\bayurved\w*|\bsai baba\b|\bbrahma\b|\bfalun\w*|\btao\b|\btaois\w*|\bzen\b|"
                     r"\bfeng shui\b|\bqi ?gong\b|\btai ?chi\b|\batma\b|\bprana\w*|\bkundalini\b|"
                     r"\bvipassan\w*|\bosho\b|\bhare\b|\bguru\w*|\bsatsang\w*"),
    ("ezoterija",    r"\breiki\b|\bmeditac\w*|\bsaman\w*|\btranspersonal\w*|\bastrolo\w*|\btarot\w*|"
                     r"\bokult\w*|\bholist\w*|\bbioenerg\w*|\bteozof\w*|\bteosof\w*|\bantropozof\w*|"
                     r"\bwicc\w*|\bpagan\w*|\bpogan\w*|\brodnovjer\w*|\bscientolo\w*|\bezoter\w*|"
                     r"\bspiritis\w*|\brozenkroj\w*|\bdruid\w*|\bnew age\b"),
]]

# Šifre djelatnosti (prefiks) → bodovi. 3.1.x su religijske/vjerničke;
# 3.2.x je "osobni razvoj" gdje živi joga, pa nosi malo. "14." postoji u DVIJE
# nomenklature — u staroj je "14. DUHOVNA", u novoj "14. ZAŠTITA ZDRAVLJA" —
# pa se za nju gleda i naziv područja, ne samo šifra. Ista šifra upisana
# dvaput (događa se) broji se jednom.
_CODE_WEIGHTS: list[tuple[str, float]] = [
    ("3.1.1.", 2.0), ("3.1.3.", 2.0), ("3.1.2.", 1.0),
    ("3.2.1.", 1.0), ("3.2.2.", 0.5), ("3.2.3.", 0.5), ("3.3.", 0.5),
]
_RELIGIOUS_CODES = ("3.1.1.", "3.1.3.", "3.1.2.")
_SPORT_AREAS = ("12. SPORT", "1. ŠPORTSKA", "18. NOMENKLATURA SPORTOVA")

# Pragovi — mijenjaj samo s mjerenjem.
T_VISOKA = 6.0
T_SREDNJA = 4.0
T_NISKA = 2.5


class Result(NamedTuple):
    score: float
    confidence: str | None      # visoka | srednja | niska | None (nije katolička)
    signals: list[str]
    excluded_by: str | None


# Mjesna imena koja sadrže katoličku riječ, a nisu katolički signal:
# "Župa dubrovačka" je općina (Judo klub Župa dubrovačka), "Sveti Ivan Zelina"
# je grad. Spajaju se u jednu "riječ" prije bodovanja pa ih regexi ne vide.
_PLACE_NEUTRAL = [
    (re.compile(r"\bzupa dubrovacka\b"), "zupadubrovacka"),
    (re.compile(r"\bzupe dubrovacke\b"), "zupedubrovacke"),
    (re.compile(r"\bsveti (ivan zelina|kriz zacretje|petar u sumi|ilija|filip i jakov|"
                r"lovrec|martin na muri|dura|juraj na bregu|petar orehovec|rok|klement)\b"), "mjesto"),
    (re.compile(r"\bsvet(a|o) (nedelja|marija|jana|ana|vid)\b"), "mjesto"),
]


def _neutralize(text: str) -> str:
    for pat, rep in _PLACE_NEUTRAL:
        text = pat.sub(rep, text)
    return text


def _matches(text: str, rules) -> dict[str, float]:
    return {k: w for k, pat, w in rules if pat.search(text)}


def classify(name: str | None, goals: str | None = None, activities_desc: str | None = None,
             target_groups: str | None = None,
             activities: list[tuple[str, str]] | None = None) -> Result:
    """`activities` je lista (šifra+naziv djelatnosti, naziv područja) iz registra."""
    n = _neutralize(norm_text(name))
    d = _neutralize(norm_text(" ".join(x for x in (goals, activities_desc, target_groups) if x)))
    signals: list[str] = []

    # 1. Isključenja u nazivu — bezuvjetno.
    for k, pat in _OTHER:
        if pat.search(n):
            return Result(-100.0, None, [f"naziv:{k}"], k)

    # 2. Naziv, puna težina.
    name_hits = _matches(n, _CATHOLIC)
    name_score = sum(name_hits.values())
    signals += [f"naziv:{k}" for k in name_hits]

    # 3. Opis, pola težine, kapa 4 — dug opis s deset ključnih riječi ne smije
    #    sam prebaciti prag (tako bi "duhovne" udruge iz 3.2.2 ušle).
    #    Iznimka je sama riječ "katolički" — u opisu je jednako odlučna kao u
    #    nazivu ("udruga okuplja katoličke liječnike…").
    desc_hits = _matches(d, _CATHOLIC)
    desc_score = min(4.0, sum(w if k == "katolic" else w * 0.5 for k, w in desc_hits.items()))
    signals += [f"opis:{k}" for k in desc_hits]

    # 4. Šifre djelatnosti — religijske (3.1.x) do 3 boda, "duhovne" (3.2.x,
    #    3.3, stara "14. DUHOVNA") zajedno najviše 1: to su područja u kojima
    #    joga i katolička molitvena zajednica stoje jedna do druge.
    rel = oth = 0.0
    seen: set[str] = set()
    areas: list[str] = []
    for code, area in activities or []:
        areas.append(area or "")
        key = code.split(" ")[0]
        if key in seen:
            continue
        seen.add(key)
        if key.startswith("14.") and "DUHOVN" in (area or "").upper():
            oth += 0.5
            signals.append("djelatnost:14.duhovna")
            continue
        for prefix, w in _CODE_WEIGHTS:
            if key.startswith(prefix):
                if prefix in _RELIGIOUS_CODES:
                    rel += w
                else:
                    oth += w
                signals.append(f"djelatnost:{prefix}")
                break
    code_score = min(3.0, rel) + min(1.0, oth)

    # 5. Druga vjera / ezoterija u opisu — oduzima, ne isključuje (dijalog s
    #    islamom je i katolička djelatnost).
    penalty = 0.0
    for k, pat in _OTHER:
        if pat.search(d):
            penalty -= 1.0
            signals.append(f"opis:-{k}")
    penalty = max(-2.0, penalty)

    # 6. Sportski klub nazvan po svecu: sve mu je sport, a "sv." u imenu.
    if areas and all(a.startswith(_SPORT_AREAS) for a in areas) and name_score < 3:
        penalty -= 2.0
        signals.append("sport:-svetac-u-imenu")

    # 7. Jak katolički pojam u NAZIVU vrijedi više od zbroja: udruga koja se
    #    zove "Marijini obroci" ili "Bratovština sv. Vida" je katolička i kad
    #    joj je opis prazan. Bez ovoga bi takve padale u "niska".
    if any(w >= 3 for w in name_hits.values()):
        name_score += 1.0
        signals.append("naziv:jak-pojam")

    score = round(name_score + desc_score + code_score + penalty, 2)
    # "Katolička" u nazivu je definicija, ne indicija — visoka bez obzira na zbroj.
    if "katolic" in name_hits or (score >= T_VISOKA and name_score >= 3):
        conf = "visoka"
    elif score >= T_SREDNJA:
        conf = "srednja"
    elif score >= T_NISKA:
        conf = "niska"
    else:
        conf = None
    return Result(score, conf, signals, None)


# --- Kategorija (za filtar na karti i u katalogu) ---------------------------
# Prvo pravilo koje pogodi naziv pobjeđuje; opis se gleda tek ako naziv ne
# kaže ništa. Redoslijed je bitan: "zbor župe sv. Ante" je zbor, ne župna
# udruga; "Frama Split" je pokret, ne mladi.
CATEGORIES: dict[str, str] = {
    "pokret":        "Pokreti i laičke zajednice",
    "molitvena":     "Molitvene zajednice",
    "karitativna":   "Karitativne i humanitarne",
    "obitelj":       "Obitelj i život",
    "mladi":         "Mladi i studenti",
    "glazba":        "Zborovi i crkvena glazba",
    "hodocasnicka":  "Hodočašća",
    "bratovstina":   "Bratovštine",
    "ministranti":   "Ministranti",
    "mediji":        "Mediji i nakladništvo",
    "obrazovanje":   "Obrazovanje i kateheza",
    "strukovna":     "Strukovne (liječnici, učitelji…)",
    "sport":         "Sport i rekreacija",
    "kultura":       "Kultura i baština",
    "zupna":         "Župne udruge",
    "ostalo":        "Ostalo",
}

_CATEGORY_RULES: list[tuple[str, re.Pattern]] = [(k, re.compile(p)) for k, p in [
    ("glazba",       r"\bzbor\w*|\bpjeva\w*|\bglazb\w*|\borgulj\w*|\bklap[aei]\b|\bkor\b"),
    ("ministranti",  r"\bministran\w*"),
    ("bratovstina",  r"\bbratovst\w*|\bbratstv\w*"),
    ("hodocasnicka", r"\bhodocas\w*"),
    ("pokret",       r"\bfranjev\w*|\bframa\b|\bfsr\b|\bneokatekumen\w*|\bfokolar\w*|\bcursillo\w*|"
                     r"\bkolping\w*|\bmarijin\w* legij\w*|\bhagioterap\w*|\bkarizmat\w*|\bpokret\w*|"
                     r"\btreci red\w*|\blaik\w*|\bopus\b|\bobnov\w* u duhu\b|\bkatekumen\w*"),
    ("molitvena",    r"\bmolitv\w*|\bkrunic\w*|\bklanjat\w*|\beuharist\w*|\bzajednic\w*|\bsrca isusov\w*"),
    ("karitativna",  r"\bkaritat\w*|\bcaritas\b|\bhumanitar\w*|\bmilosrd\w*|\bsiromas\w*|\bbeskucn\w*|"
                     r"\bpomoc\w*|\bsolidarn\w*|\bdobrotvor\w*|\bvolonter\w*"),
    ("obitelj",      r"\bobitelj\w*|\bbrak\w*|\bbracn\w*|\broditelj\w*|\bza zivot\b|\bnerod\w*|"
                     r"\bpro ?life\b|\bmajk[aei]\b|\bmaterinstv\w*|\btrudnic\w*"),
    ("mladi",        r"\bmlad\w*|\bstuden\w*|\bakadem\w*|\bskolar\w*|\bdjec\w*|\bomladin\w*"),
    ("mediji",       r"\bmedij\w*|\bradio\b|\btelevizij\w*|\bportal\w*|\bnaklad\w*|\bizdava\w*|"
                     r"\bknjig\w*|\bnovin\w*|\bglasnik\w*|\bcasopis\w*"),
    ("obrazovanje",  r"\bskol\w*|\bobrazov\w*|\bodgoj\w*|\bvrtic\w*|\bkateh\w*|\bedukac\w*|"
                     r"\bvjeronau\w*|\bvjerouc\w*|\bucili\w*|\bgimnazij\w*"),
    ("strukovna",    r"\blijecni\w*|\bucitelj\w*|\bnastavni\w*|\bprosvjet\w*|\bpravni\w*|\bnovinar\w*|"
                     r"\bpoduzetni\w*|\bgospodarstveni\w*|\binzenjer\w*|\bmedicin\w*|\bsestar\w*|"
                     r"\bpsiholo\w*|\bznanstven\w*|\bintelektual\w*"),
    ("sport",        r"\bsport\w*|\bnogomet\w*|\bkosark\w*|\bmalonogomet\w*|\bplaninar\w*|\brekreac\w*|"
                     r"\bklub\b|\bliga\b"),
    ("kultura",      r"\bkultur\w*|\bbastin\w*|\bpovijes\w*|\bumjetn\w*|\blikovn\w*|\bkazalis\w*|"
                     r"\bmuzej\w*|\bspomen\w*|\bfolklor\w*|\bkud\b"),
    ("zupna",        r"\bzup(a|e|i|u|n\w*|ljan\w*)\b|\bcrkv\w*|\bkapel\w*|\bsvetist\w*|\bobnov\w*|\bgradnj\w*"),
]]


def categorize(name: str | None, goals: str | None = None,
               activities_desc: str | None = None) -> str:
    n = norm_text(name)
    for k, pat in _CATEGORY_RULES:
        if pat.search(n):
            return k
    d = norm_text(" ".join(x for x in (goals, activities_desc) if x))
    for k, pat in _CATEGORY_RULES:
        if pat.search(d):
            return k
    return "ostalo"
