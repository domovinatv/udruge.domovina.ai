from src.datagovhr import split_sjediste, split_street
from src.ingest import iso_date, pick_president


def test_split_sjediste_zadnji_zarez():
    assert split_sjediste("Dunavski prilaz 2, Vukovar") == ("Dunavski prilaz 2", "Vukovar")
    assert split_sjediste("Trg bana J. Jelačića, 1, Zagreb") == ("Trg bana J. Jelačića, 1", "Zagreb")
    assert split_sjediste("Prizna") == (None, "Prizna")
    assert split_sjediste(None) == (None, None)
    # selo s brojem zalijepljenim na ime, bez zareza
    assert split_sjediste("Tisovac5i") == ("Tisovac 5i", "Tisovac")
    assert split_sjediste("Crkveni Bok60") == ("Crkveni Bok 60", "Crkveni Bok")


def test_split_street():
    assert split_street("Dunavski prilaz 2") == ("Dunavski prilaz", "2")
    assert split_street("Ulica kralja Zvonimira 17A") == ("Ulica kralja Zvonimira", "17A")
    assert split_street("Prizna bb") == ("Prizna", None)
    assert split_street("Bartola Kašića 3/1") == ("Bartola Kašića", "3/1")


def test_iso_date_oba_oblika():
    assert iso_date("2015-02-23T00:00:00") == "2015-02-23"
    assert iso_date("2/23/2015 12:00:00 AM") == "2015-02-23"
    assert iso_date(None) is None


def test_pick_president_predsjednik_prije_ovlastenog_i_nikad_likvidator():
    osobe = [
        {"ime": "MARIJAN", "prezime": "REZNEKI", "funkcija": "LIKVIDATOR", "svojstvo": None},
        {"ime": "ANA", "prezime": "HORVAT", "funkcija": "OSOBA OVLAŠTENA ZA ZASTUPANJE", "svojstvo": "TAJNIK"},
        {"ime": "IVO", "prezime": "IVIĆ", "funkcija": "OSOBA OVLAŠTENA ZA ZASTUPANJE", "svojstvo": "PREDSJEDNIK"},
    ]
    assert pick_president(osobe) == ("Ivo Ivić", "Predsjednik")
    assert pick_president(osobe[:1]) == (None, None)
