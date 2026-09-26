"""
Sef Projesi - NET_mi / Karma_Mod ozelliklerinin dogrulamasi
============================================================

Soru: .NET bayragi eklenince model ".NET ise zararsiz" kestirmesini mi
ogreniyor? EMBER 2018'de .NET dosyalarin cogu zararsiz; guncel .NET
zararlilari bu kestirmeyle gozden kacabilir.

  A: 5 ozellik (mevcut model)   B: A + NET_mi + Karma_Mod
  1) EMBER 2018, 5 katli CV: genel ve .NET / .NET-disi alt kumelerde hata
  2) EMBER2024 .NET test (2024 sonu, egitimde hic gorulmedi): ayni modeller,
     rf_egit_gercek.py ile ayni 80/20 egitim bolmesi
  3) B'nin kacirdigi guncel .NET zararlilarinin aileleri

EMBER2024 zararli/zararsiz orani kasitli dengelenmis; buradaki oranlar
gercek dunyadaki yayginligi degil, modelin ayirt etme gucunu gosterir.
"""

import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split

from ember2024_net_cikar import cikti_yolu
from rf_egit_gercek import EMBER_ZARARLI_CSV, EMBER_ZARARSIZ_CSV, OZELLIKLER

EMBER2024_NET_CSV = cikti_yolu("test")
MODELLER = {"A (5 ozellik)": OZELLIKLER,
            "B (+NET_mi, Karma_Mod)": OZELLIKLER + ["NET_mi", "Karma_Mod"]}


def yeni_model():
    return RandomForestClassifier(n_estimators=100, random_state=42)


def hata_ozeti(y, p, maske=None):
    if maske is not None:
        y, p = y[maske], p[maske]
    tahmin = p > 0.5
    return {
        "n": len(y),
        "zararli %": round(100 * y.mean(), 1),
        "dogruluk %": round(100 * (tahmin == y).mean(), 2),
        "yanlis alarm %": round(100 * tahmin[y == 0].mean(), 2) if (y == 0).any() else None,
        "kacan zararli %": round(100 * (~tahmin[y == 1]).mean(), 2) if (y == 1).any() else None,
        "AUC": round(roc_auc_score(y, p), 4) if len(set(y)) == 2 else None,
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    ember = pd.concat([pd.read_csv(EMBER_ZARARLI_CSV), pd.read_csv(EMBER_ZARARSIZ_CSV)],
                      ignore_index=True)
    y = ember["Etiket"].to_numpy()
    net = ember["NET_mi"].to_numpy() == 1
    print(f"EMBER 2018 egitim verisi: {len(ember)} dosya | .NET: {net.sum()} "
          f"(bunlarin %{100 * y[net].mean():.1f}'i zararli) | .NET-disi: {(~net).sum()} "
          f"(%{100 * y[~net].mean():.1f} zararli)")

    # 1) EMBER 2018 CV
    oof = {ad: np.zeros(len(y)) for ad in MODELLER}
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    for kat, (tr, te) in enumerate(skf.split(ember, y), 1):
        for ad, kolonlar in MODELLER.items():
            m = yeni_model().fit(ember.iloc[tr][kolonlar], y[tr])
            oof[ad][te] = m.predict_proba(ember.iloc[te][kolonlar])[:, 1]
        print(f"  [CV {kat}/5] tamam")
    satirlar = {}
    for ad in MODELLER:
        for alt, maske in (("tum", None), (".NET", net), (".NET-disi", ~net)):
            satirlar[f"{ad} | {alt}"] = hata_ozeti(y, oof[ad], maske)
    print("\n=== 1) EMBER 2018, 5 katli CV ===")
    print(pd.DataFrame(satirlar).T.to_string())

    # 2) EMBER2024 .NET
    yeni = pd.read_csv(EMBER2024_NET_CSV, keep_default_na=False)
    y24 = yeni["Etiket"].to_numpy()
    idx_tr, _ = train_test_split(np.arange(len(y)), test_size=0.2, stratify=y, random_state=42)
    p24 = {}
    for ad, kolonlar in MODELLER.items():
        m = yeni_model().fit(ember.iloc[idx_tr][kolonlar], y[idx_tr])
        p24[ad] = m.predict_proba(yeni[kolonlar])[:, 1]
    print(f"\n=== 2) EMBER2024 .NET test ({len(yeni)} dosya, Eylul-Aralik 2024) ===")
    print(f"NET_mi=1 olan: %{100 * yeni.NET_mi.mean():.2f} | Karma_Mod=1: zararlilarda "
          f"%{100 * yeni.Karma_Mod[y24 == 1].mean():.2f}, zararsizlarda "
          f"%{100 * yeni.Karma_Mod[y24 == 0].mean():.2f}")
    print(pd.DataFrame({ad: hata_ozeti(y24, p24[ad]) for ad in MODELLER}).T.to_string())
    print("Zararli olasiliginin medyani (gercek zararlilar / gercek zararsizlar):")
    for ad in MODELLER:
        print(f"  {ad}: {np.median(p24[ad][y24 == 1]):.2f} / {np.median(p24[ad][y24 == 0]):.2f}")

    # 3) B'nin kacirdigi zararlilarin aileleri
    b = list(MODELLER)[1]
    kacan = yeni[(y24 == 1) & (p24[b] <= 0.5)]
    tum_zararli = yeni[y24 == 1]
    print(f"\n=== 3) {b} modelinin kacirdigi {len(kacan)} guncel .NET zararlisi: en sik 10 aile ===")
    aile = pd.DataFrame({"kacan": kacan.Aile.replace("", "(bilinmiyor)").value_counts(),
                         "toplam": tum_zararli.Aile.replace("", "(bilinmiyor)").value_counts()})
    aile["kacma %"] = (100 * aile.kacan / aile.toplam).round(1)
    print(aile.sort_values("kacan", ascending=False).head(10).to_string())
