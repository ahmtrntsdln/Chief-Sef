"""
Sef Projesi - EMBER2024 native (Win32 + Win64) model adaylari: dal model/ember2024-native
============================================================

Soru: Ana modeli (EMBER 2018, 5 ozellik) EMBER2024'e tasimak + thrember dizge
ozellikleri (string_counts) eklemek ne kazandirir, bedeli ne? (CLAUDE.md, Sonraki Adimlar 1)

Olcum (Kritik Kural 6): zamansal bolme. Egitim: EMBER2024 Win32/Win64 train (ilk 52 hafta)
alt orneklemi; test: Win32/Win64 test'in TAMAMI (son 12 hafta). Her aday 5 tohum.
Alt gruplar ayri (Kural 4): EXE, DLL, Win32, Win64, import'suz, .NET.
Dis dogrulama: bu makinedeki 5637 zararsiz PE (dogrulama_dizge80.py), EXE/DLL ayri, Wilson %95.

Adaylar:
  ANA  model.pkl (EMBER 2018, 5 temel ozellik) - referans
  E1   2024 verisi, 5 temel, sinif dengeli        -> kazancin ne kadari veriden?
  E2   + 80 dizge, sinif dengeli (DLL_mi yok)     -> DLL kestirmesi ne kadar? (2024'te zararsizlarin
                                                    ~%73'u, zararlilarin ~%6'si DLL)
  E3   + 80 dizge + DLL_mi, tip-ici dengeli       -> ADAY (M2d / V4 yontemi)

On kosul: ember2024_indir.py; ember2024_cikar.py Win32_train Win64_train Win32_test Win64_test;
dogrulama_dizge80.py.  Kullanim: python ember2024_native_dogrulama.py
"""

import glob
import json
import os
import sys
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from dizge_ozellikleri import DIZGE_SUTUNLARI
from ember2024_cikar import cikti_klasoru
from net_dogrulama import hata_ozeti
from rf_egit_gercek import OZELLIKLER
from sef_ayarlar import DOGRULAMA_DZ80_CSV, EMBER2024_KLASORU, MODEL_YOLU

EGITIM_ORNEK = 100_000   # .NET uzman modeliyle ayni boyut
TOHUMLAR = [42, 1, 2, 3, 4]
CEKIRDEK = 4             # laptop isinmasin (bkz. CLAUDE.md, Calisma Aliskanliklari); sonucu degistirmez
DIZGELI = OZELLIKLER + DIZGE_SUTUNLARI
SONUC_KLASORU = os.path.join(EMBER2024_KLASORU, "sonuc")
SAYISAL = OZELLIKLER + DIZGE_SUTUNLARI + ["DLL_mi", "NET_mi", "Etiket", "Hafta"]


