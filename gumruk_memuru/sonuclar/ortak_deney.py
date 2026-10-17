"""
2a / 2b / 2c ortak kodu: veri yukleme, orneklem, olcum. Tanimlar karar_olcutleri.md ile ayni.

Ayni kod uc adimda kullanilir ki hicbir adim "kendi" kacan zararli tanimini yapmasin.
Satir sirasi 9 Ekim'le ayni (Win32 sonra Win64, haftalar sirali): ayni tohum ayni orneklemi
verir; kontrol_9ekim() bunu bir hucrede dogrular.
"""

import csv
import os
import sys
import time

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

GUMRUK = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, GUMRUK)
from dizge_ozellikleri import DIZGE_SUTUNLARI  # noqa: E402
from net_dogrulama import hata_ozeti  # noqa: E402
from rf_egit_gercek import OZELLIKLER  # noqa: E402
from sef_ayarlar import DOGRULAMA_DZ80_CSV, EMBER2024_KLASORU, EMBER2024_PARQUET_KLASORU  # noqa: E402

TOHUMLAR = [42, 1, 2, 3, 4]
E2_KOLON = OZELLIKLER + DIZGE_SUTUNLARI          # 85
E3_KOLON = E2_KOLON + ["DLL_mi"]                 # 86
SAYISAL = E3_KOLON + ["NET_mi", "Etiket", "Hafta"]
YEREL_TAHMIN_KLASORU = os.path.join(EMBER2024_KLASORU, "sonuc", "yerel_tahmin")   # repoda yok
FPR_HEDEF = 0.01
LGBM_AYAR = dict(deterministic=True, force_row_wise=True, verbose=-1)   # gerisi varsayilan


def yukle(adlar):
    d = pd.concat([pd.read_parquet(os.path.join(EMBER2024_PARQUET_KLASORU, f"{a}.parquet"),
                                   columns=SAYISAL + ["Aile", "Tur"]) for a in adlar], ignore_index=True)
    d[SAYISAL] = d[SAYISAL].astype("float32")
    d["Etiket"] = d["Etiket"].astype(int)
    return d


def veri():
    egitim = yukle(["Win32_train", "Win64_train"])
    test = yukle(["Win32_test", "Win64_test"])
    yerel = pd.read_csv(DOGRULAMA_DZ80_CSV)
    if egitim.Hafta.max() >= test.Hafta.min():
        sys.exit("Hata: egitim ve test haftalari ortusuyor (Kural 6).")
    return egitim, test, yerel


