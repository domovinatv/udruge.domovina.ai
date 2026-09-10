"""Naziv → slug/normalizirani ključ, s ispravnim rukovanjem hrvatskim đ/Đ.

Prilagođeno iz ../crkve.domovina.ai/src/normalize.py. Razlika: ovdje se NE
skida nikakav prefiks. Kod crkava "ŽUPA" nosi tip, a identitet je titular;
kod udruga je "Udruga …" / "Zajednica …" / "Bratovština …" dio imena pod kojim
je udruga upisana i pod kojim je ljudi traže.
"""
from __future__ import annotations

import re
import unicodedata

_NON_ALNUM = re.compile(r"[^a-z0-9]+")

# Đ/đ se ne dekomponiraju pod NFKD (samostalna slova), mapiramo eksplicitno.
_CROATIAN_MAP = str.maketrans({"đ": "d", "Đ": "D"})


def strip_diacritics(s: str) -> str:
    s = (s or "").translate(_CROATIAN_MAP)
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def slugify(name: str, city: str | None = None, suffix: str | None = None) -> str:
    """Stabilan URL slug: naziv + mjesto + sufiks.

    Nazivi udruga NISU jedinstveni ("Udruga mladih" postoji u desecima
    mjesta), a ni naziv+mjesto nije (ista udruga zna biti upisana dvaput,
    jednom BRISAN). Zato pozivatelj uvijek daje `suffix` — zadnje 4 znamenke
    OIB-a, a bez OIB-a UDR_ID iz registra.
    """
    base = strip_diacritics(name or "").lower().strip()
    if city:
        city_norm = strip_diacritics(city).lower().strip()
        if city_norm and city_norm not in base:
            base = f"{base}-{city_norm}"
    base = _NON_ALNUM.sub("-", base).strip("-")
    # Registarski nazivi znaju imati 200+ znakova; slug ostaje čitljiv, a
    # sufiks (jamstvo jedinstvenosti) uvijek ostaje na kraju.
    if len(base) > 110:
        base = base[:110].rpartition("-")[0] or base[:110]
    if suffix:
        base = f"{base}-{_NON_ALNUM.sub('-', strip_diacritics(str(suffix)).lower()).strip('-')}"
    return base or "udruga"


def norm_text(s: str | None) -> str:
    """Ključ za usporedbu/klasifikaciju: bez dijakritike, mala slova,
    interpunkcija → razmak, jedan razmak. "SV." ostaje "sv" kao riječ."""
    base = strip_diacritics(s or "").lower()
    base = re.sub(r"[^a-z0-9]+", " ", base)
    return re.sub(r"\s+", " ", base).strip()


def title_case_hr(s: str) -> str:
    """UPPERCASE registarski nazivi → čitljivo. Čuva "sv.", kratice, rimske brojeve.

    Registar udruga oko polovice naziva piše velikim slovima ("UDRUGA
    HRVATSKIH KATOLIČKIH LIJEČNIKA"), drugu polovicu kako je podnositelj
    upisao. Naziv koji već ima mala slova ne diramo — u njemu je velika/mala
    slova birao netko tko zna kako se udruga zove.
    """
    if not s:
        return s
    if s != s.upper():
        return " ".join(s.split())
    keep_upper = {"BDM", "OFM", "OP", "SJ", "OSB", "OCD", "SDB", "HR", "RH", "HKD",
                  "HKLD", "FSR", "MI", "HKM", "HKZ", "KUD", "HDKB", "II", "III"}
    roman = re.compile(r"^[IVXLCDM]{2,}\.?$")
    lower_words = {"i", "u", "na", "od", "za", "sa", "s", "iz", "te", "ili", "o", "pri",
                   "kod", "do", "po", "uz"}
    out: list[str] = []
    for w in s.split():
        core = w.strip("\"„”“'()")
        if out and w.lower() in lower_words:
            out.append(w.lower())
        elif core.upper() in keep_upper or roman.match(core.upper()):
            out.append(w.upper())
        elif w.upper() in {"SV.", "SV", "BL.", "BL"}:
            out.append(w.lower() if w.endswith(".") else w.lower() + ".")
        else:
            # Čuva navodnike i zagrade oko riječi: "PRILIKA" → "Prilika".
            i = w.find(core) if core else 0
            out.append(w[:i] + core.capitalize() + w[i + len(core):])
    return " ".join(out)
