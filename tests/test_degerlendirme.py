"""
Degerlendirme duzenegi testleri (gumruk_memuru/degerlendirme.py).
Sentetik veri: gercek EMBER bu ortamda yok; testler MANTIGI dogrular
(ayrim, sizinti yakalama, esik/TPR hesabi), model basarisini degil.
"""

import numpy as np
import pandas as pd
import pytest

import degerlendirme as dg
from rf_egit_gercek import OZELLIKLER


def sahte(n_ay, ay_basi, aileler, n=60, tohum=0):
    """Her ay n zararsiz + n zararli; zararlilar OZELLIKLER'de ayrisiyor."""
    rng = np.random.default_rng(tohum)
    satirlar = []
    for ay in range(ay_basi, ay_basi + n_ay):
        for etiket in (0, 1):
            x = rng.normal(loc=2.0 * etiket, scale=1.0, size=(n, len(OZELLIKLER)))
            d = pd.DataFrame(x, columns=OZELLIKLER)
            d["Etiket"] = etiket
            d["Ay"] = f"2018-{ay:02d}"
            d["Aile"] = rng.choice(aileler, n) if etiket else ""
            d["NET_mi"] = rng.integers(0, 2, n)
            d["DLL_mi"] = rng.integers(0, 2, n)
            d["Dosya_Adi"] = [f"ember_{ay}_{etiket}_{tohum}_{i}.exe" for i in range(n)]
            satirlar.append(d)
    return pd.concat(satirlar, ignore_index=True)


@pytest.fixture
def veri():
    egitim = sahte(10, 1, ["a", "b", "c"], tohum=1)
    test = sahte(2, 11, ["a", "b", "yeni1", "yeni2"], tohum=2)
    return egitim, test


# --- bolme ---

def test_zaman_bol_donem_siniri_ve_sira(veri):
    egitim, _ = veri
    fit, dog = dg.zaman_bol(egitim, "Ay")
    assert set(fit.Ay) | set(dog.Ay) == set(egitim.Ay) and not set(fit.Ay) & set(dog.Ay)
    assert max(fit.Ay) < min(dog.Ay) and len(set(dog.Ay)) == 2   # 10 donemin %20'si


def test_zaman_bol_kayit_payina_gore(veri):
    """Gercek EMBER 2018 yapisi: cok sayida eski ay, hepsi az ve sadece zararsiz.
    Donem sayisina gore bolme 2018'in tamamini dogrulamaya atip fit'i tek sinif
    birakiyordu; kayit payina gore dogrulama son ~%20 kayit olmali."""
    egitim, _ = veri
    eski = pd.concat([egitim[egitim.Etiket == 0].head(3).assign(Ay=f"20{y:02d}-06")
                      for y in range(6, 18)], ignore_index=True)   # 12 eski ay, 3'er zararsiz
    karma = pd.concat([eski, egitim], ignore_index=True)
    fit, dog = dg.zaman_bol(karma, "Ay")
    assert set(fit.Etiket) == {0, 1} and set(dog.Etiket) == {0, 1}
    assert {"2018-09", "2018-10"} <= set(dog.Ay) and min(dog.Ay) >= "2018-01"   # en yeni aylar
    assert 0.2 <= len(dog) / len(karma) <= 0.3                                   # en az %20


def test_zaman_bol_tek_sinifli_fit_reddedilir(veri):
    egitim, _ = veri
    egitim = egitim[(egitim.Ay >= "2018-09") | (egitim.Etiket == 0)]   # fit'te zararli yok
    with pytest.raises(dg.SizintiHatasi, match="tek sinif"):
        dg.zaman_bol(egitim, "Ay")


def test_zaman_bol_tek_donem_reddedilir(veri):
    with pytest.raises(dg.SizintiHatasi):
        dg.zaman_bol(veri[0][veri[0].Ay == "2018-01"], "Ay")


def test_donem_siralamasi_taninmayan_etiket_reddedilir():
    with pytest.raises(dg.SizintiHatasi):
        dg.donem_sirasi(pd.Series(["Ocak", "Subat"]))


def test_aile_ayrik_test(veri):
    _, test = veri
    t = dg.aile_ayrik_test(test, {"a", "b", "c"})
    zararli = t[t.Etiket == 1]
    assert set(zararli.Aile) <= {"yeni1", "yeni2"} and len(zararli) > 0
    assert (t.Etiket == 0).sum() == (test.Etiket == 0).sum()      # zararsizlar degismez


def test_aile_ayrik_bilinmeyen_aile_alinmaz(veri):
    _, test = veri
    test.loc[(test.Etiket == 1).idxmax(), "Aile"] = ""
    t = dg.aile_ayrik_test(test, {"a"})
    assert "" not in set(t[t.Etiket == 1].Aile)


# --- sizinti kontrolleri ---

def _kontrol(egitim, test, kolonlar=OZELLIKLER):
    fit, dog = dg.zaman_bol(egitim, "Ay")
    gorulen = set(fit.Aile) | set(dog.Aile)
    return dg.sizinti_kontrolleri(fit, dog, test, dg.aile_ayrik_test(test, gorulen), kolonlar, "Ay", "Ay")


def test_temiz_veri_gecer(veri):
    sonuc = _kontrol(*veri)
    assert {d for _, d, _ in sonuc} == {"gecti", "bilgi"}


def test_zaman_cakismasi_yakalanir(veri):
    egitim, test = veri
    test = test.assign(Ay="2018-05")                 # test egitimin ortasinda
    with pytest.raises(dg.SizintiHatasi, match="zaman|donemleri"):
        _kontrol(egitim, test)


