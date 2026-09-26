"""
Sef Projesi - Native model icin DLL_mi ve EMBER 2018 dizge ozellikleri
============================================================

Soru 1: EMBER 2018'de zararsizlarin ~%23'u, zararlilarin ~%3'u DLL. EMBER2024
.NET'teki kestirme ("EXE ise zararli") burada da var mi? Mevcut 5 ozellikli
model DLL'leri tipten dolayi mi zararsiz buluyor?
Soru 2: EMBER 2018 JSON'undaki strings grubu (17 GB EMBER2024 Win32/Win64
indirmeden elde edilebilen tek dizge sinyali) native modele ne katar?

Olcum: EMBER 2018'in kendi zamansal bolmesi. Egitim Ocak-Ekim 2018'den
orneklem (ana modelle ayni boyut), test Kasim-Aralik 2018'in tamami
(200.000). Her varyant 5 tohumla; tum / EXE / DLL / .NET ayri (Kural 4).

On kosul: python ember2018_tam_cikar.py train  ve  ... test
"""

import sys
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from dizge_ozellikleri import EMBER2018_DIZGE_SUTUNLARI
from ember2018_tam_cikar import cikti_yolu
from net_dogrulama import hata_ozeti
from rf_egit_gercek import OZELLIKLER
from sef_ayarlar import EMBER_ZARARLI_CSV, EMBER_ZARARSIZ_CSV, MODEL_YOLU

EGITIM_ORNEK = 11_400    # ana modelin toplam boyutu (5700 + 5700)
TOHUMLAR = [42, 1, 2, 3, 4]
DIZGELI = OZELLIKLER + EMBER2018_DIZGE_SUTUNLARI


def sinif_dengeli(df, tohum):
    return df.groupby("Etiket", group_keys=False).sample(n=EGITIM_ORNEK // 2, random_state=tohum)


def tip_ici_dengeli(df, tohum):
    return df.groupby(["DLL_mi", "Etiket"], group_keys=False).sample(n=EGITIM_ORNEK // 4, random_state=tohum)


VARYANTLAR = {
    "V0 5 temel": (sinif_dengeli, OZELLIKLER),
    "V1 +DLL_mi": (sinif_dengeli, OZELLIKLER + ["DLL_mi"]),
    "V2 +dizge": (sinif_dengeli, DIZGELI),
    "V3 +dizge +DLL_mi": (sinif_dengeli, DIZGELI + ["DLL_mi"]),
    "V4 +dizge +DLL_mi, tip-ici": (tip_ici_dengeli, DIZGELI + ["DLL_mi"]),
}


def alt_gruplar(test):
    dll, net = test.DLL_mi.to_numpy() == 1, test.NET_mi.to_numpy() == 1
    return {"tum": None, "EXE": ~dll, "DLL": dll, ".NET": net}


def ozet_tablo(y, p, gruplar, onek):
    return {f"{onek} | {alt}": hata_ozeti(y, p, m) for alt, m in gruplar.items()}


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    t0 = time.monotonic()
    egitim = pd.read_csv(cikti_yolu("train"), keep_default_na=False)
    test = pd.read_csv(cikti_yolu("test"), keep_default_na=False)
    print(f"[*] egitim {len(egitim)} (Ocak-Ekim), test {len(test)} (Kasim-Aralik) | "
          f"{time.monotonic() - t0:.0f} sn")
    for ad, d in (("egitim", egitim), ("test", test)):
        print(f"    {ad} DLL orani: zararsiz %{100 * d[d.Etiket == 0].DLL_mi.mean():.1f}, "
              f"zararli %{100 * d[d.Etiket == 1].DLL_mi.mean():.1f} | "
              f".NET orani %{100 * d.NET_mi.mean():.1f}")

    # --- Referans: repodaki ana model (model.pkl). Egitim orneklemi EMBER
    # dosyalarinin alfabetik ilkinden (test_features) toplandi -> kendi
    # satirlari testten cikarilir.
    ana = joblib.load(MODEL_YOLU)
    ana_satirlar = set(pd.concat([pd.read_csv(EMBER_ZARARLI_CSV), pd.read_csv(EMBER_ZARARSIZ_CSV)]).Dosya_Adi)
    gorulmemis = test[~test.Dosya_Adi.isin(ana_satirlar)]
    print(f"\n[*] Ana modelin 11.400 egitim/test satirindan {len(test) - len(gorulmemis)} tanesi "
          f"EMBER 2018 test dosyasinda; ana model kalan {len(gorulmemis)} dosyada olculuyor.")
    p_ana = ana["model"].predict_proba(gorulmemis[ana["ozellikler"]])[:, 1]
    print(pd.DataFrame(ozet_tablo(gorulmemis.Etiket.to_numpy(), p_ana,
                                  alt_gruplar(gorulmemis), "ANA model.pkl")).T.to_string())

    # --- Varyantlar, 5 tohum ---
    y = test.Etiket.to_numpy()
    gruplar = alt_gruplar(test)
    kayitlar, onemler = [], {}
    for i, (ad, (ornekle, kolonlar)) in enumerate(VARYANTLAR.items(), 1):
        t = time.monotonic()
        for tohum in TOHUMLAR:
            ornek = ornekle(egitim, tohum)
            model = RandomForestClassifier(n_estimators=100, random_state=tohum).fit(ornek[kolonlar], ornek.Etiket)
            p = model.predict_proba(test[kolonlar])[:, 1]
            for alt, m in gruplar.items():
                kayitlar.append({"varyant": ad, "alt": alt, "tohum": tohum, **hata_ozeti(y, p, m)})
            if tohum == 42:
                onemler[ad] = pd.Series(model.feature_importances_, index=kolonlar)
        print(f"  [{i}/{len(VARYANTLAR)}] {ad}: {len(kolonlar)} ozellik, {time.monotonic() - t:.0f} sn")

    sonuc = pd.DataFrame(kayitlar)
    metrikler = ["dogruluk %", "yanlis alarm %", "kacan zararli %", "AUC"]
    ortalama = sonuc.groupby(["varyant", "alt"], sort=False)[metrikler].mean()
    aralik = sonuc.groupby(["varyant", "alt"], sort=False)[metrikler].agg(lambda s: s.max() - s.min())
    print(f"\n=== EMBER 2018 test (Kasim-Aralik, {len(test)} dosya): 5 tohum ortalamasi ===")
    print(ortalama.round(3).to_string())
    print("\n=== Tohumlar arasi fark (max - min): bundan kucuk farklar anlamsiz ===")
    print(aralik.groupby(level="alt", sort=False).max().round(3).to_string())

    for ad in ("V3 +dizge +DLL_mi", "V4 +dizge +DLL_mi, tip-ici"):
        print(f"\n=== {ad}: ozellik onemleri (tohum 42) ===")
        print(onemler[ad].sort_values(ascending=False).round(3).to_string())
    print(f"\n[+] toplam sure {time.monotonic() - t0:.0f} sn")
