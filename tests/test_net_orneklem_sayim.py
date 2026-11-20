"""
sonuclar/10/net_orneklem_sayim.py - sahte kucuk veriyle.

net_model.EGITIM_ORNEK testte 8'e indirilir (M2: sinif basina 4, M2d: hucre basina 2 satir); betik
orneklemleri net_model'in fonksiyonlariyla kurdugu icin bu deger oraya da gecer. Beklenen sayilar
rastgele cekimden BAGIMSIZ kurulur: ya hucre tam orneklem boyutunda (hepsi secilir) ya da her satir
essiz (essiz == satir). Gercek veri ve egitim gerekmez.
"""

import csv
import hashlib
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "gumruk_memuru", "sonuclar", "10"))
import net_model  # noqa: E402
import net_orneklem_sayim as nos  # noqa: E402

HUCRELER = [(0, 0), (0, 1), (1, 0), (1, 1)]          # (DLL_mi, Etiket)


@pytest.fixture
def kucuk(monkeypatch):
    monkeypatch.setattr(net_model, "EGITIM_ORNEK", 8)


def veri(hucre_satir, kopya):
    """Her hucrede hucre_satir satir; her Dosya_Adi `kopya` kez (EMBER2024 .NET'te 2)."""
    satirlar = []
    for dll, etiket in HUCRELER:
        for i in range(hucre_satir):
            satirlar.append({"Dosya_Adi": f"d{dll}e{etiket}_{i // kopya:04d}", "Etiket": etiket,
                             "DLL_mi": dll, "Hafta": i % 52, "Boyut_Bayt": 1000 + i})
    return pd.DataFrame(satirlar)


def satir_bul(satirlar, orneklem, hucre):
    return next(s for s in satirlar if s["orneklem"] == orneklem and s["hucre"] == hucre)


def test_hucre_tam_dolu_ciftli(kucuk):
    """M2d hucre basina 2 satir ister; hucrede tam 2 satir = ayni dosyanin iki kopyasi -> essiz 1."""
    df = veri(hucre_satir=2, kopya=2)
    m2d = nos.say("M2d", net_model.tip_ici_dengeli(df), df)
    assert satir_bul(m2d, "M2d", "toplam") == {"orneklem": "M2d", "hucre": "toplam", "satir": 8,
                                               "essiz": 4, "havuz_satir": 8, "havuz_essiz": 4}
    for dll, etiket in HUCRELER:
        s = satir_bul(m2d, "M2d", f"DLL_mi={dll} Etiket={etiket}")
        assert (s["satir"], s["essiz"], s["havuz_satir"], s["havuz_essiz"]) == (2, 1, 2, 1)


def test_tum_satirlar_essiz(kucuk):
    """Kopya yoksa her orneklemde essiz == satir; boyutlar EGITIM_ORNEK'ten gelir (M2 8, M2d 8)."""
    df = veri(hucre_satir=10, kopya=1)
    for ad, fonk, beklenen in (("M2", net_model.sinif_dengeli, 8), ("M2d", net_model.tip_ici_dengeli, 8)):
        toplam = nos.say(ad, fonk(df), df)[0]
        assert toplam["satir"] == toplam["essiz"] == beklenen
    m2 = nos.say("M2", net_model.sinif_dengeli(df), df)
    assert [satir_bul(m2, "M2", f"Etiket={e}")["satir"] for e in (0, 1)] == [4, 4]


def test_sayim_dogrudan_hesapla_ayni(kucuk):
    """Rastgele kopyali veride betigin sayilari, orneklem uzerinde dogrudan hesapla ayni."""
    df = veri(hucre_satir=12, kopya=2)
    orn = net_model.tip_ici_dengeli(df)
    s = nos.say("M2d", orn, df)
    assert satir_bul(s, "M2d", "toplam")["essiz"] == orn.Dosya_Adi.nunique()
    for (dll, etiket), g in orn.groupby(["DLL_mi", "Etiket"]):
        h = satir_bul(s, "M2d", f"DLL_mi={dll} Etiket={etiket}")
        assert (h["satir"], h["essiz"]) == (len(g), g.Dosya_Adi.nunique())
    assert sum(k * n for k, n in nos.kopya_dagilimi(orn).items()) == len(orn)