def test_dosya_kimligi_cakismasi_yakalanir(veri):
    egitim, test = veri
    test = test.copy()
    test.loc[test.index[:3], "Dosya_Adi"] = egitim.Dosya_Adi.iloc[:3].to_numpy()
    with pytest.raises(dg.SizintiHatasi, match="Dosya_Adi"):
        _kontrol(egitim, test)


@pytest.mark.parametrize("sutun", ["Etiket", "Aile", "Ay", "Dosya_Adi"])
def test_etiket_ve_meta_ozellik_olamaz(veri, sutun):
    with pytest.raises(dg.SizintiHatasi, match="etiket/meta"):
        _kontrol(*veri, kolonlar=OZELLIKLER + [sutun])


def test_birebir_ayni_vektor_raporlanir(veri):
    egitim, test = veri
    test = test.copy()
    test.loc[test.index[:6], OZELLIKLER] = egitim[OZELLIKLER].iloc[:6].to_numpy()
    bilgi = [a for ad, d, a in _kontrol(egitim, test) if d == "bilgi"][0]
    assert "%2.5" in bilgi   # 6/240


# --- metrik ---

def test_esik_ve_tpr_elle_hesap():
    zararsiz_dog = np.arange(100) / 100          # 0.00 .. 0.99
    esik = dg.esik_sec(zararsiz_dog, 0.05)
    assert (zararsiz_dog > esik).mean() <= 0.05 and (zararsiz_dog > esik - 0.011).mean() > 0.05
    y = np.array([0] * 10 + [1] * 4)
    p = np.array([0.1] * 9 + [0.9] + [0.2, 0.95, 0.99, 0.5])
    fpr, tpr, nz, nm = dg.tpr_fpr(y, p, 0.6)
    assert (fpr, tpr, nz, nm) == (0.1, 0.5, 10, 4)


def test_tpr_fpr_bos_taraf_nan():
    fpr, tpr, *_ = dg.tpr_fpr(np.array([1, 1]), np.array([0.9, 0.1]), 0.5)
    assert np.isnan(fpr) and tpr == 0.5


def test_olc_alt_grup_ve_az_isareti(veri):
    _, test = veri
    p = np.where(test.Etiket == 1, 0.9, 0.1)
    satir = {s["grup"]: s for s in dg.olc(test, p, {0.01: 0.5, 0.001: 0.5})}
    assert {"tum", "PE (.NET disi)", ".NET", "EXE", "DLL"} <= set(satir)
    assert satir["tum"]["AUC"] == 1.0 and satir["tum"]["TPR@0.01"] == 1.0
    assert satir[".NET"]["az@0.001"]            # ~60 zararsiz * 0.001 < 10 -> guvenilmez


# --- uctan uca ---

def test_uctan_uca_rapor(veri):
    egitim, test = veri
    sonuc, kontroller, bilgi = dg.degerlendir(egitim, test, OZELLIKLER, egitim_ornek=200,
                                              tohumlar=(1, 2), log=lambda *_: None)
    assert {"RandomForest", "HistGradientBoosting"} <= set(sonuc.model)
    assert set(sonuc.test) == {"zaman", "zaman+aile"}
    rapor = dg.rapor_yaz(sonuc, kontroller, bilgi, OZELLIKLER, "temel")
    for parca in ("## Sızıntı kontrolleri", "Hedef FPR %1", "Hedef FPR %0.1", ".NET",
                  "PE (.NET disi)", "zaman+aile", "HistGradientBoosting", "†"):
        assert parca in rapor
    # sentetik veri kolay ayriliyor -> sizinti suphesi uyarisi calisiyor mu
    assert "UYARI" in rapor or sonuc[sonuc.grup == "tum"].AUC.mean() <= dg.SUPHELI_AUC


def test_ayni_egitim_ornegi_tum_modellerde(veri, monkeypatch):
    egitim, test = veri
    goruldu = {}

    class Sahte:
        def __init__(self, ad):
            self.ad = ad

        def fit(self, X, y):
            goruldu.setdefault(self.ad, []).append(tuple(X.index))
            self.m = dg.RandomForestClassifier(n_estimators=5, random_state=0).fit(X, y)
            return self

        def predict_proba(self, X):
            return self.m.predict_proba(X)

    monkeypatch.setattr(dg, "model_uretecleri",
                        lambda: {"A": lambda s: Sahte("A"), "B": lambda s: Sahte("B")})
    dg.degerlendir(egitim, test, OZELLIKLER, egitim_ornek=100, tohumlar=(1, 2), log=lambda *_: None)
    assert goruldu["A"] == goruldu["B"] and goruldu["A"][0] != goruldu["A"][1]


def test_esik_dogrulamadan_secilir_testten_degil(veri, monkeypatch):
    egitim, _ = veri
    test = sahte(3, 11, ["a", "yeni1"], tohum=3)          # 180 zararsiz; dogrulamada 120
    cagrilar = []
    gercek = dg.esik_sec
    monkeypatch.setattr(dg, "esik_sec", lambda p, f: cagrilar.append(len(p)) or gercek(p, f))
    dg.degerlendir(egitim, test, OZELLIKLER, egitim_ornek=100, tohumlar=(1,), log=lambda *_: None)
    assert cagrilar and set(cagrilar) == {120}            # test zararsiz sayisi (180) olsaydi sapardi