def sinif_dengeli(df, tohum):
    return df.groupby("Etiket", group_keys=False).sample(n=EGITIM_ORNEK // 2, random_state=tohum)


def tip_ici_dengeli(df, tohum):
    return df.groupby(["DLL_mi", "Etiket"], group_keys=False).sample(n=EGITIM_ORNEK // 4, random_state=tohum)


ADAYLAR = {
    "E1 2024, 5 temel": (sinif_dengeli, OZELLIKLER),
    "E2 +dizge, sinif dengeli": (sinif_dengeli, DIZGELI),
    "E3 +dizge +DLL_mi, tip-ici (ADAY)": (tip_ici_dengeli, DIZGELI + ["DLL_mi"]),
}


def yukle(adlar):
    parcalar = []
    for ad in adlar:
        dosyalar = sorted(glob.glob(os.path.join(cikti_klasoru(ad), "*.csv")))
        if not dosyalar:
            sys.exit(f"Hata: '{cikti_klasoru(ad)}' bos (once ember2024_cikar.py {ad}).")
        for f in dosyalar:
            d = pd.read_csv(f, usecols=SAYISAL + ["Aile", "Tur"], keep_default_na=False,
                            dtype={k: "float32" for k in SAYISAL} | {"Aile": str, "Tur": str})
            parcalar.append(d)
    df = pd.concat(parcalar, ignore_index=True)
    df["Etiket"] = df["Etiket"].astype(int)
    return df


def alt_gruplar(df):
    dll = df.DLL_mi.to_numpy() == 1
    return {"tum": None, "EXE": ~dll, "DLL": dll, "Win32": df.Tur.to_numpy() == "Win32",
            "Win64": df.Tur.to_numpy() == "Win64", "import'suz": df.Toplam_API.to_numpy() == 0,
            ".NET": df.NET_mi.to_numpy() == 1}


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    m = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    o = (p + z * z / (2 * n)) / (1 + z * z / n)
    return 100 * p, 100 * max(0, o - m), 100 * min(1, o + m)


def yerel_yanlis_alarm(p, yerel):
    satir = {}
    for ad, m in {"tum": np.ones(len(yerel), bool), "EXE": yerel.DLL_mi.to_numpy() == 0, "DLL": yerel.DLL_mi.to_numpy() == 1}.items():
        k, n = int((p[m] > 0.5).sum()), int(m.sum())
        oran, alt, ust = wilson(k, n)
        satir[ad] = f"%{oran:.1f} [{alt:.1f}-{ust:.1f}] ({k}/{n})"
    return satir


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    os.makedirs(SONUC_KLASORU, exist_ok=True)
    t0 = time.monotonic()
    egitim = yukle(["Win32_train", "Win64_train"])
    test = yukle(["Win32_test", "Win64_test"])
    yerel = pd.read_csv(DOGRULAMA_DZ80_CSV)
    print(f"[*] egitim {len(egitim)} (ilk 52 hafta), test {len(test)} (son 12 hafta), yerel zararsiz {len(yerel)} | "
          f"{time.monotonic() - t0:.0f} sn")
    print(f"    haftalar: egitim {int(egitim.Hafta.min())}-{int(egitim.Hafta.max())}, test {int(test.Hafta.min())}-{int(test.Hafta.max())}")
    if egitim.Hafta.max() >= test.Hafta.min():
        sys.exit("Hata: egitim ve test haftalari ortusuyor (Kural 6).")
    for ad, d in (("egitim", egitim), ("test", test)):
        print(f"    {ad}: zararli %{100 * d.Etiket.mean():.1f} | DLL zararsiz %{100 * d[d.Etiket == 0].DLL_mi.mean():.1f}, "
              f"zararli %{100 * d[d.Etiket == 1].DLL_mi.mean():.1f} | import'suz %{100 * (d.Toplam_API == 0).mean():.1f} | "
              f".NET %{100 * d.NET_mi.mean():.2f}")

    y = test.Etiket.to_numpy()
    gruplar = alt_gruplar(test)
    kayitlar, onemler, yerel_tablo, aile_tablo = [], {}, {}, {}

    # --- Referans: ana model (EMBER 2018) ---
    ana = joblib.load(MODEL_YOLU)
    p = ana["model"].predict_proba(test[ana["ozellikler"]])[:, 1]
    for alt, m in gruplar.items():
        kayitlar.append({"aday": "ANA model.pkl (EMBER 2018)", "alt": alt, "tohum": 42, **hata_ozeti(y, p, m)})
    yerel_tablo["ANA model.pkl (EMBER 2018)"] = yerel_yanlis_alarm(ana["model"].predict_proba(yerel[ana["ozellikler"]])[:, 1], yerel)
    print(f"  [0/{len(ADAYLAR)}] ANA model olculdu")

    # --- Adaylar, 5 tohum ---
    for i, (ad, (ornekle, kolonlar)) in enumerate(ADAYLAR.items(), 1):
        t = time.monotonic()
        for tohum in TOHUMLAR:
            ornek = ornekle(egitim, tohum)
            model = RandomForestClassifier(n_estimators=100, random_state=tohum, n_jobs=CEKIRDEK).fit(ornek[kolonlar], ornek.Etiket)
            p = model.predict_proba(test[kolonlar])[:, 1]
            for alt, m in gruplar.items():
                kayitlar.append({"aday": ad, "alt": alt, "tohum": tohum, **hata_ozeti(y, p, m)})
            if tohum == 42:
                onemler[ad] = pd.Series(model.feature_importances_, index=kolonlar)
                yerel_tablo[ad] = yerel_yanlis_alarm(model.predict_proba(yerel[kolonlar])[:, 1], yerel)
                zararli = test.Etiket.to_numpy() == 1
                aile = pd.DataFrame({"Aile": test.Aile[zararli].replace("", "(bilinmiyor)"), "kacti": p[zararli] <= 0.5})
                aile_tablo[ad] = aile.groupby("Aile").kacti.agg(["size", "mean"])
            print(f"      {ad} tohum {tohum}: {time.monotonic() - t:.0f} sn")
        print(f"  [{i}/{len(ADAYLAR)}] {ad}: {len(kolonlar)} ozellik")

    sonuc = pd.DataFrame(kayitlar)
    sonuc.to_csv(os.path.join(SONUC_KLASORU, "native_tum_kayitlar.csv"), index=False)
    metrikler = ["dogruluk %", "yanlis alarm %", "kacan zararli %", "AUC"]
    ortalama = sonuc.groupby(["aday", "alt"], sort=False)[metrikler].mean()
    aralik = sonuc[sonuc.aday != "ANA model.pkl (EMBER 2018)"].groupby(["aday", "alt"], sort=False)[metrikler].agg(lambda s: s.max() - s.min())
    print(f"\n=== EMBER2024 native test (son 12 hafta, {len(test)} dosya): 5 tohum ortalamasi ===")
    print(ortalama.round(3).to_string())
    print("\n=== Tohumlar arasi fark (max - min): bundan kucuk farklar anlamsiz ===")
    print(aralik.groupby(level="alt", sort=False).max().round(3).to_string())
    print("\n=== Bu makinedeki zararsiz PE'lerde yanlis alarm (tohum 42), Wilson %95 ===")
    print(pd.DataFrame(yerel_tablo).T.to_string())
    en_cok = aile_tablo[list(ADAYLAR)[-1]].sort_values("size", ascending=False).head(15).index
    print("\n=== En sik 15 ailede kacan zararli % (tohum 42) ===")
    print(pd.DataFrame({ad: (100 * t.loc[en_cok, "mean"]).round(1) for ad, t in aile_tablo.items()}
                       ).assign(n=aile_tablo[list(ADAYLAR)[-1]].loc[en_cok, "size"]).to_string())
    for ad in ("E2 +dizge, sinif dengeli", "E3 +dizge +DLL_mi, tip-ici (ADAY)"):
        print(f"\n=== {ad}: ilk 15 ozellik onemi (tohum 42) ===")
        print(onemler[ad].sort_values(ascending=False).head(15).round(3).to_string())
    with open(os.path.join(SONUC_KLASORU, "native_ozet.json"), "w", encoding="utf-8") as f:
        json.dump({"ortalama": ortalama.round(3).reset_index().to_dict("records"), "yerel": yerel_tablo}, f, ensure_ascii=False, indent=1)
    print(f"\n[+] toplam sure {(time.monotonic() - t0) / 60:.1f} dk -> {SONUC_KLASORU}")
