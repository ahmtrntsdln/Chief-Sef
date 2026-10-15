"""
Adim 2c - Karar tablosu: E2 / E3 ve RF / LightGBM, 300 bin, her turde %1 yanlis alarm noktasi.

karar_olcutleri.md (sonuclardan once yazildi) MEKANIK olarak uygulanir; karar kullanicinindir.
Girdi: ../2a/ogrenme_egrisi.csv (LGBM), ../2b/rf_300bin.csv (RF), yerel tahminler
(<EMBER2024>/sonuc/yerel_tahmin/*.npz, hucre basina saklı 5.635 satirin skorlari + tur esikleri).
McNemar: her tohumda iki aday ayni yerel satirlarda; b = yalniz A alarm, c = yalniz B alarm;
kesin binom testi (iki yonlu). Cikti: ../karar_tablosu.md. Kullanim: python karar_tablosu.py
"""

import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import binomtest

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BURASI, ".."))
import ortak_deney as o  # noqa: E402

BOYUT = 300_000
TURLER = ("EXE", "DLL")


def yukle_sonuclar():
    lgbm = pd.read_csv(os.path.join(BURASI, "..", "2a", "ogrenme_egrisi.csv"))
    rf = pd.read_csv(os.path.join(BURASI, "..", "2b", "rf_300bin.csv"))
    return pd.concat([lgbm, rf], ignore_index=True)


def aralik(s, d=2):
    return f"{s.mean():.{d}f} ({s.min():.{d}f}–{s.max():.{d}f})"


def yerel_alarm(algoritma, aday, tohum, yerel):
    z = np.load(os.path.join(o.YEREL_TAHMIN_KLASORU, f"{algoritma}_{aday}_{BOYUT}_{tohum}.npz"))
    p, dll = z["p"], yerel.DLL_mi.to_numpy() == 1
    return {"EXE": p[~dll] > float(z["esik_EXE"]), "DLL": p[dll] > float(z["esik_DLL"])}


def mcnemar(a, b):
    """a, b: ayni satirlarda bool alarm vektorleri. (yalniz_a, yalniz_b, p)"""
    ya, yb = int((a & ~b).sum()), int((b & ~a).sum())
    p = 1.0 if ya + yb == 0 else binomtest(ya, ya + yb, 0.5).pvalue
    return ya, yb, p