# --- Orneklem (9 Ekim kurali) ---
def sinif_dengeli(df, n, tohum):
    return df.groupby("Etiket", group_keys=False).sample(n=n // 2, random_state=tohum)


def tip_ici_dengeli(df, n, tohum):
    return df.groupby(["DLL_mi", "Etiket"], group_keys=False).sample(n=n // 4, random_state=tohum)


ADAYLAR = {"E2": (sinif_dengeli, E2_KOLON), "E3": (tip_ici_dengeli, E3_KOLON)}


def tamami(df, aday):
    """Yerine koymadan kurulabilen en buyuk dengeli boyut."""
    if aday == "E2":
        return 2 * int(df.Etiket.value_counts().min())
    return 4 * int(df.groupby(["DLL_mi", "Etiket"]).size().min())


# --- Olcum (karar_olcutleri.md, Tanimlar) ---
def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    m = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    o = (p + z * z / (2 * n)) / (1 + z * z / n)
    return 100 * max(0, o - m), 100 * min(1, o + m)


def tur_esikleri(p, df):
    """Her tur icin, df'deki o turun ZARARSIZLARININ %1'inin astigi esik (karar_olcutleri.md)."""
    y, esik = df.Etiket.to_numpy(), {}
    for tur, deger in (("EXE", 0), ("DLL", 1)):
        z = p[(df.DLL_mi.to_numpy() == deger) & (y == 0)]
        esik[tur] = float(np.quantile(z, 1 - FPR_HEDEF, method="higher"))
    return esik


def olc(p_test, test, p_yerel, yerel, esik=None):
    """Bir model+tohum icin tum olculer (tek satir) ve tur esikleri.
    esik=None: esik TESTTEN secilir (2c'deki ROC calisma noktasi). esik verilirse (dogrulama
    diliminden secilmis) test o SABIT esikle bir kez olculur."""
    y = test.Etiket.to_numpy()
    satir = {f"genel_{k}": v for k, v in hata_ozeti(y, p_test).items() if k != "n"}
    esik = dict(esik) if esik is not None else tur_esikleri(p_test, test)
    for tur, deger in (("EXE", 0), ("DLL", 1)):
        m = test.DLL_mi.to_numpy() == deger
        zararsiz, zararli = p_test[m & (y == 0)], p_test[m & (y == 1)]
        tau = esik[tur]
        satir[f"{tur}_dogruluk_%"] = round(100 * ((p_test[m] > 0.5) == (y[m] == 1)).mean(), 3)
        satir[f"{tur}_AUC"] = round(roc_auc_score(y[m], p_test[m]), 5)
        satir[f"{tur}_esik@1"] = tau
        satir[f"{tur}_test_YA_%@1"] = round(100 * (zararsiz > tau).mean(), 3)
        satir[f"{tur}_kacan_%@1"] = round(100 * (zararli <= tau).mean(), 3)
        my = yerel.DLL_mi.to_numpy() == deger
        k, n = int((p_yerel[my] > tau).sum()), int(my.sum())
        alt, ust = wilson(k, n)
        satir[f"{tur}_yerel_YA_%@1"] = round(100 * k / n, 3)
        satir[f"{tur}_yerel_YA_alt"], satir[f"{tur}_yerel_YA_ust"] = round(alt, 3), round(ust, 3)
        satir[f"{tur}_yerel_YA_k"], satir[f"{tur}_yerel_n"] = k, n
        satir[f"{tur}_yerel_YA_%@0.5"] = round(100 * (p_yerel[my] > 0.5).mean(), 3)
    return satir, esik


def yerel_tahmin_kaydet(anahtar, p_yerel, esik):
    os.makedirs(YEREL_TAHMIN_KLASORU, exist_ok=True)
    np.savez(os.path.join(YEREL_TAHMIN_KLASORU, f"{anahtar}.npz"), p=p_yerel, **{f"esik_{k}": v for k, v in esik.items()})


def model_uret(algoritma, tohum, cekirdek):
    if algoritma == "LGBM":
        from lightgbm import LGBMClassifier
        return LGBMClassifier(random_state=tohum, n_jobs=cekirdek, **LGBM_AYAR)
    from sklearn.ensemble import RandomForestClassifier
    return RandomForestClassifier(n_estimators=100, random_state=tohum, n_jobs=cekirdek)


def hucre_kos(algoritma, aday, boyut, tohum, egitim, test, yerel, cekirdek=8, dogrulama=None,
              onek="", model_dondur=False):
    """Tek deney hucresi: orneklem -> egitim -> olcum; yerel tahminleri diske yazar.
    dogrulama verilirse esik ORADAN secilir ve test o sabit esikle bir kez olculur."""
    ornekle, kolonlar = ADAYLAR[aday]
    t = time.monotonic()
    ornek = ornekle(egitim, boyut, tohum)
    model = model_uret(algoritma, tohum, cekirdek).fit(ornek[kolonlar], ornek.Etiket)
    ek = {}
    esik = None
    if dogrulama is not None:
        p_dog = model.predict_proba(dogrulama[kolonlar])[:, 1]
        esik = tur_esikleri(p_dog, dogrulama)
        y_dog = dogrulama.Etiket.to_numpy()
        for tur, deger in (("EXE", 0), ("DLL", 1)):
            m = dogrulama.DLL_mi.to_numpy() == deger
            ek[f"{tur}_dogrulama_YA_%"] = round(100 * (p_dog[m & (y_dog == 0)] > esik[tur]).mean(), 3)
            ek[f"{tur}_dogrulama_kacan_%"] = round(100 * (p_dog[m & (y_dog == 1)] <= esik[tur]).mean(), 3)
    p_test = model.predict_proba(test[kolonlar])[:, 1]
    p_yerel = model.predict_proba(yerel[kolonlar])[:, 1]
    satir, esik = olc(p_test, test, p_yerel, yerel, esik)
    anahtar = f"{onek}{algoritma}_{aday}_{boyut}_{tohum}"
    yerel_tahmin_kaydet(anahtar, p_yerel, esik)
    sonuc = {"hucre": anahtar, "algoritma": algoritma, "aday": aday, "boyut": boyut, "tohum": tohum,
             "egitim_satir": len(ornek), "sure_sn": round(time.monotonic() - t, 1), **satir, **ek}
    return (sonuc, model) if model_dondur else sonuc


# --- Sonuc CSV'si: hucre basina satir, --devam ---
class SonucCSV:
    def __init__(self, yol):
        self.yol = yol
        self.biten = set()
        if os.path.exists(yol):
            with open(yol, newline="", encoding="utf-8") as f:
                self.biten = {s["hucre"] for s in csv.DictReader(f)}

    def ekle(self, satir):
        yeni = not os.path.exists(self.yol)
        with open(self.yol, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(satir))
            if yeni:
                w.writeheader()
            w.writerow(satir)
        self.biten.add(satir["hucre"])


def ilerleme(i, toplam, t0, ek=""):
    gecen = time.monotonic() - t0
    kalan = gecen / i * (toplam - i) if i else 0
    print(f"  [{i}/{toplam}] %{100 * i / toplam:5.1f} | gecen {gecen / 60:.1f} dk, kalan ~{kalan / 60:.1f} dk {ek}")
