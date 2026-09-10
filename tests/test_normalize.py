from src.normalize import norm_text, slugify, strip_diacritics, title_case_hr


def test_strip_diacritics_djordje():
    assert strip_diacritics("Đurđevac Čšž") == "Durdevac Csz"


def test_slug_stabilan_i_s_sufiksom():
    assert slugify("UDRUGA MLADIH", "Sinj", suffix="1234") == "udruga-mladih-sinj-1234"
    assert slugify("Udruga mladih Sinj", "Sinj", suffix="9") == "udruga-mladih-sinj-9"


def test_slug_dugacak_naziv_se_reze():
    s = slugify("A" * 300, "Zagreb", suffix="77")
    assert len(s) <= 125 and s.endswith("-77")


def test_norm_text():
    assert norm_text('KATOLIČKA UDRUGA "MOLITVA", ŽUPA SV. ANE') == "katolicka udruga molitva zupa sv ane"


def test_title_case_cuva_navodnike_i_kratice():
    assert title_case_hr('KATOLIČKA UDRUGA "MOLITVA"') == 'Katolička Udruga "Molitva"'
    assert title_case_hr("ŽUPA SV. ANE I FSR") == "Župa sv. Ane i FSR"


def test_title_case_ne_dira_mjesovita_slova():
    assert title_case_hr("Udruga Padre Pio") == "Udruga Padre Pio"
