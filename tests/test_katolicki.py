"""Klasifikator — svaki primjer je stvarna udruga iz Registra (ili minimalna
varijacija) na kojoj je pravilo bilo krivo prije nego što je ispravljeno."""
from src.katolicki import categorize, classify


def conf(name, **kw):
    return classify(name, **kw).confidence


def test_katolicki_u_nazivu_je_dovoljan():
    assert conf('KATOLIČKA UDRUGA "MOLITVA"') == "visoka"
    assert conf("Hrvatska katolička udruga medicinskih sestara i tehničara") in ("visoka", "srednja")


def test_zupanija_nije_zupa():
    # "županija" sadrži "žup" — ne smije bodovati kao župa.
    r = classify("KUGLAČKI SAVEZ KARLOVAČKE ŽUPANIJE")
    assert r.confidence is None
    assert not any(s.startswith("naziv:zupa") for s in r.signals)


def test_zupa_dubrovacka_je_opcina():
    assert conf("Judo klub Župa dubrovačka") is None
    assert conf("Limena glazba Župa dubrovačka") is None


def test_sportski_klub_nazvan_po_svecu():
    assert conf('MALONOGOMETNI KLUB "SVETI JAKOV"',
                activities=[("1.2.1. NOGOMET", "1. ŠPORTSKA")]) is None
    assert conf('KOŠARKAŠKI KLUB "SVETI MATEJ" VIŠKOVO',
                activities=[("12.1. Sudjelovanje u sportskom natjecanju", "12. SPORT")]) is None


def test_druga_vjera_u_nazivu_iskljucuje():
    for name in ["UDRUGA VJERNIKA KOPTSKE PRAVOSLAVNE CRKVE SVETOG MARKA",
                 "PRESBITERSKA REFORMATSKA KRŠĆANSKA ZAJEDNICA VJERNIKA",
                 "MEĐUNARODNO DRUŠTVO ZA SVJESNOST KRIŠNE U ZAGREBU",
                 "UDRUGA VJERNIKA MEĐUNARODNE KRISTOVE CRKVE ZAGREB",
                 "UDRUGA ZA KRŠĆANSKU DUHOVNU OBNOVU ELLEL HRVATSKA",
                 "KRIYA YOGA"]:
        r = classify(name)
        assert r.confidence is None and r.excluded_by, name


def test_grkokatolici_su_katolici():
    assert conf("Udruga grkokatoličkih vjernika Žumberka") == "visoka"


def test_crveni_kriz_nije_krizni_put():
    assert conf("HRVATSKI CRVENI KRIŽ", goals="humanitarna pomoć", activities=[
        ("14.1. Preventivno djelovanje", "14. ZAŠTITA ZDRAVLJA")]) is None


def test_stara_i_nova_sifra_14():
    # "14." je u staroj nomenklaturi DUHOVNA, u novoj ZAŠTITA ZDRAVLJA.
    a = classify("Udruga X", activities=[("14.1.1. Duhovna", "14. DUHOVNA")])
    b = classify("Udruga X", activities=[("14.1.1. Prevencija", "14. ZAŠTITA ZDRAVLJA")])
    assert a.score > b.score


def test_ista_sifra_dvaput_broji_jednom():
    once = classify("Udruga X", activities=[("3.1.1. Promicanje religijske etike", "3. DUHOVNOST")])
    twice = classify("Udruga X", activities=[("3.1.1. Promicanje religijske etike", "3. DUHOVNOST")] * 2)
    assert once.score == twice.score


def test_jak_pojam_u_nazivu_bez_opisa_je_barem_srednja():
    assert conf('"MARIJINI OBROCI"') in ("srednja", "visoka")
    assert conf("Bratovština Svetoga Vida - Vrhovčak") in ("srednja", "visoka")


def test_biskupija_kao_selo_ne_boduje_kao_klerik():
    r = classify('DRUŠTVO SPORTSKE REKREACIJE "BISKUPIJA"')
    assert "naziv:klerik" not in r.signals
    assert conf("Dobrovoljno vatrogasno društvo Biškupci") is None


def test_opis_s_drugom_vjerom_samo_oduzima():
    r = classify("Katolička udruga za dijalog", goals="dijalog s islamom i pravoslavljem")
    assert r.confidence is not None
    assert any(s.startswith("opis:-") for s in r.signals)


def test_kategorije():
    assert categorize("Župni zbor sv. Ante") == "glazba"
    assert categorize("FRAMA Split") == "pokret"
    assert categorize("Molitvena zajednica Kraljice ljubavi") == "molitvena"
    assert categorize("Udruga za obnovu crkve sv. Roka") == "zupna"
    assert categorize('KARITATIVNO DRUŠTVO "KRUH SVETOG ANTE"') == "karitativna"
    assert categorize("Hrvatsko katoličko liječničko društvo") == "strukovna"