def karsilastir(df, A, B, yerel):
    """A, B: (algoritma, aday). Olcut 1-3'un mekanik sonucu."""
    da = df[(df.algoritma == A[0]) & (df.aday == A[1]) & (df.boyut == BOYUT)].sort_values("tohum")
    db = df[(df.algoritma == B[0]) & (df.aday == B[1]) & (df.boyut == BOYUT)].sort_values("tohum")
    ka, kb = da["DLL_kacan_%@1"], db["DLL_kacan_%@1"]
    fark = ka.mean() - kb.mean()
    oynama = max(ka.max() - ka.min(), kb.max() - kb.min())
    olcut1 = "ESIT" if abs(fark) <= oynama else (f"{A[0]} {A[1]}" if fark < 0 else f"{B[0]} {B[1]}")
    mc = {}
    for tur in TURLER:
        kayit = []
        for tohum in o.TOHUMLAR:
            ya, yb, p = mcnemar(yerel_alarm(*A, tohum, yerel)[tur], yerel_alarm(*B, tohum, yerel)[tur])
            kayit.append((tohum, ya, yb, p))
        a_kotu = sum(1 for _, ya, yb, p in kayit if ya > yb and p < 0.05)
        b_kotu = sum(1 for _, ya, yb, p in kayit if yb > ya and p < 0.05)
        mc[tur] = (kayit, a_kotu, b_kotu)
    return {"A": A, "B": B, "fark": fark, "oynama": oynama, "olcut1": olcut1, "mcnemar": mc}


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    df = yukle_sonuclar()
    yerel = pd.read_csv(o.DOGRULAMA_DZ80_CSV)
    adaylar = [(a, d) for a in ("RF", "LGBM") for d in ("E2", "E3")]
    eksik = [f"{a} {d}" for a, d in adaylar
             if len(df[(df.algoritma == a) & (df.aday == d) & (df.boyut == BOYUT)]) != len(o.TOHUMLAR)]
    if eksik:
        sys.exit(f"Hata: 300 bin hucresi eksik: {eksik}")

    R = []
    a = R.append
    a("# Karar tablosu (Adım 2c): E2 / E3 ve RF / LightGBM, 300 bin\n")
    a("Ölçütler ve tanımlar: [karar_olcutleri.md](karar_olcutleri.md) (sonuçlardan önce commit'lendi). "
      "Bu dosya ölçütleri MEKANİK olarak uygular; **karar kullanıcınındır.**\n")
    a(f"Test: EMBER2024 Win32+Win64 hafta 52-63 ({len(yerel)} yerel satır ayrıca). Eğitim boyutu {BOYUT:,}, "
      f"tohumlar {o.TOHUMLAR}. Hücre: 5 tohum ortalaması (en düşük–en yüksek). %1 noktası: her türde "
      "test zararsızlarının %1'i eşiği aşar (ROC çalışma noktası, üretim eşiği değil).\n")
    a("## 1. Ölçüler\n")
    a("| Model | DLL kaçan %@1 (ANA ÖLÇÜT) | EXE kaçan %@1 | AUC genel | AUC EXE | AUC DLL | "
      "Yerel YA %@1 EXE | Yerel YA %@1 DLL | Yerel YA %@0.5 EXE / DLL |")
    a("|---|---|---|---|---|---|---|---|---|")
    for alg, ad in adaylar:
        d = df[(df.algoritma == alg) & (df.aday == ad) & (df.boyut == BOYUT)]
        yer = []
        for tur in TURLER:
            k, n = d[f"{tur}_yerel_YA_k"].mean(), int(d[f"{tur}_yerel_n"].iloc[0])
            alt, ust = o.wilson(round(k), n)
            yer.append(f"{100 * k / n:.2f} [{alt:.2f}–{ust:.2f}] (ort. {k:.1f}/{n})")
        a(f"| {alg} {ad} | {aralik(d['DLL_kacan_%@1'])} | {aralik(d['EXE_kacan_%@1'])} | "
          f"{aralik(d['genel_AUC'], 4)} | {aralik(d['EXE_AUC'], 4)} | {aralik(d['DLL_AUC'], 4)} | "
          f"{yer[0]} | {yer[1]} | {d['EXE_yerel_YA_%@0.5'].mean():.2f} / {d['DLL_yerel_YA_%@0.5'].mean():.2f} |")
    a("\nGerçekleşen test yanlış alarmı (%1 hedefi, kontrol): " + "; ".join(
        f"{alg} {ad} EXE {df[(df.algoritma == alg) & (df.aday == ad) & (df.boyut == BOYUT)]['EXE_test_YA_%@1'].mean():.2f} / "
        f"DLL {df[(df.algoritma == alg) & (df.aday == ad) & (df.boyut == BOYUT)]['DLL_test_YA_%@1'].mean():.2f}"
        for alg, ad in adaylar) + "\n")

    karsilastirmalar = [(("RF", "E2"), ("RF", "E3")), (("LGBM", "E2"), ("LGBM", "E3")),
                        (("RF", "E2"), ("LGBM", "E2")), (("RF", "E3"), ("LGBM", "E3"))]
    a("## 2. Ölçütlerin mekanik uygulaması\n")
    a("| Karşılaştırma (A vs B) | Ölçüt 1: DLL kaçan farkı A−B (tohum oynaması) | Ölçüt 1 sonucu | "
      "Ölçüt 2: yerel YA McNemar, anlamlı kötüleşen tohum sayısı (A / B), EXE | aynısı, DLL | Ölçüt 3 |")
    a("|---|---|---|---|---|---|")
    ayrinti = []
    for A, B in karsilastirmalar:
        r = karsilastir(df, A, B, yerel)
        algoritma_karsilastirmasi = A[1] == B[1]
        if r["olcut1"] == "ESIT":
            o3 = "eşit → LightGBM tercih" if algoritma_karsilastirmasi else "eşit → karar kullanıcıda"
        else:
            o3 = "—"
        ihlal = []
        for tur in TURLER:
            _, ak, bk = r["mcnemar"][tur]
            if ak >= 3:
                ihlal.append(f"{A[0]} {A[1]} {tur}'de anlamlı kötü")
            if bk >= 3:
                ihlal.append(f"{B[0]} {B[1]} {tur}'de anlamlı kötü")
        o2 = lambda tur: f"{r['mcnemar'][tur][1]} / {r['mcnemar'][tur][2]}"  # noqa: E731
        a(f"| {A[0]} {A[1]} vs {B[0]} {B[1]} | {r['fark']:+.2f} ({r['oynama']:.2f}) | {r['olcut1']} | "
          f"{o2('EXE')} | {o2('DLL')} | {o3}{'; ÖLÇÜT 2 İHLALİ: ' + ', '.join(ihlal) if ihlal else ''} |")
        ayrinti.append(r)
    a("\nÖlçüt 2 eşiği: anlamlı kötüleşme = alarmı fazla olan taraf VE p < 0,05, 5 tohumun en az 3'ünde.\n")
    a("## 3. McNemar ayrıntısı (her tohum: yalnız A alarm / yalnız B alarm, p)\n")
    for r in ayrinti:
        for tur in TURLER:
            kayit = r["mcnemar"][tur][0]
            a(f"- {r['A'][0]} {r['A'][1]} vs {r['B'][0]} {r['B'][1]}, {tur}: " + "; ".join(
                f"t{t}: {ya}/{yb}, p={p:.3g}" for t, ya, yb, p in kayit))
    a("")
    a("## 4. Öğrenme eğrisi (LightGBM, bilgi için; ölçüt bu noktada uygulanmadı)\n")
    lg = df[df.algoritma == "LGBM"]
    a("| Aday | Boyut | DLL kaçan %@1 | EXE kaçan %@1 | AUC genel | Yerel YA %@1 EXE / DLL |")
    a("|---|---|---|---|---|---|")
    for (ad, b), d in lg.groupby(["aday", "boyut"]):
        a(f"| {ad} | {b:,} | {aralik(d['DLL_kacan_%@1'])} | {aralik(d['EXE_kacan_%@1'])} | "
          f"{aralik(d['genel_AUC'], 4)} | {d['EXE_yerel_YA_%@1'].mean():.2f} / {d['DLL_yerel_YA_%@1'].mean():.2f} |")
    a("\nE3 1 milyon kurulamadı (eğitimde zararlı DLL 130.550 < 250.000); E3 'tamamı' = 522.200.\n")
    a("**DUR: karar kullanıcının.**")
    metin = "\n".join(R) + "\n"
    with open(os.path.join(BURASI, "..", "karar_tablosu.md"), "w", encoding="utf-8") as f:
        f.write(metin)
    print(metin)
