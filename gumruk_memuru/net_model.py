"""
Sef Projesi - .NET uzman modeli (EMBER2024) ve ablasyon
============================================================

Iki modelli mimari: NET_mi=1 dosyalar EMBER2024 .NET ile egitilen bu modele,
digerleri EMBER 2018 ile egitilen ana modele gider. Her modelde iki sinif
ayni kaynaktan gelir (Kritik Kural 2); .NET ve .NET-disi kaynaklar tek
modelde karistirilmaz (string_counts EMBER 2018'de yok).

Ablasyon (test: EMBER2024 .NET son 12 hafta, egitimde hic gorulmedi):
  M0 : mevcut ana model (EMBER 2018, 5 ozellik)          -> referans
  M1 : EMBER2024 .NET egitim, temel ozellikler           -> verinin etkisi
  M2 : M1 + dizge ozellikleri, sinifa gore dengeli       -> dizgelerin etkisi
  M2d: M2 + DLL_mi, her dosya tipinin ICINDE dengeli     -> ONERILEN
EMBER2024 .NET'te zararsizlarin ~%90'i DLL, zararlilarin ~%90'i EXE; M2 bunu
"EXE ise zararli" kestirmesi olarak ogreniyor (EXE yanlis alarmi ~%26).
M2d her tip icin %50 onsel varsayar; uretimde esik aninda tipe ozel onselle
duzeltilmeli (CLAUDE.md, ".NET Uzman Modeli").

Kullanim: once `python ember2024_net_cikar.py train` ve `... test`.
"""

import sys
import time

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from dizge_ozellikleri import DIZGE_SUTUNLARI
from ember2024_net_cikar import cikti_yolu
from net_dogrulama import hata_ozeti
from rf_egit_gercek import EMBER_ZARARLI_CSV, EMBER_ZARARSIZ_CSV, OZELLIKLER

EGITIM_ORNEK = 100_000   # 520K'nin alt ornegi; tek cekirdek, laptopu isitmamak icin
TEMEL = OZELLIKLER + ["Karma_Mod"]   # NET_mi bu veride hep 1, bilgi tasimaz
DIZGELI = TEMEL + DIZGE_SUTUNLARI
DIZGELI_TIPLI = DIZGELI + ["DLL_mi"]


def rf():
    return RandomForestClassifier(n_estimators=100, random_state=42)


def sinif_dengeli(df):
    return df.groupby("Etiket", group_keys=False).sample(n=EGITIM_ORNEK // 2, random_state=42)


def tip_ici_dengeli(df):
    return df.groupby(["DLL_mi", "Etiket"], group_keys=False).sample(n=EGITIM_ORNEK // 4, random_state=42)


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    t0 = time.monotonic()
    egitim = pd.read_csv(cikti_yolu("train"), keep_default_na=False)
    test = pd.read_csv(cikti_yolu("test"), keep_default_na=False)
    print(f"[*] yuklendi: egitim {len(egitim)}, test {len(test)} ({time.monotonic() - t0:.0f} sn) | "
          f"NET_mi=1 orani egitim %{100 * egitim.NET_mi.mean():.2f}, test %{100 * test.NET_mi.mean():.2f}")
    for ad, d in (("egitim", egitim), ("test", test)):
        print(f"    {ad} DLL orani: zararsiz %{100 * d[d.Etiket == 0].DLL_mi.mean():.1f}, "
              f"zararli %{100 * d[d.Etiket == 1].DLL_mi.mean():.1f}")

    ember = pd.concat([pd.read_csv(EMBER_ZARARLI_CSV), pd.read_csv(EMBER_ZARARSIZ_CSV)], ignore_index=True)
    e_tr, _ = train_test_split(ember, test_size=0.2, stratify=ember["Etiket"], random_state=42)
    sd, td = sinif_dengeli(egitim), tip_ici_dengeli(egitim)

    tanimlar = {
        "M0 ana model (EMBER 2018)": (e_tr, OZELLIKLER),
        "M1 EMBER2024, temel": (sd, TEMEL),
        "M2 + dizge": (sd, DIZGELI),
        "M2d + dizge, tip-ici dengeli": (td, DIZGELI_TIPLI),
    }
    olasilik, modeller = {}, {}
    for i, (ad, (X, kolonlar)) in enumerate(tanimlar.items(), 1):
        t = time.monotonic()
        modeller[ad] = rf().fit(X[kolonlar], X["Etiket"])
        olasilik[ad] = modeller[ad].predict_proba(test[kolonlar])[:, 1]
        print(f"  [{i}/{len(tanimlar)}] {ad}: {len(kolonlar)} ozellik, {time.monotonic() - t:.0f} sn")

    y = test["Etiket"].to_numpy()
    dll = test["DLL_mi"].to_numpy() == 1
    satirlar = {f"{ad} | {alt}": hata_ozeti(y, p, maske)
                for ad, p in olasilik.items()
                for alt, maske in (("tum", None), ("EXE", ~dll), ("DLL", dll))}
    print(f"\n=== EMBER2024 .NET test ({len(test)} dosya, son 12 hafta) ===")
    print(pd.DataFrame(satirlar).T.to_string())

    print("\n=== Aile bazinda kacma orani % (en sik 12 zararli aile) ===")
    zararli = test[y == 1]
    aile_adi = zararli.Aile.replace("", "(bilinmiyor)")
    aileler = aile_adi.value_counts().head(12)
    tablo = pd.DataFrame({"test'te n": aileler})
    for ad, p in olasilik.items():
        kacti = pd.Series(p[y == 1] <= 0.5, index=zararli.index)
        tablo[ad.split()[0]] = [round(100 * kacti[aile_adi == a].mean(), 1) for a in aileler.index]
    print(tablo.to_string())

    onerilen = list(modeller)[-1]
    print(f"\n=== {onerilen.split()[0]}: en onemli 15 ozellik ===")
    print(pd.Series(modeller[onerilen].feature_importances_, index=DIZGELI_TIPLI)
          .sort_values(ascending=False).head(15).round(4).to_string())
    print(f"\n[+] toplam sure {time.monotonic() - t0:.0f} sn")
