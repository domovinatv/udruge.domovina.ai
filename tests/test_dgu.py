"""Geokoder — parsiranje broja i sličnost naziva ulice.

Mrežni dio se ne testira; ovdje su čiste funkcije na kojima je geokoder
padao. Svaki primjer je stvarna adresa iz MZO popisa.
"""
from src import dgu


def test_split_number_odbacuje_podbroj_iza_crte():
    """„Bartola Kašića 3/1" je stan 1 u kući 3 — bez rezanja postane broj 31."""
    assert dgu._split_number("3/1") == (3, None)
    assert dgu._split_number("20/3") == (20, None)


def test_split_number_slovo_je_verzal():
    """RPJ drži „37B", ne „37b" — upit s malim slovom vraća nula."""
    assert dgu._split_number("37b") == (37, "B")
    assert dgu._split_number("181A") == (181, "A")
    # Slovo iza crte je ULAZ, ne stan.
    assert dgu._split_number("7/A") == (7, "A")
    assert dgu._split_number("90") == (90, None)
    assert dgu._split_number("bb") == (None, None)


def test_keyword_cuva_dijakritiku():
    """`ILIKE '%Klaiceva%'` ne pogađa „Klaićeva" — ključ mora ostati s dijakritikom."""
    assert dgu.keyword("KLAIĆEVA") == "KLAIĆ"
    assert dgu.keyword("STJEPANA MIHALIĆA") == "MIHALIĆ"
    # Generičke riječi nisu ključ.
    assert dgu.keyword("IVANA PERKOVCA") == "PERKOVC"


def test_street_similarity_prezivi_kracenje():
    """RPJ krati duge nazive; `token_set_ratio` na tome daje 65."""
    assert dgu.street_similarity("TRG HRVATSKE BRATSKE ZAJEDNICE",
                                 "Trg Hrv. brat. zaj.") == 100.0
    assert dgu.street_similarity("DON MIHOVILA PAVLINOVIĆA",
                                 "Don M. Pavlinovića") == 100.0
    assert dgu.street_similarity("ŠKOLSKA", "Školska") == 100.0


def test_street_similarity_ne_lazira_slicnost():
    """„Splitska" i „Pulska" ne smiju biti sličnije nego što jesu."""
    assert dgu.street_similarity("SPLITSKA", "Pulska") < 80