def test_net_model_fonksiyonlarini_cagirir(kucuk, monkeypatch, tmp_path):
    """Betik orneklemi kendisi kurmaz: net_model.sinif_dengeli / tip_ici_dengeli cagrilir (kopya yok)."""
    cagri = []
    for ad in ("sinif_dengeli", "tip_ici_dengeli"):
        asil = getattr(net_model, ad)
        monkeypatch.setattr(net_model, ad, lambda d, _a=asil, _ad=ad: (cagri.append(_ad), _a(d))[1])
    girdi = tmp_path / "girdi.csv"
    veri(hucre_satir=6, kopya=2).to_csv(girdi, index=False)
    assert nos.main(["--girdi", str(girdi), "--cikti-klasoru", str(tmp_path / "c")]) == 0
    assert cagri == ["sinif_dengeli", "tip_ici_dengeli"]


def test_uctan_uca_cikti_ve_yan_etki_yok(kucuk, tmp_path):
    girdi = tmp_path / "girdi.csv"
    veri(hucre_satir=6, kopya=2).to_csv(girdi, index=False)
    once = hashlib.sha256(girdi.read_bytes()).hexdigest()
    cikti = tmp_path / "cikti"
    assert nos.main(["--girdi", str(girdi), "--cikti-klasoru", str(cikti)]) == 0
    assert hashlib.sha256(girdi.read_bytes()).hexdigest() == once            # girdi degismedi
    assert sorted(os.listdir(cikti)) == [nos.CSV_ADI, nos.LOG_ADI]          # model / baska dosya yok
    log = (cikti / nos.LOG_ADI).read_text(encoding="utf-8")
    assert f"sha256 {once}" in log and str(tmp_path) not in log            # ozet var, yerel yol yok
    assert "=== M2 " in log and "=== M2d " in log and "model yazilmadi" in log
    with open(cikti / nos.CSV_ADI, encoding="utf-8", newline="") as f:
        satirlar = list(csv.DictReader(f))
    assert list(satirlar[0]) == nos.CSV_KOLONLARI
    assert len(satirlar) == 2 * (1 + 2 + 4)                                 # toplam + 2 Etiket + 4 hucre
    toplam_m2d = satir_bul(satirlar, "M2d", "toplam")
    assert (toplam_m2d["satir"], toplam_m2d["havuz_satir"], toplam_m2d["havuz_essiz"]) == ("8", "24", "12")


def test_ayni_girdi_ayni_orneklem(kucuk):
    """Tohum net_model'de sabit: iki kez kurulan orneklemin sira ozeti ayni."""
    df = veri(hucre_satir=20, kopya=2)
    assert nos.sira_ozeti(net_model.tip_ici_dengeli(df)) == nos.sira_ozeti(net_model.tip_ici_dengeli(df))


def test_girdi_yoksa_hata(tmp_path):
    assert nos.main(["--girdi", str(tmp_path / "yok.csv"), "--cikti-klasoru", str(tmp_path / "c")]) == 1
    assert "girdi yok" in (tmp_path / "c" / nos.LOG_ADI).read_text(encoding="utf-8")


def test_eksik_kolon_hata(tmp_path):
    girdi = tmp_path / "g.csv"
    pd.DataFrame({"Dosya_Adi": ["a"], "Etiket": [0]}).to_csv(girdi, index=False)
    assert nos.main(["--girdi", str(girdi), "--cikti-klasoru", str(tmp_path / "c")]) == 1
    assert "DLL_mi" in (tmp_path / "c" / nos.LOG_ADI).read_text(encoding="utf-8")


def test_celiskili_sha_sayilir():
    df = pd.DataFrame({"Dosya_Adi": ["a", "a", "b", "b"], "Etiket": [0, 1, 0, 0], "DLL_mi": [0, 0, 1, 1]})
    assert nos.celiskili_sha(df) == 1
